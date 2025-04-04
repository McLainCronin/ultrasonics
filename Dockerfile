FROM python:3.13-alpine

COPY . /
WORKDIR /

VOLUME [ "/config", "/plugins" ]

RUN apk --no-cache add gcc g++ musl-dev
RUN pip install -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python"]

CMD ["app.py"]
