from starlette.requests import Request
import ipaddress

TRUSTED_PROXIES = [
    ipaddress.ip_network("127.0.0.1/32"),
    ipaddress.ip_network("192.168.0.0/16"),
]

def _is_trusted(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in TRUSTED_PROXIES)
    except ValueError:
        return False

def get_client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"

    if not _is_trusted(peer):
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return peer
