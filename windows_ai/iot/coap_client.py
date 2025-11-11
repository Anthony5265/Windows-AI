"""
CoAP Client Module
Constrained Application Protocol for IoT devices
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from aiocoap import Context, Message, Code
    import asyncio
    AIOCOAP_AVAILABLE = True
except ImportError:
    AIOCOAP_AVAILABLE = False
    logger.warning("aiocoap not available. Install with: pip install aiocoap")


class CoAPClient:
    """
    CoAP client for constrained IoT devices
    Implements Constrained Application Protocol (RFC 7252)
    """

    def __init__(self):
        self.is_available = AIOCOAP_AVAILABLE
        self.context = None

    async def _get_context(self):
        """Get or create CoAP context"""
        if self.context is None and self.is_available:
            self.context = await Context.create_client_context()
        return self.context

    def get(self, uri: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Send GET request

        Args:
            uri: CoAP URI (e.g., "coap://device.local/sensor/temp")
            timeout: Request timeout in seconds

        Returns:
            Dict with response data
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "aiocoap not available. Install with: pip install aiocoap"
            }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._get_async(uri, timeout)
            )
            loop.close()
            return result

        except Exception as e:
            logger.error(f"CoAP GET error: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_async(self, uri: str, timeout: int) -> Dict[str, Any]:
        """Async GET request"""
        try:
            context = await self._get_context()

            request = Message(code=Code.GET, uri=uri)
            response = await asyncio.wait_for(
                context.request(request).response,
                timeout=timeout
            )

            # Decode payload
            payload = response.payload.decode('utf-8') if response.payload else None

            return {
                "status": "success",
                "code": str(response.code),
                "payload": payload,
                "content_format": response.opt.content_format
            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except Exception as e:
            logger.error(f"CoAP GET async error: {e}")
            return {"status": "error", "message": str(e)}

    def post(self, uri: str, payload: Any,
             content_format: int = 0, timeout: int = 10) -> Dict[str, Any]:
        """
        Send POST request

        Args:
            uri: CoAP URI
            payload: Request payload
            content_format: Content format code (0=text/plain, 50=application/json)
            timeout: Request timeout in seconds

        Returns:
            Dict with response data
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "aiocoap not available"
            }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._post_async(uri, payload, content_format, timeout)
            )
            loop.close()
            return result

        except Exception as e:
            logger.error(f"CoAP POST error: {e}")
            return {"status": "error", "message": str(e)}

    async def _post_async(self, uri: str, payload: Any,
                         content_format: int, timeout: int) -> Dict[str, Any]:
        """Async POST request"""
        try:
            context = await self._get_context()

            # Encode payload
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            elif not isinstance(payload, bytes):
                import json
                payload = json.dumps(payload).encode('utf-8')

            request = Message(
                code=Code.POST,
                uri=uri,
                payload=payload
            )
            request.opt.content_format = content_format

            response = await asyncio.wait_for(
                context.request(request).response,
                timeout=timeout
            )

            # Decode response
            response_payload = response.payload.decode('utf-8') if response.payload else None

            return {
                "status": "success",
                "code": str(response.code),
                "payload": response_payload
            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except Exception as e:
            logger.error(f"CoAP POST async error: {e}")
            return {"status": "error", "message": str(e)}

    def put(self, uri: str, payload: Any,
            content_format: int = 0, timeout: int = 10) -> Dict[str, Any]:
        """
        Send PUT request

        Args:
            uri: CoAP URI
            payload: Request payload
            content_format: Content format code
            timeout: Request timeout in seconds

        Returns:
            Dict with response data
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "aiocoap not available"
            }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._put_async(uri, payload, content_format, timeout)
            )
            loop.close()
            return result

        except Exception as e:
            logger.error(f"CoAP PUT error: {e}")
            return {"status": "error", "message": str(e)}

    async def _put_async(self, uri: str, payload: Any,
                        content_format: int, timeout: int) -> Dict[str, Any]:
        """Async PUT request"""
        try:
            context = await self._get_context()

            # Encode payload
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            elif not isinstance(payload, bytes):
                import json
                payload = json.dumps(payload).encode('utf-8')

            request = Message(
                code=Code.PUT,
                uri=uri,
                payload=payload
            )
            request.opt.content_format = content_format

            response = await asyncio.wait_for(
                context.request(request).response,
                timeout=timeout
            )

            response_payload = response.payload.decode('utf-8') if response.payload else None

            return {
                "status": "success",
                "code": str(response.code),
                "payload": response_payload
            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except Exception as e:
            logger.error(f"CoAP PUT async error: {e}")
            return {"status": "error", "message": str(e)}

    def delete(self, uri: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Send DELETE request

        Args:
            uri: CoAP URI
            timeout: Request timeout in seconds

        Returns:
            Dict with response data
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "aiocoap not available"
            }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._delete_async(uri, timeout)
            )
            loop.close()
            return result

        except Exception as e:
            logger.error(f"CoAP DELETE error: {e}")
            return {"status": "error", "message": str(e)}

    async def _delete_async(self, uri: str, timeout: int) -> Dict[str, Any]:
        """Async DELETE request"""
        try:
            context = await self._get_context()

            request = Message(code=Code.DELETE, uri=uri)
            response = await asyncio.wait_for(
                context.request(request).response,
                timeout=timeout
            )

            return {
                "status": "success",
                "code": str(response.code),
                "message": "Resource deleted"
            }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except Exception as e:
            logger.error(f"CoAP DELETE async error: {e}")
            return {"status": "error", "message": str(e)}

    def observe(self, uri: str, callback, duration: int = 60) -> Dict[str, Any]:
        """
        Observe resource (CoAP observe option)

        Args:
            uri: CoAP URI
            callback: Callback function(response) for notifications
            duration: Observation duration in seconds

        Returns:
            Dict with status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "aiocoap not available"
            }

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._observe_async(uri, callback, duration)
            )
            loop.close()
            return result

        except Exception as e:
            logger.error(f"CoAP observe error: {e}")
            return {"status": "error", "message": str(e)}

    async def _observe_async(self, uri: str, callback, duration: int) -> Dict[str, Any]:
        """Async observe"""
        try:
            context = await self._get_context()

            request = Message(code=Code.GET, uri=uri, observe=0)

            observation_count = 0
            start_time = asyncio.get_event_loop().time()

            requester = context.request(request)

            async for response in requester.observation:
                # Check duration
                if asyncio.get_event_loop().time() - start_time > duration:
                    requester.observation.cancel()
                    break

                # Process response
                payload = response.payload.decode('utf-8') if response.payload else None
                callback({
                    "code": str(response.code),
                    "payload": payload
                })
                observation_count += 1

            return {
                "status": "success",
                "message": f"Observed {observation_count} updates",
                "count": observation_count
            }

        except Exception as e:
            logger.error(f"CoAP observe async error: {e}")
            return {"status": "error", "message": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "status": "success",
            "available": self.is_available,
            "context_active": self.context is not None
        }

    async def shutdown(self):
        """Shutdown client"""
        if self.context:
            await self.context.shutdown()
            self.context = None
