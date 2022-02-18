FROM python:3-alpine

RUN apk --no-cache add openssh openssl

RUN pip install websockets

COPY ./entrypoint  ./websocket_ssh.py ./

ENTRYPOINT ["./entrypoint"]