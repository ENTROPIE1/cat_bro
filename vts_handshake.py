import asyncio
import json
import uuid

import websockets


def _req_id() -> str:
    return str(uuid.uuid4())


async def vts_handshake(url: str = "ws://127.0.0.1:8001") -> None:
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": _req_id(),
            "messageType": "AuthenticationTokenRequest",
            "data": {"pluginName": "GPT-TTS", "pluginDeveloper": "You"},
        }))
        token_resp = json.loads(await ws.recv())
        token = token_resp["data"]["authenticationToken"]

        await ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": _req_id(),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": "GPT-TTS",
                "pluginDeveloper": "You",
                "authenticationToken": token,
            },
        }))
        auth_resp = await ws.recv()
        print(auth_resp)

if __name__ == "__main__":
    asyncio.run(vts_handshake())
