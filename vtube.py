import asyncio
import json
import logging
from typing import Optional

import websockets
import uuid


class VTubeClient:
    """WebSocket client for controlling VTube Studio parameters."""

    def __init__(
        self,
        url: str = "ws://127.0.0.1:8001",
        param: str = "MouthOpen",
        smoothing: float = 0.3,
        *,
        plugin_name: str = "GPT-TTS",
        plugin_developer: str = "You",
    ) -> None:
        """Initialize client.

        Args:
            url: WebSocket URL of VTube Studio.
            param: Parameter name to update.
            smoothing: Exponential smoothing factor for level values.
        """
        self.url = url
        self.param = param
        self.smoothing = smoothing
        self.plugin_name = plugin_name
        self.plugin_developer = plugin_developer
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._level: float = 0.0
        self._last_log: float = 0.0

    async def check_connection(self) -> bool:
        """Ping the server to ensure the connection is alive."""
        if self._ws is None:
            return False
        try:
            pong = await self._ws.ping()
            await asyncio.wait_for(pong, timeout=1)
            logging.debug("VTube WS ping OK")
            return True
        except Exception:
            logging.warning("VTube WS ping failed")
            self._ws = None
            return False

    async def connect(self) -> None:
        """Establish WebSocket connection and authenticate."""
        self._ws = await websockets.connect(self.url)
        logging.debug("VTube WS connected to %s", self.url)

        def _req_id() -> str:
            return str(uuid.uuid4())

        # 1. request authentication token
        token_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": _req_id(),
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": self.plugin_name,
                "pluginDeveloper": self.plugin_developer,
            },
        }
        await self._ws.send(json.dumps(token_request))
        logging.debug("WS send: %s", token_request)
        try:
            token_resp = json.loads(await asyncio.wait_for(self._ws.recv(), timeout=2))
        except Exception:
            logging.warning("VTube WS token request timed out")
            return
        logging.debug("WS recv: %s", token_resp)
        token = token_resp.get("data", {}).get("authenticationToken")
        if not token:
            logging.warning("VTube WS token missing in response")
            return

        # 2. confirm the token
        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": _req_id(),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": self.plugin_name,
                "pluginDeveloper": self.plugin_developer,
                "authenticationToken": token,
            },
        }
        await self._ws.send(json.dumps(auth_request))
        logging.debug("WS send: %s", auth_request)
        try:
            auth_resp = json.loads(await asyncio.wait_for(self._ws.recv(), timeout=2))
        except Exception:
            logging.warning("VTube WS authentication timed out")
            return
        logging.debug("WS recv: %s", auth_resp)
        if not auth_resp.get("data", {}).get("authenticated"):
            logging.warning("VTube WS authentication failed")
            await self._ws.close()
            self._ws = None
            return

        logging.info("VTube handshake: %s", auth_resp)
        for v in (1.0, 0.0):
            test_payload = {
                "apiName": "VTubeStudioParameterUpdate",
                "parameters": [{"name": self.param, "value": v}],
            }
            await self._ws.send(json.dumps(test_payload))
            await asyncio.sleep(0.5)

    async def send_level(self, level: float) -> None:
        """Send normalized level to VTube Studio.

        Args:
            level: Value in range 0..1.
        """
        if self._ws is None:
            return
        self._level = self._level + self.smoothing * (level - self._level)
        self._level = min(max(self._level, 0.0), 1.0)
        try:
            payload = {
                "apiName": "VTubeStudioParameterUpdate",
                "parameters": [{"name": self.param, "value": self._level}],
            }
            await self._ws.send(json.dumps(payload))
            logging.debug("WS send: %s", payload)
        except (websockets.ConnectionClosed, ConnectionRefusedError):
            logging.warning("VTube WS connection lost")
            self._ws = None
        now = asyncio.get_event_loop().time()
        if logging.getLogger().level == logging.DEBUG and now - self._last_log >= 0.1:
            status = "connected" if self._ws else "disconnected"
            logging.debug("RMS %.3f \u2192 %.3f, WS %s", level, self._level, status)
            self._last_log = now

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
            logging.debug("VTube WS closed")
