#!/usr/local/bin/python

import asyncio
import http
import websockets
import os
import time
from subprocess import run, STDOUT, PIPE


authn_token = os.getenv('WEBSOCKET_TOKEN')
user = os.getenv('HOST_USER')
default_timeout = 180
ssh_cmd_received_at = time.time()


class TokenParamProtocol(websockets.WebSocketServerProtocol):
    async def process_request(self, path, headers):
        try:
            user_token = path.split("token=")[1]
        except IndexError:
            return http.HTTPStatus.UNAUTHORIZED, [], b"Missing authentication token\n"

        if user_token != authn_token or not user_token:
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"


async def handle_ssh_message(self, websocket):
    async for message in websocket:
        ssh_cmd = f'ssh -i id_rsa -f -q -o BatchMode=yes -o StrictHostKeyChecking=no -o LogLevel=ERROR {user}@localhost -- {message}'
        global ssh_cmd_received_at
        ssh_cmd_received_at = time.time()
        result = run(ssh_cmd, stdout=PIPE, stderr=STDOUT, timeout=180, encoding='UTF-8', shell=True)
        await websocket.send(result.stdout)


async def main():
    with websockets.serve(handle_ssh_message, "0.0.0.0", 8765, create_protocol=TokenParamProtocol):
        socket_timeout = default_timeout
        while True:
            try:
                await asyncio.wait_for(asyncio.Future(), socket_timeout)  # run forever
            except asyncio.exceptions.TimeoutError:
                socket_timeout = default_timeout - (time.time() - ssh_cmd_received_at) + 1
                if socket_timeout <= 0:
                    break

asyncio.run(main())