# -*- codeing = utf-8 -*-
# @Create: 2023-03-29 3:23 p.m.
# @Update: 2025-10-24 11:53 p.m.
# @Author: John Zhao
"""HTTP probing helper functions."""

import logging
from typing import Any, Callable, Dict, Optional

import requests

import configuration

LOGGER = logging.getLogger(__name__)


def resolve_timeout(explicit_timeout: Optional[float] = None) -> float:
    """Resolve the request timeout from configuration or explicit overrides."""

    if explicit_timeout is not None:
        return explicit_timeout
    return configuration.get_request_timeout()


def _perform_http_request(
    method_name: str,
    request_callable: Callable[..., Any],
    url: str,
    *,
    timeout: float,
    payload: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
) -> bool:
    request_kwargs: Dict[str, Any] = {"timeout": timeout}
    if payload is not None:
        request_kwargs["data"] = payload
    if headers is not None:
        request_kwargs["headers"] = headers

    try:
        response = request_callable(url, **request_kwargs)
    except requests.RequestException as exc:
        LOGGER.error("monitor.http.error method=%s url=%s error=%s",
                     method_name, url, exc)
        return False

    if 200 <= response.status_code < 400:
        LOGGER.info(
            "monitor.http.success method=%s url=%s status=%s",
            method_name,
            url,
            response.status_code,
        )
        return True

    LOGGER.warning(
        "monitor.http.failure method=%s url=%s status=%s",
        method_name,
        url,
        response.status_code,
    )
    return False


def monitor_get(url: str, timeout: Optional[float] = None) -> bool:
    try:
        resolved_timeout = resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error("monitor.http.timeout_error method=GET url=%s error=%s",
                     url, exc)
        return False

    return _perform_http_request(
        "GET",
        requests.get,
        url,
        timeout=resolved_timeout,
    )


def monitor_post(
    url: str,
    payload: Optional[Any] = None,
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> bool:
    try:
        resolved_timeout = resolve_timeout(timeout)
    except ValueError as exc:
        LOGGER.error("monitor.http.timeout_error method=POST url=%s error=%s",
                     url, exc)
        return False

    return _perform_http_request(
        "POST",
        requests.post,
        url,
        timeout=resolved_timeout,
        payload=payload,
        headers=headers,
    )


def probe_http_service(url: str, timeout: float) -> bool:
    """Perform a GET probe against the service endpoint."""

    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        LOGGER.error("monitor.http_probe.error url=%s error=%s", url, exc)
        return False

    status_code = response.status_code
    if 200 <= status_code < 400:
        LOGGER.info("monitor.http_probe.success url=%s status=%s", url,
                    status_code)
        return True

    LOGGER.warning("monitor.http_probe.failure url=%s status=%s", url,
                   status_code)
    return False
