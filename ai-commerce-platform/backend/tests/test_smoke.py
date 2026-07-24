"""Smoke tests that need no database — import wiring + stub AI behavior."""
from __future__ import annotations


def test_app_imports_and_routes_registered():
    from app.main import app

    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/v1/products" in paths
    assert "/api/v1/ai/chat" in paths


def test_stub_provider_grounds_in_context():
    from app.ai.stub import StubProvider

    provider = StubProvider()
    context = (
        "PRODUCTS:\n"
        "Precision Burr Grinder — 189.00 — conical burr grinder [tags=grinder,burr]\n"
        "French Press 1L — 39.00 — immersion brewer [tags=french-press]"
    )
    reply = provider.chat("I need a good burr grinder", [], context)
    assert "Grinder" in reply


def test_get_provider_defaults_to_stub():
    from app.ai.base import get_provider

    # With no keys configured, the factory must fall back to the stub.
    assert get_provider().name == "stub"
