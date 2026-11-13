"""Outbound URL validation (SSRF mitigation)."""

import ipaddress
import socket
from urllib.parse import urlparse

_BLOCKED_HOSTS = frozenset({"localhost", "metadata.google.internal"})


def validate_outbound_url(url: str) -> None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Only http and https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    host = parsed.hostname.lower()
    if host in _BLOCKED_HOSTS or host.endswith(".local"):
        raise ValueError("Destination host is not allowed")
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError("Private or loopback destinations are not allowed")
    except ValueError:
        # hostname — resolve and block private IPs
        try:
            resolved = socket.getaddrinfo(host, None)
        except socket.gaierror as exc:
            raise ValueError("Hostname could not be resolved") from exc
        for entry in resolved:
            ip = entry[4][0]
            parsed_ip = ipaddress.ip_address(ip)
            if (
                parsed_ip.is_private
                or parsed_ip.is_loopback
                or parsed_ip.is_link_local
                or parsed_ip.is_reserved
            ):
                raise ValueError("Resolved address is not allowed for outbound connections")
