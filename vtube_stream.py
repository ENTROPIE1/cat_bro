import asyncio
import json
import uuid
import websockets
import numpy as np
import logging
import subprocess
import os

rid = lambda: str(uuid.uuid4())

class VTubeStreamer:
    def __init__(self, url="ws://127.0.0.1:8001", param="MouthOpen",
                 smoothing=0.25, gain=1.6):
        self.url = url
        self.param = param
        self.smooth = smoothing
        self.gain = gain
        self.ws = None
        self.value = 0.0

    async def connect(self, plugin="GPT-TTS", dev="CLI"):
        self.ws = await websockets.connect(self.url, open_timeout=10)
        await self.ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": rid(),
            "messageType": "AuthenticationTokenRequest",
            "data": {"pluginName": plugin, "pluginDeveloper": dev},
        }))
        token = json.loads(await self.ws.recv())["data"]["authenticationToken"]
        await self.ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": rid(),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": plugin,
                "pluginDeveloper": dev,
                "authenticationToken": token,
            },
        }))
        await self.ws.recv()
        logging.info("VTS authenticated")

    async def send_rms(self, mp3_bytes: bytes):
        ffmpeg = os.path.join("ffmpeg", "bin", "ffmpeg.exe")
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", "48000", "pipe:1",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        pcm, _ = await proc.communicate(mp3_bytes)
        if not pcm:
            return
        sig = np.frombuffer(pcm, np.int16).astype(np.float32)
        rms = np.sqrt(np.mean(sig**2)) / 32768 * self.gain
        rms = min(1.0, rms)
        self.value += self.smooth * (rms - self.value)
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": rid(),
            "messageType": "InjectParameterDataRequest",
            "data": {
                "mode": "set",
                "parameterValues": [
                    {"id": self.param, "value": self.value, "weight": 1.0}
                ],
            },
        }
        await self.ws.send(json.dumps(payload))
        resp = await self.ws.recv()
        logging.debug("raw_rms %.3f -> %.3f", rms, self.value)
        logging.debug("VTS reply: %s", resp)
        if "ParameterNotFound" in resp:
            create = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": rid(),
                "messageType": "ParameterCreationRequest",
                "data": {
                    "name": self.param,
                    "description": "GPT-TTS lip sync",
                    "min": 0,
                    "max": 1,
                    "defaultValue": 0,
                },
            }
            await self.ws.send(json.dumps(create))
            logging.info("привяжите MouthOpen к ParamMouthOpenY")

    async def close(self):
        if self.ws:
            await self.ws.close()
