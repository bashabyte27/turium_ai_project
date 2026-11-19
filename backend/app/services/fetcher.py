import ipaddress
import socket
from urllib.parse import urlparse

import httpx
import trafilatura

from app.config import settings


class FetchError(Exception):
    """The page could not be downloaded or had no readable text."""


def check_not_private(url):
    """Stop people from using the server to reach localhost or internal networks."""
    host = urlparse(url).hostname
    if not host:
        raise FetchError("The URL has no hostname.")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        raise FetchError(f"Could not find the host '{host}'.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise FetchError("URLs that point to private or local addresses are not allowed.")


def fetch_page(url):
    """Download a web page and return (title, text)."""
    check_not_private(url)
    try:
        with httpx.stream(
            "GET", url, follow_redirects=True, timeout=settings.fetch_timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AIKnowledgeInbox/1.0)"},  # some sites block unknown agents
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text" not in content_type:
                raise FetchError(f"Unsupported content type: {content_type}")
            data = b""
            for part in response.iter_bytes():
                data += part
                if len(data) > settings.max_page_bytes:
                    raise FetchError("The page is too large.")
            html = data.decode(response.encoding or "utf-8", errors="replace")
    except httpx.HTTPStatusError as error:
        raise FetchError(f"The site answered with HTTP {error.response.status_code}.")
    except httpx.HTTPError as error:
        raise FetchError(f"Could not download the page: {error}")

    text = trafilatura.extract(html, include_comments=False)
    if not text or not text.strip():
        raise FetchError("No readable text was found on the page.")
    metadata = trafilatura.extract_metadata(html)
    title = metadata.title if metadata and metadata.title else url
    return title.strip(), text.strip()
