app_name = ultrasonics

build:
	@docker build -t $(app_name) .

run:
	docker run --detach --name $(app_name) -p 8080:8080 $(app_name)

tag-latest:
	docker tag $(app_name) xdgfx/$(app_name):latest

push-latest:
	docker push xdgfx/$(app_name):latest