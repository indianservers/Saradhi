"""Resolve a client address without trusting spoofable forwarding headers."""

import ipaddress

from fastapi import Request


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        peer_ip = ipaddress.ip_address(peer)
    except ValueError:
        return "unknown"

    settings = getattr(request.app.state, "settings", None)
    trusted = []
    for cidr in getattr(settings, "trusted_proxy_cidrs", ()):
        try:
            trusted.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            # Invalid runtime configuration is never allowed to expand trust.
            continue
    if not any(peer_ip in network for network in trusted):
        return str(peer_ip)

    forwarded = request.headers.get("x-forwarded-for", "")
    chain = []
    for value in forwarded.split(","):
        try:
            chain.append(ipaddress.ip_address(value.strip()))
        except ValueError:
            return str(peer_ip)

    # Walk from the trusted peer toward the origin. The first untrusted hop is
    # the client; leftmost data outside the chain of trusted proxies is ignored.
    for candidate in reversed(chain):
        if not any(candidate in network for network in trusted):
            return str(candidate)
    return str(chain[0]) if chain else str(peer_ip)
