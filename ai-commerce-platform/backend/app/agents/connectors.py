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

import httpx

from app.core.config import settings
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


class AmazonBusinessConnector(SupplierConnector):
    """Amazon Business API connector — TEMPLATE (official B2B procurement path).

    This is the ONLY compliant way to automate Amazon purchases: the Amazon
    *Business* API, tied to an approved Amazon Business account. It is NOT the
    retail amazon.eg website, and it is NOT scraping — do not attempt either.

    ── What is real vs. what you must fill in ────────────────────────────────
    • Real & complete here: the OAuth2 (Login with Amazon) token exchange in
      `_get_access_token()`, credential gating, and the request scaffolding.
    • You must fill in `_submit_order()` with the exact procurement endpoint for
      YOUR integration type. Amazon Business exposes ordering through one of:
        - the Amazon Business API (create-cart / create-order calls), or
        - Punchout (cXML) if your account uses Punchout catalogs.
      The endpoint + payload differ per account, so Amazon documents them after
      you are approved. Until then this connector raises NotConfiguredError and
      the platform keeps using the safe assisted flow.

    ── How to activate (once approved) ───────────────────────────────────────
    1. Register an Amazon Business account and request API/Punchout access.
    2. Create an LWA (Login with Amazon) security profile → get client id/secret
       + a long-lived refresh token for your integration user.
    3. Put them in .env: AMAZON_BUSINESS_CLIENT_ID / _CLIENT_SECRET /
       _REFRESH_TOKEN / _API_BASE / _MARKETPLACE_ID (see .env.example).
    4. Implement `_submit_order()` per Amazon's docs for your integration type.
    5. Set the supplier row mode='api' (admin) and AGENT_MODE=api in .env.
    The purchasing agent then routes buys here automatically — no other changes.
    """

    slug = "amazon-eg"

    def _configured(self) -> bool:
        return bool(
            settings.AMAZON_BUSINESS_CLIENT_ID
            and settings.AMAZON_BUSINESS_CLIENT_SECRET
            and settings.AMAZON_BUSINESS_REFRESH_TOKEN
            and settings.AMAZON_BUSINESS_API_BASE
        )

    def _get_access_token(self) -> str:
        """Exchange the refresh token for a short-lived access token (LWA OAuth2).

        This is the standard, documented Login-with-Amazon flow and is complete;
        it needs only your real client id/secret + refresh token.
        """
        resp = httpx.post(
            settings.AMAZON_BUSINESS_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": settings.AMAZON_BUSINESS_REFRESH_TOKEN,
                "client_id": settings.AMAZON_BUSINESS_CLIENT_ID,
                "client_secret": settings.AMAZON_BUSINESS_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _submit_order(self, access_token: str, po: PurchaseOrder, ship_to: str) -> str:
        """Place the actual order and return the Amazon order reference.

        FILL THIS IN per your Amazon Business integration type. The shape below
        is a documented starting point for the API path — adjust the endpoint,
        payload, and response parsing to match the docs Amazon gives you after
        approval. `po.offer.external_sku` / `po.offer.url` hold the item ASIN or
        product URL you saved on the supplier offer.
        """
        raise NotConfiguredError(
            "Amazon Business order submission not implemented yet — fill in "
            "_submit_order() with your account's procurement endpoint (API or "
            "Punchout). See the class docstring."
        )
        # Example scaffold (uncomment + adapt once you have the real endpoint):
        # item_ref = (po.offer.external_sku or po.offer.url) if po.offer else None
        # resp = httpx.post(
        #     f"{settings.AMAZON_BUSINESS_API_BASE}/orders",
        #     headers={
        #         "Authorization": f"Bearer {access_token}",
        #         "x-amz-marketplace-id": settings.AMAZON_BUSINESS_MARKETPLACE_ID,
        #         "Content-Type": "application/json",
        #     },
        #     json={
        #         "items": [{"asin": item_ref, "quantity": po.quantity}],
        #         "shippingAddress": ship_to,          # map to Amazon's address schema
        #         "maxUnitPrice": str(po.expected_cost),  # price-drift guard
        #     },
        #     timeout=60,
        # )
        # resp.raise_for_status()
        # return resp.json()["orderId"]

    def place_order(self, po: PurchaseOrder, ship_to: str) -> PurchaseResult:
        if not self._configured():
            raise NotConfiguredError(
                "Amazon Business API credentials are not set. Fill AMAZON_BUSINESS_* "
                "in .env and set the supplier mode='api' to enable auto-purchase."
            )
        token = self._get_access_token()
        order_ref = self._submit_order(token, po, ship_to)
        return PurchaseResult(
            ok=True,
            supplier_order_ref=order_ref,
            detail="تم الشراء عبر Amazon Business API",
        )


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
    for c in (SimulationConnector, AmazonBusinessConnector, NoonConnector, JumiaConnector)
}


def get_connector(slug: str) -> SupplierConnector | None:
    return _REGISTRY.get(slug)
