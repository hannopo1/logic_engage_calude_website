"""Pluggable payment layer — COD-first launch.

`CODProvider` (default) needs no external account: the order is accepted unpaid
and cash is collected on delivery (fulfillment_service marks it paid when the
last PO is delivered).

`GatewayStubProvider` documents the adapter contract for a real gateway
(Paymob, Stripe, …). To go live: implement `authorize()` against the gateway's
API, set PAYMENT_PROVIDER=gateway plus the gateway keys in .env. No call-site
changes are needed anywhere else.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class PaymentResult:
    accepted: bool
    method: str
    status: str  # unpaid | paid | pending
    detail: str = ""


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    def authorize(self, amount: float, currency: str, meta: dict) -> PaymentResult:
        """
        Authorize a payment for checkout.
        
        Parameters:
            amount (float): Payment amount.
            currency (str): Payment currency.
            meta (dict): Additional payment metadata.
        
        Returns:
            PaymentResult: The authorization outcome.
        
        Normal payment declines are represented in the result rather than raised as exceptions.
        """


class CODProvider(PaymentProvider):
    """Cash on delivery — dominant in the Egyptian market, zero setup cost."""

    name = "cod"

    def authorize(self, amount: float, currency: str, meta: dict) -> PaymentResult:
        """
        Authorize payment for cash on delivery.
        
        Parameters:
            amount (float): Order amount.
            currency (str): Payment currency.
            meta (dict): Additional payment metadata.
        
        Returns:
            PaymentResult: An accepted COD result with an unpaid status.
        """
        return PaymentResult(
            accepted=True,
            method="cod",
            status="unpaid",
            detail="الدفع نقداً عند الاستلام",
        )


class GatewayStubProvider(PaymentProvider):
    """Placeholder for a real gateway (Paymob/Stripe). Not configured yet."""

    name = "gateway"

    def authorize(self, amount: float, currency: str, meta: dict) -> PaymentResult:
        """
        Report that electronic gateway payment authorization is unavailable.
        
        Returns:
            PaymentResult: An unpaid result marked as declined, with instructions for enabling the payment gateway.
        """
        return PaymentResult(
            accepted=False,
            method="gateway",
            status="unpaid",
            detail=(
                "بوابة الدفع الإلكتروني غير مفعّلة بعد. "
                "فعّلها بضبط PAYMENT_PROVIDER=gateway ومفاتيح المزود في .env "
                "(انظر docs/launch.md)."
            ),
        )


def get_payment_provider(method: str | None = None) -> PaymentProvider:
    """
    Selects the payment provider for a checkout method.
    
    Parameters:
        method (str | None): Customer-selected payment method. Gateway requests use the gateway stub; other values default to cash on delivery.
    
    Returns:
        PaymentProvider: The selected payment provider.
    """
    chosen = (method or "cod").lower()
    if chosen == "gateway" and settings.PAYMENT_PROVIDER.lower() == "gateway":
        return GatewayStubProvider()  # replaced by a real adapter when configured
    if chosen == "gateway":
        return GatewayStubProvider()  # will decline with a clear message
    return CODProvider()
