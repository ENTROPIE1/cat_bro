import asyncio
import json
import uuid
import websockets

WS_URL = "ws://127.0.0.1:8001"
PARAM_ID = "MouthOpen"  # change this if you want another parameter
PLUGIN = {"pluginName": "GPT-TTS test", "pluginDeveloper": "You"}

rid = lambda: str(uuid.uuid4())

async def main():
    async with websockets.connect(WS_URL) as ws:
        # 1. AuthenticationTokenRequest
        await ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": rid(),
            "messageType": "AuthenticationTokenRequest",
            "data": PLUGIN,
        }))
        token = json.loads(await ws.recv())["data"]["authenticationToken"]

        # 2. AuthenticationRequest
        await ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": rid(),
            "messageType": "AuthenticationRequest",
            "data": {**PLUGIN, "authenticationToken": token},
        }))
        print("Auth response:", await ws.recv())

        # 3. Open and close the mouth three times
        for _ in range(3):
            for v in (1.0, 0.0):
                await ws.send(json.dumps({
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": rid(),
                    "messageType": "InjectParameterDataRequest",
                    "data": {
                        "mode": "set",
                        "parameterValues": [
                            {"id": PARAM_ID, "value": v, "weight": 1.0},
                        ],
                    },
                }))
                print("Resp:", await ws.recv())
                await asyncio.sleep(0.4)

if __name__ == "__main__":
    asyncio.run(main())
