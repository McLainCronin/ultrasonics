#!/usr/bin/env python3

"""
up_local playlists
Local playlists plugin for ultrasonics.

Designed as both an input and output plugin.
Interacts with physical playlist files, reading the songs present in each one.
Extracts additional tag data from each song discovered.
Upon saving playlists, it will update any existing playlists before creating new ones.

XDGFX, 2020
"""

import os
import io

from ultrasonics import logs
from ultrasonics.tools.local_tags import local_tags

log = logs.create_log(__name__)

handshake = {
    "name": "local playlists",
    "description": "interface with all local .m3u playlists in a directory",
    "type": [
        "inputs",
        "outputs"
    ],
    "mode": [
        "playlists"
    ],
    "version": 0.1,
    "settings": [
        {
            "type": "string",
            "value": "Local playlists (such as .m3u files) include paths directly to the song."
        },
        {
            "type": "string",
            "value": """If the playlists were generated by a different computer/server to the one you're running
            ultrasonics 🎧 on currently, the paths saved in the playlist cannot be used by ultrasonics
            to find the song file."""
        },
        {
            "type": "string",
            "value": """Therefore, you need to provide a prepend for your playlist music files, and the
            path relative to ultrasonics."""
        },
        {
            "type": "string",
            "value": "This prepend is the longest path 📏 common to all audio files."
        },
        {
            "type": "text",
            "label": "Local Playlist Prepend",
            "name": "local_prepend",
            "value": "D:/Music"
        },
        {
            "type": "text",
            "label": "ultrasonics Prepend",
            "name": "ultrasonics_prepend",
            "value": "/mnt/music library/music"
        }
    ]
}

supported_playlist_extensions = [
    ".m3u"
]


def run(settings_dict, database, component, songs_dict=None):
    """
    if songs_dict is not supplied, this is an input plugin. it must return a songs_dict
    if songs_dict is supplied, it can be a modifier (and also returns songs_dict) or an output (and does not return anything)
    """

    def remove_prepend(path, invert=False):
        """
        Remove any playlist local music files prepend, so only the path relative to the user's music directory is left.
        Default is local prepend, invert is ultrasonics prepend.
        """

        if not invert:
            if database["local_prepend"]:
                return path.replace(database["local_prepend"], '').lstrip("/").lstrip("\\")

        else:
            if database["ultrasonics_prepend"]:
                return path.replace(database["ultrasonics_prepend"], '').lstrip("/").lstrip("\\")

        # If no database prepends exist, return the same path
        return path

    def convert_path(path, invert=False):
        """
        Converts a path string into the system format.
        """
        if enable_convert_path:
            unix = os.name != "nt"

            if invert:
                unix = not unix

            if unix:
                return path.replace("\\", "/")
            else:
                return path.replace("/", "\\")
        else:
            return path

    # Get path for playlist files
    path = settings_dict["dir"].rstrip("/").rstrip("\\")
    playlists = []

    # Check if file paths are unix or nt (windows)
    enable_convert_path = False
    ultrasonics_unix = database["ultrasonics_prepend"].startswith("/")
    local_unix = database["local_prepend"].startswith("/")

    if ultrasonics_unix != local_unix:
        log.debug(
            "ultrasonics paths and local playlist paths do not use the same separators!")
        enable_convert_path = True

    # Create a dictionary 'playlists' of all playlists in the specified directory
    # name is the playlist name
    # path is the full path to the playlist
    try:
        if "recursive" in settings_dict:
            # Recursive mode
            for root, _, files in os.walk(path):
                for item in files:
                    playlists.append({
                        "name": os.path.splitext(item)[0],
                        "path": os.path.join(root, item)
                    })

        else:
            # Non recursive mode
            files = os.listdir(path)
            for item in files:
                playlists.append({
                    "name": os.path.splitext(item)[0],
                    "path": os.path.join(path, item)
                })

    except Exception as e:
        log.error(e)

    # Remove any files which don't have a supported extension
    playlists = [item for item in playlists if os.path.splitext(item["path"])[
        1] in supported_playlist_extensions]

    if component == "inputs":
        songs_dict = []

        for playlist in playlists:

            # Initialise entry for this playlist
            songs_dict_entry = {
                "name": playlist["name"],
                "songs": []
            }

            # Read the playlist file
            songs = io.open(playlist["path"], 'r',
                            encoding='utf8').read().splitlines()

            for song in songs:

                # Skip .m3u tags beginning with "#"
                if song.startswith("#"):
                    continue

                # Convert path to be usable by ultrasonics
                song_path = remove_prepend(song)
                song_path = convert_path(song_path)
                song_path = os.path.join(
                    database["ultrasonics_prepend"], song_path)

                # Skip files which don't exist
                if not os.path.isfile(song_path):
                    continue

                try:
                    temp_song_dict = local_tags.tags(song_path)

                except NotImplementedError:
                    log.warning(
                        f"The file {song_path} is not a supported filetype")
                    continue

                except Exception as e:
                    log.error(f"Could not load tags from song: {song_path}")
                    log.error(e)

                # Add entry to the full songs dict for this playlist
                songs_dict_entry["songs"].append(temp_song_dict)

            # Add previous playlist to full songs_dict
            songs_dict.append(songs_dict_entry)

        return songs_dict

    elif component == "outputs":
        existing_playlist_titles = [item["name"] for item in playlists]

        for item in songs_dict:
            # Check if playlist already exists
            if item["name"] in existing_playlist_titles:
                # Update existing playlist
                existing_playlist_path = [
                    x["path"] for x in playlists if x["name"] == item["name"]][0]

                f = io.open(existing_playlist_path, "w", encoding="utf8")

            else:
                # Create new playlist
                new_playlist_path = os.path.join(path, item["name"] + ".m3u")

                f = io.open(new_playlist_path, "w", encoding="utf8")

            # Get songs list for this playlist
            songs = item["songs"]

            for song in songs:

                # Find location of song, and convert back to local playlists format
                song_path = song["location"]
                song_path = remove_prepend(song_path, invert=True)

                prepend_path_converted = convert_path(
                    database["local_prepend"])

                song_path = os.path.join(prepend_path_converted, song_path)
                song_path = convert_path(song_path, invert=True)

                # Write song to playlist terminated with newline character
                f.write(song_path + '\n')

            f.close()


def builder(database=None):
    """
    This function is run when the plugin is selected within a flow. It may query names of playlists or how many recent songs to include in the list.
    It returns a dictionary containing the settings the user must input in this case.

    Inputs: Persistent database settings for this plugin
    """

    settings_dict = [
        {
            "type": "string",
            "value": f"""⚠️ Only {', '.join(supported_playlist_extensions)} extensions are supported for playlists,
            and {', '.join(supported_audio_extensions)} extensions are supported for audio files.
            Unsupported files will be ignored."""
        },
        {
            "type": "text",
            "label": "Directory",
            "name": "dir",
            "value": "/mnt/music library/playlists"
        },
        {
            "type": "checkbox",
            "label": "Recursive",
            "name": "recursive",
            "value": "recursive",
            "id": "recursive"
        },
        {
            "type": "string",
            "value": "Enabling recursive mode will search all subfolders for more playlists."
        }
    ]

    return settings_dict
