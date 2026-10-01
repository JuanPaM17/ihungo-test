import time
import logging
from enum import Enum
from typing import Optional, Dict, Any
import httpx
import langsmith as ls
from charset_normalizer import detect
import json as jsonClass
from decimal import Decimal
import aiohttp

logger = logging.getLogger(__name__)

def sanitize_json_data(d):
    for key, value in d.items():
        if isinstance(value, dict):
            sanitize_json_data(value)
        elif isinstance(value, Decimal):
            d[key] = float(value)
        elif value is None:
            d[key] = ""
    return d

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class ApiRequestManager:

    _header_content_type: str = (
        "application/json"  # Se deja constante, no veo el caso de uso de otro tipo
    )
    _header_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # Se deja constante
    )
    _api_endpoint: str = None
    default_tenant_id: str = None

    def __init__(self, api_endpoint: str, time_out: float = 30):
        self._api_endpoint = api_endpoint
        self._time_out = time_out
        
    async def make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        body_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """
        Make an asynchronous HTTP request using httpx.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: API endpoint
        :param headers: Optional HTTP headers
        :param params: Optional query parameters
        :param data: Optional form data
        :param json: Optional JSON body
        :param kwargs: Additional arguments to pass to httpx.request()
        :return: Response JSON or raise an HTTP error
        """
        assert self._api_endpoint is not None, "API_ENDPOINT is not set"
        assert endpoint is not None, "endpoint is not set"

        start_time = time.time()
        url = self._api_endpoint.rstrip("/") + "/" + endpoint.lstrip("/")
        logger.info("-- MAKE REQUEST --")
        logger.info("method=%s endpoint=%s", method.value, endpoint)
        logger.info("URL API: %s", url)
        _safe_headers = {k: ("[REDACTED]" if k.lower() == "authorization" else v) for k, v in (headers or {}).items()}
        logger.info("HEADERS: %s", _safe_headers)

        if query_params is None:
            query_params = {}
        try:
            format_params = sanitize_json_data(query_params.dict())
        except:
            format_params = sanitize_json_data(query_params)
        logger.info("PARAMS: %s", format_params)

        if body_params is None:
            body_params = {}
        try:
            body = sanitize_json_data(body_params.dict())
        except:
            body = sanitize_json_data(body_params)
        safe_body = {k: v for k, v in body.items() if k.lower() != "password"}
        logger.info("BODY (safe): %s", safe_body)
        response_data = None
        response = None
        timeout = aiohttp.ClientTimeout(total=self._time_out)
        # Only send a JSON body for non-GET requests and when body is non-empty
        json_body = body if (method != HTTPMethod.GET and body) else None

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=method.value,
                    url=url,
                    headers=headers,
                    params=format_params,
                    data=data,
                    json=json_body,
                ) as response:
                    # Read body first so it's available for error logging
                    try:
                        response_data = await response.json()
                    except Exception:
                        text = await response.text()
                        try:
                            response_data = jsonClass.loads(text)
                        except Exception:
                            response_data = text
                    if not response.ok:
                        logger.error("make_request: HTTP %s — error body: %s", response.status, response_data)
                        response_data = {"error": response_data, "status_code": response.status}
                        return response_data
        except aiohttp.ClientError as e:
            logger.error("make_request: Request failed: %s", e)
            response_data = {"error": str(e)}
        except Exception as e:
            logger.error("Unexpected error occurred: %s", e)
            response_data = {"error": "Unexpected error occurred", "details": str(e)}

        end_time = time.time()
        logger.warning(
            "REQUEST TIME: %.3f sec", end_time - start_time
        )
        run_tree = ls.get_current_run_tree()
        if run_tree:
            run_tree.metadata[f"request_time_{endpoint}"] = (
                f"url={url} - type={method} - time={end_time - start_time:.3f} sec"
            )
        logger.info("REQUEST RESPONSE:%s", response_data)
        return response_data

    def build_basic_info(
        self, token: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Builds the basic headers and merges optional parameters with basic parameters
        for HTTP requests.

        Args:
            token (str): User authorization token.
            params (Optional[Dict[str, Any]]): Additional parameters to be included in 'params',
            only used in GET requests.

        Returns:
            dict: Dictionary with 'headers' and 'params' for the request.
        """
        # Basic headers
        basic_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": self._header_content_type,
            "User-Agent": self._header_user_agent,
        }

        # Elimina el token de los parámetros, si se pasa
        if params and "token" in params:
            del params["token"]

        return {"headers": basic_headers, "params": params}

def api_request_manager_factory() -> ApiRequestManager:
    """
    Returns an instance of ApiRequestManager with the specified API endpoint.
    """
    import os
    mgr = ApiRequestManager(
        os.getenv("API_ENDPOINT"),
        float(os.getenv("API_REQUEST_TIME_OUT", "30"))
    )
    return mgr
