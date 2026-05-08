# utils/ws_server.py
import asyncio
import json
import threading
from typing import Optional

import websockets

from core.services.logging_service import get_logger

logger = get_logger("zeno.ws")

try:
    # Helps both runtime and static analysis
    from websockets.server import serve as ws_serve  # type: ignore
except ImportError:  # pragma: no cover
    from websockets import serve as ws_serve  # type: ignore


class ZenoWSServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._started = False
        self._lock = threading.Lock()

    async def register(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            try:
                self.clients.remove(websocket)
            except KeyError:
                pass

    async def _send_to_all(self, message):
        if not self.clients:
            return
        msg_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(msg_json) for client in list(self.clients)],
            return_exceptions=True,
        )

    def broadcast(self, message):
        """Send message to all connected clients (Thread-safe)."""
        if not self._loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._send_to_all(message), self._loop)
        except Exception:
            logger.exception("WS broadcast failed")

    def _start_server(self):
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)

        try:
            async def main():
                async with ws_serve(self.register, self.host, self.port):
                    logger.info("WebSocket Server running on ws://%s:%s", self.host, self.port)
                    await asyncio.Future()  # runs forever

            loop.run_until_complete(main())
        except Exception:
            logger.exception("WS server crashed")
        finally:
            try:
                loop.stop()
            except Exception:
                pass

    def start(self):
        # Backwards-compatible method
        self.start_once()

    def start_once(self):
        """Start the WS server exactly once."""
        with self._lock:
            if self._started and self._thread and self._thread.is_alive():
                return
            self._started = True
            self._thread = threading.Thread(target=self._start_server, daemon=True, name="ZenoWSServer")
            logger.info("Starting WS server thread on ws://%s:%s", self.host, self.port)
            self._thread.start()

    def stop(self):
        """Best-effort stop. (Clients should disconnect on loop stop)."""
        with self._lock:
            loop = self._loop
            self._loop = None

        logger.info("Stopping WS server (best-effort)")
        if loop:
            try:
                loop.call_soon_threadsafe(loop.stop)
            except Exception:
                logger.exception("WS stop failed")

# Global instance
ws_server = ZenoWSServer()
