#!/usr/local/bin/python

import asyncio
import http
import websockets
import os
import ssl
import time
from subprocess import run, STDOUT, PIPE, TimeoutExpired


authn_token = os.getenv('WEBSOCKET_TOKEN')
user = os.getenv('HOST_USER')
default_timeout = 180
ssh_cmd_received_at = time.time()
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("cert.pem", "cert.pem")


class TokenParamProtocol(websockets.WebSocketServerProtocol):
    async def process_request(self, path, headers):
        try:
            user_token = path.split("token=")[1]
        except IndexError:
            return http.HTTPStatus.UNAUTHORIZED, [], b"Missing authentication token\n"

        if user_token != authn_token or not user_token:
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"


async def handle_ssh_message(websocket):
    async for message in websocket:
        ssh_cmd = f'ssh -i id_rsa -o BatchMode=yes -o StrictHostKeyChecking=no -o LogLevel=ERROR {user}@localhost -- {message}'
        global ssh_cmd_received_at
        ssh_cmd_received_at = time.time()
        try:
            result = run(ssh_cmd, stdout=PIPE, stderr=STDOUT, timeout=10, encoding='UTF-8', shell=True).stdout
        except TimeoutExpired:
            result = f'Command timed out after 10 seconds (tried to run "{message}")'
        except Exception as e:
            result = f'Unable to execute command "{message}": {str(e)}'
        await websocket.send(result)


async def main():
    async with websockets.serve(handle_ssh_message, "0.0.0.0", 8765,
                                create_protocol=TokenParamProtocol, ssl=ssl_context):
        socket_timeout = default_timeout
        while True:
            try:
                await asyncio.wait_for(asyncio.Future(), socket_timeout)  # run forever
            except asyncio.exceptions.TimeoutError:
                socket_timeout = default_timeout - (time.time() - ssh_cmd_received_at) + 1
                if socket_timeout <= 0:
                    break

asyncio.run(main())
