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
        """
        Place a purchase order through the connector.
        
        Parameters:
            po (PurchaseOrder): Purchase order to execute.
            ship_to (str): Shipping address for the order.
        
        Raises:
            NotConfiguredError: Always, because this base connector has no order implementation.
        """
        raise NotConfiguredError(f"Connector '{self.slug}' is not configured")


class SimulationConnector(SupplierConnector):
    """Fake executor for demos/tests — spends no real money."""

    slug = "simulation"

    def place_order(self, po: PurchaseOrder, ship_to: str) -> PurchaseResult:
        """
        Simulate placing a purchase order without contacting an external supplier.
        
        Parameters:
        	po (PurchaseOrder): The purchase order to simulate.
        	ship_to (str): The shipping destination.
        
        Returns:
        	PurchaseResult: A successful result with a generated simulation reference.
        """
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
        """Determine whether the Amazon Business connector has all required settings.
        
        Returns:
        	bool: `True` if all required Amazon Business credentials and API settings are configured, `False` otherwise.
        """
        return bool(
            settings.AMAZON_BUSINESS_CLIENT_ID
            and settings.AMAZON_BUSINESS_CLIENT_SECRET
            and settings.AMAZON_BUSINESS_REFRESH_TOKEN
            and settings.AMAZON_BUSINESS_API_BASE
        )

    def _get_access_token(self) -> str:
        """Exchange the configured OAuth2 refresh token for an access token.
        
        Returns:
            str: The access token.
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
        """Define the Amazon Business order-submission hook.
        
        Parameters:
            access_token (str): OAuth2 access token for the Amazon Business API.
            po (PurchaseOrder): Purchase order to submit.
            ship_to (str): Shipping address for the order.
        
        Raises:
            NotConfiguredError: Always, because order submission is not implemented.
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
        """
        Place an order through the Amazon Business API.
        
        Parameters:
            po (PurchaseOrder): Purchase order to submit.
            ship_to (str): Shipping address for the order.
        
        Returns:
            PurchaseResult: Successful purchase result containing the supplier order reference.
        
        Raises:
            NotConfiguredError: If Amazon Business API credentials are not configured or order submission is unavailable.
        """
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


class ApiDropshipConnector(SupplierConnector):
    """Generic official drop-ship supplier connector — READY TEMPLATE.

    Unlike the retail marketplaces, a real drop-ship supplier/aggregator gives
    you an official REST order API. This connector implements the *conventional*
    shape of such an API end-to-end, so for many suppliers it works after only
    filling `.env` — and where field names differ, you tweak a few lines.

    Expected supplier API (adjust to your supplier's docs):
      POST {DROPSHIP_API_BASE}/orders
        headers: Authorization: Bearer <key>   (or  X-Api-Key: <key>)
        body: { external_id, items:[{sku, quantity, product_url}],
                shipping_address, max_unit_cost }
        resp: { <DROPSHIP_ORDER_ID_FIELD>: "..." }
      GET  {DROPSHIP_API_BASE}/orders/{ref}     → status + tracking (optional)

    Activation:
      1. Get your supplier's API base URL + key.
      2. Fill DROPSHIP_API_BASE / DROPSHIP_API_KEY / DROPSHIP_API_AUTH_STYLE /
         DROPSHIP_ORDER_ID_FIELD in .env.
      3. In the admin, create/set a supplier with slug 'api-dropship', mode='api'.
      4. Set AGENT_MODE=api. The purchasing agent routes buys here automatically.
    """

    slug = "api-dropship"

    def _configured(self) -> bool:
        """Determine whether the drop-shipping API has the required configuration.
        
        Returns:
        	bool: `True` if the API base URL and API key are configured, `False` otherwise.
        """
        return bool(settings.DROPSHIP_API_BASE and settings.DROPSHIP_API_KEY)

    def _auth_headers(self) -> dict[str, str]:
        """Builds authentication headers for the configured dropship API.
        
        Returns:
        	dict[str, str]: An ``X-Api-Key`` header when configured for API-key authentication; otherwise, a Bearer authorization header.
        """
        if settings.DROPSHIP_API_AUTH_STYLE.lower() == "x-api-key":
            return {"X-Api-Key": settings.DROPSHIP_API_KEY}
        return {"Authorization": f"Bearer {settings.DROPSHIP_API_KEY}"}

    def place_order(self, po: PurchaseOrder, ship_to: str) -> PurchaseResult:
        """
        Place a purchase order through the configured drop-shipping supplier API.
        
        Parameters:
            po (PurchaseOrder): Purchase order containing the item, quantity, and cost limit.
            ship_to (str): Shipping address supplied to the drop-shipping provider.
        
        Returns:
            PurchaseResult: Successful result containing the supplier's order reference.
        
        Raises:
            NotConfiguredError: If the supplier API is not configured or the response lacks an order reference.
        """
        if not self._configured():
            raise NotConfiguredError(
                "Drop-ship supplier API not configured. Fill DROPSHIP_API_* in .env "
                "and set the supplier mode='api' to enable auto-purchase."
            )
        offer = po.offer
        item = {
            "sku": (offer.external_sku if offer else None),
            "product_url": (offer.url if offer else None),
            "quantity": po.quantity,
        }
        payload = {
            "external_id": f"PO-{po.id}",  # your order id → idempotency on their side
            "items": [item],
            "shipping_address": ship_to,   # map to the supplier's address schema if needed
            "max_unit_cost": str(po.expected_cost) if po.expected_cost is not None else None,
        }
        resp = httpx.post(
            f"{settings.DROPSHIP_API_BASE.rstrip('/')}/orders",
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        ref = (
            data.get(settings.DROPSHIP_ORDER_ID_FIELD)
            or data.get("id")
            or data.get("reference")
        )
        if not ref:
            raise NotConfiguredError(
                "Order placed but no order id found in the response — set "
                "DROPSHIP_ORDER_ID_FIELD to match your supplier's response."
            )
        return PurchaseResult(ok=True, supplier_order_ref=str(ref), detail="تم الشراء عبر API المورد")

    def get_tracking(self, order_ref: str) -> dict:
        """
        Fetch the current status and tracking details for a drop-ship order.
        
        Parameters:
            order_ref (str): Supplier-assigned order reference.
        
        Returns:
            dict: Supplier response containing the order status and tracking details.
        
        Raises:
            NotConfiguredError: If the drop-ship supplier API is not configured.
        """
        if not self._configured():
            raise NotConfiguredError("Drop-ship supplier API not configured.")
        resp = httpx.get(
            f"{settings.DROPSHIP_API_BASE.rstrip('/')}/orders/{order_ref}",
            headers=self._auth_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


# OLX/Dubizzle is person-to-person classifieds: no purchase API exists, so it
# intentionally has no connector — those POs are always operator-manual.

_REGISTRY: dict[str, SupplierConnector] = {
    c.slug: c()
    for c in (
        SimulationConnector,
        AmazonBusinessConnector,
        NoonConnector,
        JumiaConnector,
        ApiDropshipConnector,
    )
}


def get_connector(slug: str) -> SupplierConnector | None:
    """Retrieve the registered supplier connector for a slug.
    
    Parameters:
    	slug (str): The connector identifier.
    
    Returns:
    	SupplierConnector | None: The registered connector, or `None` if no connector matches the slug.
    """
    return _REGISTRY.get(slug)
