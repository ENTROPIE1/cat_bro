import asyncio
import json
import logging
from typing import Optional

import websockets


class VTubeClient:
    """WebSocket client for controlling VTube Studio parameters."""

    def __init__(self, url: str = "ws://127.0.0.1:8001", param: str = "MouthOpen", smoothing: float = 0.3) -> None:
        """Initialize client.

        Args:
            url: WebSocket URL of VTube Studio.
            param: Parameter name to update.
            smoothing: Exponential smoothing factor for level values.
        """
        self.url = url
        self.param = param
        self.smoothing = smoothing
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._level: float = 0.0
        self._last_log: float = 0.0

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        self._ws = await websockets.connect(self.url)
        logging.debug("VTube WS connected to %s", self.url)

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
