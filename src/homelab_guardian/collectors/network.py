from __future__ import annotations

import socket
import time
from urllib.error import URLError
from urllib.request import urlopen


def check_internet(
    url: str,
    timeout_seconds: int,
) -> dict[str, object]:
    """Check internet reachability and response time."""

    started = time.perf_counter()

    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            return {
                "reachable": True,
                "status_code": response.status,
                "response_time_ms": round(
                    (time.perf_counter() - started) * 1000,
                    1,
                ),
                "error": None,
            }
    except (URLError, TimeoutError, OSError) as error:
        return {
            "reachable": False,
            "status_code": None,
            "response_time_ms": round(
                (time.perf_counter() - started) * 1000,
                1,
            ),
            "error": str(error),
        }


def check_dns(hostname: str) -> dict[str, object]:
    """Resolve a hostname to verify DNS functionality."""

    try:
        return {
            "resolved": True,
            "hostname": hostname,
            "ip_address": socket.gethostbyname(hostname),
            "error": None,
        }
    except socket.gaierror as error:
        return {
            "resolved": False,
            "hostname": hostname,
            "ip_address": None,
            "error": str(error),
        }