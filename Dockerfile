FROM python:3-alpine

RUN apk --no-cache add openssh

RUN pip install websockets

COPY ./entrypoint  ./websocket_ssh.py ./

ENTRYPOINT ["./entrypoint"]