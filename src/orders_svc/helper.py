from asgi_correlation_id import correlation_id
from httpx import Request

# Event hook for log tracing
async def add_correlation_id_header(req: Request):
    cid = correlation_id.get()
    if cid:
        req.headers["X-Correlation-ID"] = cid
