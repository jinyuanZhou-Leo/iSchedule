#!/usr/bin/env python3
# coding=utf-8

import requests
from loguru import logger

class RequestHandler:
    def __init__(self, timeout: int = 10, retry: int = 3, headers: dict = {}) -> None:
        self.timeout = timeout
        self.retry = retry
        self.headers = headers
        self.session = requests.Session()

    def _handle_error(self, error):
        if isinstance(error, requests.exceptions.HTTPError):
            logger.critical(f"HTTP Error - {error}")
        elif isinstance(error, requests.exceptions.ConnectionError):
            logger.critical(f"Connection Error - {error}")
        elif isinstance(error, requests.exceptions.Timeout):
            logger.critical(f"Timeout Error - {error}")
        elif isinstance(error, requests.exceptions.RequestException):
            logger.critical(f"Request Exception - {error}")
        elif isinstance(error, requests.exceptions.InvalidSchema):
            logger.critical(f"Invalid Schema Error - {error}")
        else:
            logger.critical(f"Unknown Error - {error}")

        exit(1)

    def _sendRequest(self, method: str, url: str, **kwargs) -> requests.Response | None:
        for attempts in range(self.retry):
            try:
                logger.debug(f"{method.upper()} - {url} with **kwargs: {kwargs}")
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    headers=self.headers,
                    **kwargs,
                )
                # response = method(url, timeout=self.timeout, headers=self.headers, **kwargs)
                response.raise_for_status()
                logger.success(f"Successfully {method.upper()}: {url}")
                return response
            except Exception as e:
                logger.warning(
                    f"{method.upper()} failed (Attempt:[{attempts+1}/{self.retry}]): {e}"
                )
                if attempts + 1 == self.retry:
                    self._handle_error(e)

        return None

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._sendRequest("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._sendRequest("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self._sendRequest("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self._sendRequest("DELETE", url, **kwargs)


if __name__ == "__main__":
    logger.warning("This module cannot run independently")
