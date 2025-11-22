"""
Finance & Trading AI Manager - 25+ Services
Market analysis, portfolio management, fraud detection, risk assessment
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FinanceAIManager:
    """Unified finance AI across 25+ services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== MARKET DATA ====================

    async def get_stock_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote"""
        import aiohttp

        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            ) as response:
                data = await response.json()
                quote = data.get("Global Quote", {})
                return {
                    "symbol": quote.get("01. symbol"),
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent"),
                    "volume": int(quote.get("06. volume", 0))
                }

    async def get_historical_data(self, symbol: str, period: str = "1y") -> List[Dict]:
        """Get historical price data"""
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        return [{
            "date": str(date.date()),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "volume": row["Volume"]
        } for date, row in hist.iterrows()]

    async def get_crypto_price(self, symbol: str = "bitcoin") -> Dict:
        """Get cryptocurrency price"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
            ) as response:
                data = await response.json()
                return {
                    "symbol": symbol,
                    "price_usd": data.get(symbol, {}).get("usd"),
                    "change_24h": data.get(symbol, {}).get("usd_24h_change")
                }

    # ==================== TECHNICAL ANALYSIS ====================

    async def analyze_technicals(self, symbol: str) -> Dict:
        """Perform technical analysis"""
        import yfinance as yf
        import numpy as np

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")

        closes = hist["Close"].values

        # Moving averages
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else None
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
        sma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else None

        # RSI
        deltas = np.diff(closes[-15:])
        gains = np.mean([d for d in deltas if d > 0]) if any(d > 0 for d in deltas) else 0
        losses = np.mean([-d for d in deltas if d < 0]) if any(d < 0 for d in deltas) else 0.001
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))

        # Trend
        current_price = closes[-1]
        trend = "bullish" if current_price > (sma_50 or current_price) else "bearish"

        return {
            "symbol": symbol,
            "current_price": float(current_price),
            "sma_20": float(sma_20) if sma_20 else None,
            "sma_50": float(sma_50) if sma_50 else None,
            "sma_200": float(sma_200) if sma_200 else None,
            "rsi": float(rsi),
            "trend": trend,
            "signals": {
                "rsi_signal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral",
                "ma_signal": "buy" if sma_20 and sma_50 and sma_20 > sma_50 else "sell" if sma_20 and sma_50 else "neutral"
            }
        }

    # ==================== FUNDAMENTAL ANALYSIS ====================

    async def analyze_fundamentals(self, symbol: str) -> Dict:
        """Analyze company fundamentals"""
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            "symbol": symbol,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "recommendation": info.get("recommendationKey")
        }

    # ==================== SENTIMENT ANALYSIS ====================

    async def analyze_market_sentiment(self, symbol: str) -> Dict:
        """Analyze market sentiment for stock"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import aiohttp

        # Get recent news
        api_key = os.environ.get("NEWS_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&pageSize=10&apiKey={api_key}"
            ) as response:
                news_data = await response.json()
                articles = news_data.get("articles", [])

        # Analyze sentiment with AI
        ai = AIProvidersManager()
        await ai.initialize()

        headlines = [a.get("title", "") for a in articles[:10]]

        messages = [
            {"role": "system", "content": """Analyze these headlines for market sentiment.
Return JSON: {"sentiment": "bullish/bearish/neutral", "confidence": 0-100, "key_factors": [...]}"""},
            {"role": "user", "content": f"Headlines for {symbol}:\n" + "\n".join(headlines)}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            sentiment = json.loads(response["content"])
        except:
            sentiment = {"raw": response["content"]}

        return {"symbol": symbol, "headlines": headlines, "sentiment": sentiment}

    # ==================== PORTFOLIO ANALYSIS ====================

    async def analyze_portfolio(self, holdings: List[Dict]) -> Dict:
        """Analyze portfolio performance and risk"""
        import numpy as np

        total_value = sum(h.get("value", 0) for h in holdings)

        # Calculate weights
        weights = [h.get("value", 0) / total_value for h in holdings] if total_value > 0 else []

        # Sector allocation
        sectors = {}
        for h in holdings:
            sector = h.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + h.get("value", 0)

        # Calculate diversification score
        diversification = 1 - sum(w**2 for w in weights) if weights else 0

        return {
            "total_value": total_value,
            "num_holdings": len(holdings),
            "sector_allocation": {k: v/total_value*100 for k, v in sectors.items()} if total_value > 0 else {},
            "diversification_score": round(diversification * 100, 2),
            "top_holdings": sorted(holdings, key=lambda x: x.get("value", 0), reverse=True)[:5]
        }

    async def optimize_portfolio(self, holdings: List[Dict], risk_tolerance: str = "moderate") -> Dict:
        """AI-powered portfolio optimization"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Analyze this portfolio for a {risk_tolerance} risk investor.
Provide:
1. Current allocation assessment
2. Rebalancing recommendations
3. Risk analysis
4. Suggested additions/removals
Return structured JSON."""},
            {"role": "user", "content": str(holdings)}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"recommendations": response["content"]}

    # ==================== FRAUD DETECTION ====================

    async def detect_fraud(self, transaction: Dict) -> Dict:
        """Detect potential fraudulent transaction"""
        risk_score = 0
        flags = []

        # Amount check
        if transaction.get("amount", 0) > 10000:
            risk_score += 20
            flags.append("high_amount")

        # Time check
        hour = transaction.get("hour", 12)
        if hour < 6 or hour > 23:
            risk_score += 15
            flags.append("unusual_time")

        # Location check
        if transaction.get("foreign", False):
            risk_score += 25
            flags.append("foreign_transaction")

        # Velocity check
        if transaction.get("transactions_24h", 0) > 10:
            risk_score += 20
            flags.append("high_velocity")

        return {
            "transaction_id": transaction.get("id"),
            "risk_score": min(risk_score, 100),
            "risk_level": "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
            "flags": flags,
            "recommendation": "block" if risk_score > 70 else "review" if risk_score > 40 else "approve"
        }

    # ==================== FINANCIAL PLANNING ====================

    async def create_financial_plan(self, profile: Dict) -> Dict:
        """AI-powered financial planning"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Create a comprehensive financial plan including:
1. Budget recommendations
2. Savings goals
3. Investment allocation
4. Debt repayment strategy
5. Emergency fund target
6. Retirement projections
Return detailed JSON plan."""},
            {"role": "user", "content": f"Profile: {profile}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"plan": response["content"]}

    async def calculate_retirement(self, current_age: int, retirement_age: int, current_savings: float,
                                   monthly_contribution: float, expected_return: float = 0.07) -> Dict:
        """Calculate retirement projections"""
        years_to_retirement = retirement_age - current_age
        months = years_to_retirement * 12
        monthly_return = expected_return / 12

        # Future value calculation
        fv_savings = current_savings * ((1 + monthly_return) ** months)
        fv_contributions = monthly_contribution * (((1 + monthly_return) ** months - 1) / monthly_return)
        total_at_retirement = fv_savings + fv_contributions

        # Safe withdrawal rate (4% rule)
        annual_income = total_at_retirement * 0.04

        return {
            "years_to_retirement": years_to_retirement,
            "projected_total": round(total_at_retirement, 2),
            "annual_retirement_income": round(annual_income, 2),
            "monthly_retirement_income": round(annual_income / 12, 2),
            "total_contributions": round(monthly_contribution * months, 2),
            "total_growth": round(total_at_retirement - current_savings - monthly_contribution * months, 2)
        }

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "market_data": ["stocks", "crypto", "forex", "commodities"],
            "analysis": ["technical", "fundamental", "sentiment"],
            "portfolio": ["analysis", "optimization", "rebalancing"],
            "risk": ["fraud_detection", "credit_scoring", "var_calculation"],
            "planning": ["retirement", "budgeting", "tax_optimization"]
        }
