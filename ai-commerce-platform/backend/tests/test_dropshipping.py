"""DB-free unit tests for the drop-shipping layer: state machine, margin math,
connector registry, and the payment factory."""
from __future__ import annotations

from decimal import Decimal


# ---------- PO state machine ----------

def test_state_machine_happy_path():
    from app.services.fulfillment_service import can_transition

    chain = ["pending_sourcing", "awaiting_approval", "purchasing", "purchased", "shipped", "delivered"]
    for cur, nxt in zip(chain, chain[1:]):
        assert can_transition(cur, nxt), f"{cur} → {nxt} must be allowed"


def test_state_machine_blocks_illegal_jumps():
    from app.services.fulfillment_service import can_transition

    assert not can_transition("pending_sourcing", "purchased")
    assert not can_transition("delivered", "shipped")
    assert not can_transition("cancelled", "awaiting_approval")
    assert not can_transition("purchased", "awaiting_approval")


def test_failed_po_can_retry():
    from app.services.fulfillment_service import can_transition

    assert can_transition("failed", "pending_sourcing")
    assert can_transition("failed", "cancelled")


# ---------- margin math ----------

def test_margin_percent():
    from app.agents.sourcing import margin_percent

    # selling 100, cost 80 → 20%
    assert margin_percent(Decimal("100"), Decimal("80")) == Decimal("20")
    # zero selling price never divides by zero
    assert margin_percent(Decimal("0"), Decimal("10")) == Decimal("0")


# ---------- connectors ----------

def test_connector_registry_and_compliance():
    from app.agents.connectors import (
        NotConfiguredError,
        SimulationConnector,
        get_connector,
    )

    # Marketplace connectors exist as stubs but refuse to run unconfigured —
    # the compliance guarantee that nothing auto-buys without an official API.
    for slug in ("amazon-eg", "noon-eg", "jumia-eg"):
        connector = get_connector(slug)
        assert connector is not None
        try:
            connector.place_order(None, "")  # type: ignore[arg-type]
            raise AssertionError("unconfigured connector must raise")
        except NotConfiguredError:
            pass

    # OLX deliberately has no connector (person-to-person classifieds).
    assert get_connector("olx-eg") is None

    # Generic API drop-ship connector exists but is gated until configured.
    api_ds = get_connector("api-dropship")
    assert api_ds is not None
    try:
        api_ds.place_order(None, "Cairo")  # type: ignore[arg-type]
        raise AssertionError("unconfigured api-dropship must raise")
    except NotConfiguredError:
        pass

    # Simulation works and never returns an empty ref.
    result = SimulationConnector().place_order(None, "Cairo")  # type: ignore[arg-type]
    assert result.ok and result.supplier_order_ref.startswith("SIM-")


# ---------- payments ----------

def test_payment_factory_cod_default():
    from app.services.payments import get_payment_provider

    cod = get_payment_provider(None)
    assert cod.name == "cod"
    res = cod.authorize(100.0, "EGP", {})
    assert res.accepted and res.status == "unpaid"


def test_payment_gateway_declines_until_configured():
    from app.services.payments import get_payment_provider

    gw = get_payment_provider("gateway")
    res = gw.authorize(100.0, "EGP", {})
    assert not res.accepted  # PAYMENT_PROVIDER=cod by default → gateway declines
