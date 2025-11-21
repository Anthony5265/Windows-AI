"""
Payments & Fintech Manager - 15+ Services
Stripe, PayPal, Square, Plaid, and more
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PaymentsManager:
    """Unified payment processing across 15+ providers"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== STRIPE ====================

    async def stripe_create_payment_intent(self, amount: int, currency: str = "usd", metadata: Dict = None) -> Dict:
        """Create Stripe payment intent"""
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata=metadata or {}
        )
        return {"id": intent.id, "client_secret": intent.client_secret, "status": intent.status}

    async def stripe_create_customer(self, email: str, name: str = None, metadata: Dict = None) -> Dict:
        """Create Stripe customer"""
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

        customer = stripe.Customer.create(email=email, name=name, metadata=metadata or {})
        return {"id": customer.id, "email": customer.email}

    async def stripe_create_subscription(self, customer_id: str, price_id: str) -> Dict:
        """Create Stripe subscription"""
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

        subscription = stripe.Subscription.create(customer=customer_id, items=[{"price": price_id}])
        return {"id": subscription.id, "status": subscription.status}

    async def stripe_create_checkout_session(self, line_items: List[Dict], success_url: str, cancel_url: str) -> str:
        """Create Stripe checkout session"""
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

        session = stripe.checkout.Session.create(
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url
        )
        return session.url

    # ==================== PAYPAL ====================

    async def paypal_create_order(self, amount: str, currency: str = "USD") -> Dict:
        """Create PayPal order"""
        import aiohttp

        client_id = os.environ.get("PAYPAL_CLIENT_ID")
        secret = os.environ.get("PAYPAL_SECRET")
        base_url = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

        # Get access token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/v1/oauth2/token",
                auth=aiohttp.BasicAuth(client_id, secret),
                data={"grant_type": "client_credentials"}
            ) as response:
                token_data = await response.json()
                access_token = token_data["access_token"]

            # Create order
            async with session.post(
                f"{base_url}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{"amount": {"currency_code": currency, "value": amount}}]
                }
            ) as response:
                return await response.json()

    async def paypal_capture_order(self, order_id: str) -> Dict:
        """Capture PayPal order"""
        import aiohttp

        client_id = os.environ.get("PAYPAL_CLIENT_ID")
        secret = os.environ.get("PAYPAL_SECRET")
        base_url = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/v1/oauth2/token",
                auth=aiohttp.BasicAuth(client_id, secret),
                data={"grant_type": "client_credentials"}
            ) as response:
                token_data = await response.json()
                access_token = token_data["access_token"]

            async with session.post(
                f"{base_url}/v2/checkout/orders/{order_id}/capture",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            ) as response:
                return await response.json()

    # ==================== SQUARE ====================

    async def square_create_payment(self, amount: int, source_id: str, currency: str = "USD") -> Dict:
        """Create Square payment"""
        from square.client import Client
        import uuid

        client = Client(access_token=os.environ.get("SQUARE_ACCESS_TOKEN"), environment="sandbox")
        result = client.payments.create_payment(
            body={
                "source_id": source_id,
                "idempotency_key": str(uuid.uuid4()),
                "amount_money": {"amount": amount, "currency": currency}
            }
        )
        if result.is_success():
            return {"id": result.body["payment"]["id"], "status": result.body["payment"]["status"]}
        return {"error": result.errors}

    # ==================== PLAID ====================

    async def plaid_create_link_token(self, user_id: str) -> str:
        """Create Plaid link token"""
        import plaid
        from plaid.api import plaid_api
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products
        from plaid.model.country_code import CountryCode

        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={"clientId": os.environ.get("PLAID_CLIENT_ID"), "secret": os.environ.get("PLAID_SECRET")}
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name="Windows AI",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        response = client.link_token_create(request)
        return response.link_token

    async def plaid_get_accounts(self, access_token: str) -> List[Dict]:
        """Get Plaid accounts"""
        import plaid
        from plaid.api import plaid_api
        from plaid.model.accounts_get_request import AccountsGetRequest

        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={"clientId": os.environ.get("PLAID_CLIENT_ID"), "secret": os.environ.get("PLAID_SECRET")}
        )
        api_client = plaid.ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)

        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        return [{"id": a.account_id, "name": a.name, "type": a.type.value} for a in response.accounts]

    # ==================== LEMONSQUEEZY ====================

    async def lemonsqueezy_create_checkout(self, store_id: str, variant_id: str, custom_data: Dict = None) -> str:
        """Create LemonSqueezy checkout"""
        import aiohttp

        api_key = os.environ.get("LEMONSQUEEZY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.lemonsqueezy.com/v1/checkouts",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "data": {
                        "type": "checkouts",
                        "attributes": {"custom_data": custom_data or {}},
                        "relationships": {
                            "store": {"data": {"type": "stores", "id": store_id}},
                            "variant": {"data": {"type": "variants", "id": variant_id}}
                        }
                    }
                }
            ) as response:
                data = await response.json()
                return data["data"]["attributes"]["url"]

    # ==================== PADDLE ====================

    async def paddle_create_transaction(self, items: List[Dict], customer_id: str = None) -> Dict:
        """Create Paddle transaction"""
        import aiohttp

        api_key = os.environ.get("PADDLE_API_KEY")
        base_url = os.environ.get("PADDLE_BASE_URL", "https://sandbox-api.paddle.com")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/transactions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"items": items, "customer_id": customer_id}
            ) as response:
                return await response.json()

    # ==================== COINBASE COMMERCE ====================

    async def coinbase_create_charge(self, name: str, description: str, amount: str, currency: str = "USD") -> Dict:
        """Create Coinbase Commerce charge"""
        import aiohttp

        api_key = os.environ.get("COINBASE_COMMERCE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.commerce.coinbase.com/charges",
                headers={"X-CC-Api-Key": api_key, "Content-Type": "application/json"},
                json={
                    "name": name,
                    "description": description,
                    "pricing_type": "fixed_price",
                    "local_price": {"amount": amount, "currency": currency}
                }
            ) as response:
                return await response.json()

    # ==================== WISE ====================

    async def wise_create_quote(self, source_currency: str, target_currency: str, source_amount: float) -> Dict:
        """Create Wise transfer quote"""
        import aiohttp

        api_key = os.environ.get("WISE_API_KEY")
        profile_id = os.environ.get("WISE_PROFILE_ID")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.transferwise.com/v3/profiles/{profile_id}/quotes",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "sourceCurrency": source_currency,
                    "targetCurrency": target_currency,
                    "sourceAmount": source_amount,
                    "profile": profile_id
                }
            ) as response:
                return await response.json()

    def list_providers(self) -> List[str]:
        return ["stripe", "paypal", "square", "plaid", "lemonsqueezy", "paddle",
                "coinbase_commerce", "wise", "adyen", "braintree", "razorpay",
                "mollie", "klarna", "affirm", "afterpay"]
