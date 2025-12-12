from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, List

import httpx
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.config import Config

logger = logging.getLogger(__name__)


def _normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    return prefix if prefix.startswith("/") else f"/{prefix}"


def _build_routes(app: FastAPI, gateway_prefix: str) -> List[Dict]:
    routes: List[Dict] = []
    ignored_paths = ("/openapi", "/docs", "/redoc")

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path.startswith(ignored_paths):
            continue

        methods = [m for m in route.methods or [] if m not in {"HEAD", "OPTIONS"}]
        if not methods:
            continue

        summary = route.summary or route.name or route.operation_id or "API route"
        description = (route.description or route.dependant and route.dependant.call and route.dependant.call.__doc__) or summary  # type: ignore

        gateway_path = f"{gateway_prefix}{route.path}"
        for method in methods:
            routes.append(
                {
                    "name": f"{method.lower()} {gateway_path}",
                    "method": method,
                    "gateway_path": gateway_path,
                    "upstream_path": route.path,
                    "summary": summary,
                    "description": description,
                }
            )
    return routes


async def register_gateway(app: FastAPI) -> None:
    gateway_url = os.getenv("GATEWAY_URL") or Config.GATEWAY_URL
    service_base_url = os.getenv("SERVICE_BASE_URL") or Config.SERVICE_BASE_URL or Config.DOMAIN_NAME
    service_name = os.getenv("SERVICE_NAME") or Config.SERVICE_NAME or "rag-fastapi-chatbot"
    gateway_prefix = _normalize_prefix(os.getenv("GATEWAY_PREFIX") or Config.GATEWAY_PREFIX)
    retries = int(os.getenv("REGISTER_RETRIES") or Config.REGISTER_RETRIES)
    delay = float(os.getenv("REGISTER_DELAY") or Config.REGISTER_DELAY)

    if not gateway_url:
        logger.info("GATEWAY_URL not set; skipping gateway registration")
        return

    routes = _build_routes(app, gateway_prefix=gateway_prefix)
    if not routes:
        logger.warning("No routes discovered for gateway registration")
        return

    payload = {
        "name": service_name,
        "base_url": service_base_url.rstrip("/"),
        "routes": routes,
    }
    endpoint = gateway_url.rstrip("/") + "/gateway/register"

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(endpoint, json=payload)
                resp.raise_for_status()
            logger.info("Gateway registered (%s) base_url=%s routes=%s", service_name, service_base_url, len(routes))
            return
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Gateway registration failed attempt %s/%s: %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                await asyncio.sleep(delay)

    logger.error("Exhausted gateway registration retries")
