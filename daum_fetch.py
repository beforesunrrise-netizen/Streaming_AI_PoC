"""
Daum Finance exclusive fetcher with allowlist enforcement
"""

import requests
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from dataclasses import dataclass

from config import (
    ALLOWED_DOMAINS,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    RETRY_DELAY,
    MAX_RETRIES,
    CACHE_TTL_DEFAULT
)
from cache_manager import get_cache


@dataclass
class FetchResult:
    """
    Result of a fetch operation
    """
    success: bool
    status_code: Optional[int] = None
    content: Optional[str] = None
    json_data: Optional[dict] = None
    error_message: Optional[str] = None
    url: Optional[str] = None


def _is_allowed_domain(url: str) -> bool:
    """
    Check if URL domain is in allowlist
    Args:
        url: URL to check
    Returns:
        True if allowed, False otherwise
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove 'www.' prefix if exists
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain in ALLOWED_DOMAINS
    except Exception:
        return False


def fetch(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    use_cache: bool = True,
    cache_ttl: int = CACHE_TTL_DEFAULT,
    params: Optional[dict] = None,
    is_json: bool = False
) -> FetchResult:
    """
    Fetch content from Daum Finance with allowlist enforcement

    Args:
        url: URL to fetch
        headers: Additional headers (optional)
        use_cache: Whether to use cache (default: True)
        cache_ttl: Cache TTL in seconds (default: CACHE_TTL_DEFAULT)
        params: URL parameters (optional)
        is_json: Whether to parse response as JSON (default: False)

    Returns:
        FetchResult object
    """

    # CRITICAL: Allowlist check - block immediately if not allowed
    if not _is_allowed_domain(url):
        return FetchResult(
            success=False,
            error_message=f"도메인 허용 목록에 없음: {url}",
            url=url
        )

    # Check cache first
    cache = get_cache()
    if use_cache:
        cached = cache.get(url, params)
        if cached is not None:
            if is_json:
                return FetchResult(
                    success=True,
                    status_code=200,
                    json_data=cached,
                    url=url
                )
            else:
                return FetchResult(
                    success=True,
                    status_code=200,
                    content=cached,
                    url=url
                )

    # Prepare headers
    request_headers = DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    # Add Referer for Daum Finance
    if 'Referer' not in request_headers:
        request_headers['Referer'] = 'https://finance.daum.net/'

    # Retry logic
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=request_headers,
                params=params,
                timeout=DEFAULT_TIMEOUT
            )

            # Success
            if response.status_code == 200:
                if is_json:
                    try:
                        json_data = response.json()
                        # Cache the result
                        if use_cache:
                            cache.set(url, json_data, cache_ttl, params)

                        return FetchResult(
                            success=True,
                            status_code=200,
                            json_data=json_data,
                            url=url
                        )
                    except Exception as e:
                        return FetchResult(
                            success=False,
                            status_code=200,
                            error_message=f"JSON 파싱 실패: {str(e)}",
                            url=url
                        )
                else:
                    content = response.text
                    # Cache the result
                    if use_cache:
                        cache.set(url, content, cache_ttl, params)

                    return FetchResult(
                        success=True,
                        status_code=200,
                        content=content,
                        url=url
                    )

            # Handle 403/429 with retry
            elif response.status_code in [403, 429]:
                last_error = f"HTTP {response.status_code}"
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return FetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"접근 거부 (HTTP {response.status_code})",
                        url=url
                    )

            # Other HTTP errors
            else:
                return FetchResult(
                    success=False,
                    status_code=response.status_code,
                    error_message=f"HTTP 오류: {response.status_code}",
                    url=url
                )

        except requests.Timeout:
            last_error = "Timeout"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            else:
                return FetchResult(
                    success=False,
                    error_message=f"요청 시간 초과 ({DEFAULT_TIMEOUT}초)",
                    url=url
                )

        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            else:
                return FetchResult(
                    success=False,
                    error_message=f"요청 실패: {str(e)}",
                    url=url
                )

    # Should not reach here, but just in case
    return FetchResult(
        success=False,
        error_message=f"알 수 없는 오류: {last_error}",
        url=url
    )
