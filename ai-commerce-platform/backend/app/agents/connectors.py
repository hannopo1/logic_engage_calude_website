"""Supplier connectors — how a purchase actually gets executed.

Compliance rule (load-bearing): we never script/scrape a supplier's checkout.
Automated purchasing happens ONLY through an official API with a real account.
Until such credentials exist, marketplace suppliers run in `assisted` mode:
the agent prepares the complete purchase package and the operator executes it.

To enable a real connector later:
  1. Obtain the official seller/partner API credentials for the supplier.
  2. Implement `place_order()` in the matching connector below.
  3. Set the supplier row's mode='api' (admin API) and AGENT_MODE=api in .env.
No other code changes are required — the purchasing agent dispatches here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.models.purchase_order import PurchaseOrder


class NotConfiguredError(RuntimeError):
    """Raised by connectors whose official API credentials are not set up."""


@dataclass
class PurchaseResult:
    ok: bool
    supplier_order_ref: str = ""
    detail: str = ""


class SupplierConnector:
    """Interface every connector implements."""

    slug: str = "base"

    def place_order(self, po: PurchaseOrder, ship_to: str) -> PurchaseResult:
        raise NotConfiguredError(f"Connector '{self.slug}' is not configured")


class SimulationConnector(SupplierConnector):
    """Fake executor for demos/tests — spends no real money."""

    slug = "simulation"

    def place_order(self, po: PurchaseOrder, ship_to: str) -> PurchaseResult:
        ref = f"SIM-{uuid.uuid4().hex[:10].upper()}"
        return PurchaseResult(ok=True, supplier_order_ref=ref, detail="محاكاة — لم يُنفق مال حقيقي")


class AmazonEGConnector(SupplierConnector):
    """Amazon Egypt.

    Official path: Amazon Business API / Punchout (requires an Amazon Business
    account) — NOT the retail website. Credentials → implement place_order.
    """

    slug = "amazon-eg"


class NoonConnector(SupplierConnector):
    """Noon Egypt.

    Official path: noon partner/seller integrations (requires a partner
    account). Credentials → implement place_order.
    """

    slug = "noon-eg"


class JumiaConnector(SupplierConnector):
    """Jumia Egypt.

    Official path: Jumia vendor/partner API (requires a partner account).
    Credentials → implement place_order.
    """

    slug = "jumia-eg"


# OLX/Dubizzle is person-to-person classifieds: no purchase API exists, so it
# intentionally has no connector — those POs are always operator-manual.

_REGISTRY: dict[str, SupplierConnector] = {
    c.slug: c()
    for c in (SimulationConnector, AmazonEGConnector, NoonConnector, JumiaConnector)
}


def get_connector(slug: str) -> SupplierConnector | None:
    return _REGISTRY.get(slug)
