"""Import all models so Alembic's autogenerate and metadata see them."""
from app.models.user import User  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.cart import Cart, CartItem  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.supplier import Supplier, SupplierOffer  # noqa: F401
from app.models.purchase_order import PurchaseOrder, PurchaseOrderEvent  # noqa: F401
from app.models.analytics import AnalyticsEvent  # noqa: F401
from app.models.coupon import Coupon  # noqa: F401
from app.models.review import Review  # noqa: F401
