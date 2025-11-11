"""
HTTP REST API Client for IoT Devices
Standard HTTP/HTTPS communication with IoT devices
"""
from typing import Dict, Any, Optional
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP/REST API client for IoT device communication
    """

    def __init__(self, base_url: str = None, **kwargs):
        """
        Initialize HTTP client

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            verify_ssl: Verify SSL certificates
            auth: Authentication tuple (username, password)
            api_key: API key for authentication
            headers: Default headers
        """
        self.base_url = base_url
        self.timeout = kwargs.get('timeout', 30)
        self.verify_ssl = kwargs.get('verify_ssl', True)
        self.auth = kwargs.get('auth')
        self.api_key = kwargs.get('api_key')

        # Create session with retry strategy
        self.session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        default_headers = {
            'User-Agent': 'Windows-AI-IoT-Client/1.0',
            'Accept': 'application/json'
        }

        # Add API key if provided
        if self.api_key:
            default_headers['Authorization'] = f'Bearer {self.api_key}'

        # Merge with custom headers
        custom_headers = kwargs.get('headers', {})
        self.session.headers.update({**default_headers, **custom_headers})

        # Set authentication
        if self.auth:
            self.session.auth = self.auth

    def get(self, endpoint: str, params: Dict[str, Any] = None,
            **kwargs) -> Dict[str, Any]:
        """
        Send GET request

        Args:
            endpoint: API endpoint
            params: Query parameters
            timeout: Request timeout
            headers: Additional headers

        Returns:
            Dict with response data
        """
        try:
            url = self._build_url(endpoint)
            timeout = kwargs.get('timeout', self.timeout)
            headers = kwargs.get('headers', {})

            response = self.session.get(
                url,
                params=params,
                timeout=timeout,
                headers=headers,
                verify=self.verify_ssl
            )

            return self._process_response(response)

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP GET error: {e}")
            return {"status": "error", "message": str(e)}

    def post(self, endpoint: str, data: Any = None,
             json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Send POST request

        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            timeout: Request timeout
            headers: Additional headers

        Returns:
            Dict with response data
        """
        try:
            url = self._build_url(endpoint)
            timeout = kwargs.get('timeout', self.timeout)
            headers = kwargs.get('headers', {})

            response = self.session.post(
                url,
                data=data,
                json=json_data,
                timeout=timeout,
                headers=headers,
                verify=self.verify_ssl
            )

            return self._process_response(response)

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP POST error: {e}")
            return {"status": "error", "message": str(e)}

    def put(self, endpoint: str, data: Any = None,
            json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Send PUT request

        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            timeout: Request timeout
            headers: Additional headers

        Returns:
            Dict with response data
        """
        try:
            url = self._build_url(endpoint)
            timeout = kwargs.get('timeout', self.timeout)
            headers = kwargs.get('headers', {})

            response = self.session.put(
                url,
                data=data,
                json=json_data,
                timeout=timeout,
                headers=headers,
                verify=self.verify_ssl
            )

            return self._process_response(response)

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP PUT error: {e}")
            return {"status": "error", "message": str(e)}

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Send DELETE request

        Args:
            endpoint: API endpoint
            timeout: Request timeout
            headers: Additional headers

        Returns:
            Dict with response data
        """
        try:
            url = self._build_url(endpoint)
            timeout = kwargs.get('timeout', self.timeout)
            headers = kwargs.get('headers', {})

            response = self.session.delete(
                url,
                timeout=timeout,
                headers=headers,
                verify=self.verify_ssl
            )

            return self._process_response(response)

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP DELETE error: {e}")
            return {"status": "error", "message": str(e)}

    def patch(self, endpoint: str, data: Any = None,
              json_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Send PATCH request

        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            timeout: Request timeout
            headers: Additional headers

        Returns:
            Dict with response data
        """
        try:
            url = self._build_url(endpoint)
            timeout = kwargs.get('timeout', self.timeout)
            headers = kwargs.get('headers', {})

            response = self.session.patch(
                url,
                data=data,
                json=json_data,
                timeout=timeout,
                headers=headers,
                verify=self.verify_ssl
            )

            return self._process_response(response)

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP PATCH error: {e}")
            return {"status": "error", "message": str(e)}

    def _build_url(self, endpoint: str) -> str:
        """Build complete URL"""
        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            return endpoint

        if self.base_url:
            # Remove trailing slash from base_url and leading slash from endpoint
            base = self.base_url.rstrip('/')
            endpoint = endpoint.lstrip('/')
            return f"{base}/{endpoint}"

        return endpoint

    def _process_response(self, response: requests.Response) -> Dict[str, Any]:
        """Process HTTP response"""
        try:
            # Check status code
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.reason}",
                    "status_code": response.status_code,
                    "body": response.text
                }

            # Try to parse JSON
            try:
                data = response.json()
            except ValueError:
                data = response.text

            return {
                "status": "success",
                "status_code": response.status_code,
                "data": data,
                "headers": dict(response.headers)
            }

        except Exception as e:
            logger.error(f"Response processing error: {e}")
            return {"status": "error", "message": str(e)}

    def close(self):
        """Close session"""
        self.session.close()


class IoTDeviceHTTPClient:
    """
    High-level HTTP client for IoT device control
    """

    def __init__(self, device_url: str, **kwargs):
        """
        Initialize device client

        Args:
            device_url: Base URL of the device
            api_key: Device API key
            username: Basic auth username
            password: Basic auth password
        """
        auth = None
        if kwargs.get('username') and kwargs.get('password'):
            auth = (kwargs['username'], kwargs['password'])

        self.client = HTTPClient(
            base_url=device_url,
            api_key=kwargs.get('api_key'),
            auth=auth,
            verify_ssl=kwargs.get('verify_ssl', True)
        )

    def get_status(self) -> Dict[str, Any]:
        """Get device status"""
        return self.client.get('/status')

    def get_state(self) -> Dict[str, Any]:
        """Get device state"""
        return self.client.get('/state')

    def set_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set device state

        Args:
            state: New state parameters

        Returns:
            Dict with response
        """
        return self.client.post('/state', json_data=state)

    def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send command to device

        Args:
            command: Command name
            params: Command parameters

        Returns:
            Dict with response
        """
        return self.client.post('/command', json_data={
            'command': command,
            'params': params or {}
        })

    def get_sensor_data(self, sensor_id: str = None) -> Dict[str, Any]:
        """
        Get sensor data

        Args:
            sensor_id: Specific sensor ID (optional)

        Returns:
            Dict with sensor data
        """
        if sensor_id:
            return self.client.get(f'/sensors/{sensor_id}')
        else:
            return self.client.get('/sensors')

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        return self.client.get('/info')

    def reboot(self) -> Dict[str, Any]:
        """Reboot device"""
        return self.client.post('/reboot')

    def close(self):
        """Close client"""
        self.client.close()
