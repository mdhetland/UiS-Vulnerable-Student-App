import traceback
import requests
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_user_from_session
from app.config import APP_ENV
from urllib.parse import urlparse
import ipaddress
import socket

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(hostname))
            if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved):
                return False
        except Exception:
            return False
        blocked_hosts = {"localhost", "mailhog", "db"}
        if hostname.lower() in blocked_hosts:
            return False
        return True
    except Exception:
        return False


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/status", response_class=HTMLResponse)
def status(request: Request):
    user = get_user_from_session(request)
    return templates.TemplateResponse(
        "status.html",
        {"request": request, "user": user, "env": APP_ENV, "python": "3.11", "service": "backend"},
    )


@router.get("/resources/import", response_class=HTMLResponse)
def import_resource_get(request: Request, url: str = ""):
    user = get_user_from_session(request)
    body = ""
    error = ""
    if url:
        try:
            if not is_safe_url(url):
                error = "URL not allowed"
            else:
                r = requests.get(url, timeout=5)
                body = r.text[:2000]
        except Exception as exc:
            error = str(exc)
    return templates.TemplateResponse(
        "resource_import.html",
        {"request": request, "user": user, "body": body, "url": url, "error": error},
    )


@router.post("/resources/import", response_class=HTMLResponse)
def import_resource_post(request: Request, url: str = Form(...)):
    return import_resource_get(request, url)


@router.get("/error", response_class=HTMLResponse)
def trigger_error(request: Request):
    try:
        x = 1 / 0
        return {"x": x}
    except Exception:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "details": traceback.format_exc()},
            status_code=500,
        )
