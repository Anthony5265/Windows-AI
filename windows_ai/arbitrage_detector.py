"""
ArbitrageDetector — deterministic analysis facade for Windows AI.

Provides structured transaction/market-text analysis without fabricating
confidence or risk values when no quantitative market data is supplied.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import hashlib
import json
import logging
import math
import os
import tempfile
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageDetectorResult:
    result_id: str
    analysis: Dict[str, Any]
    recommendations: List[str]
    risk_score: float


class ArbitrageDetectorSystem:
    """Arbitrage analysis system with deterministic, auditable behavior."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.is_dir():
            raise ValueError("data_dir must be a directory")
        self._state_file = self.data_dir / "arbitrage_detector_state.json"
        self.results: List[ArbitrageDetectorResult] = []
        self._config = {"initialized": True, "version": "1.1.0"}
        self._cache = {}
        self._load_state()
        logger.info("ArbitrageDetector initialized")

    def _hash_transaction(self, tx_data):
        return hashlib.sha256(str(tx_data).encode("utf-8")).hexdigest()

    def _analyze_transfer_graph(self, transactions):
        graph = {}
        for tx in transactions:
            sender = tx.get("from", "unknown")
            receiver = tx.get("to", "unknown")
            amount = tx.get("amount", 0)
            graph.setdefault(sender, []).append({"to": receiver, "amount": amount})
        return graph

    def _detect_cycles(self, graph, max_depth=10):
        if max_depth < 2:
            raise ValueError("max_depth must be at least 2")
        cycles = []
        for start in list(graph.keys())[:100]:
            visited = set()
            stack = [(start, [start])]
            while stack:
                node, path = stack.pop()
                if len(path) > max_depth:
                    continue
                for edge in graph.get(node, []):
                    next_node = edge["to"]
                    if next_node == start and len(path) > 2:
                        cycles.append(list(path))
                    elif next_node not in visited:
                        visited.add(next_node)
                        stack.append((next_node, path + [next_node]))
        return cycles

    def _calculate_risk_score(self, address_history):
        score = 50.0
        if not address_history:
            return score
        amounts = [float(tx.get("amount", 0)) for tx in address_history]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0
        if avg_amount > 0 and max_amount > avg_amount * 10:
            score += 20
        if len(address_history) > 100:
            score += 10
        unique_counterparties = len(set(tx.get("to", "") for tx in address_history))
        if unique_counterparties > 50:
            score += 10
        return min(100.0, max(0.0, score))

    def _moving_average_price(self, prices, window=20):
        if window < 1:
            raise ValueError("window must be positive")
        return [sum(prices[max(0, i - window + 1):i + 1]) / (i - max(0, i - window + 1) + 1) for i in range(len(prices))]

    def _rsi(self, prices, period=14):
        if period < 1:
            raise ValueError("period must be positive")
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [max(0, d) for d in deltas]
        losses = [max(0, -d) for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi = [50.0] * (period + 1)
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                value = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                value = 100 - 100 / (1 + rs)
            rsi.append(value)
        return rsi

    def _bollinger_bands(self, prices, window=20, num_std=2):
        if window < 1 or num_std < 0:
            raise ValueError("window must be positive and num_std non-negative")
        upper, lower, mid = [], [], []
        for i in range(len(prices)):
            start = max(0, i - window + 1)
            w = prices[start:i + 1]
            mean = sum(w) / len(w)
            std = (sum((x - mean) ** 2 for x in w) / len(w)) ** 0.5
            mid.append(mean)
            upper.append(mean + num_std * std)
            lower.append(mean - num_std * std)
        return upper, mid, lower

    def _portfolio_metrics(self, returns):
        if not returns:
            return {"sharpe": 0, "volatility": 0, "max_drawdown": 0}
        mean_r = sum(returns) / len(returns)
        vol = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe = mean_r / vol * (252 ** 0.5) if vol > 0 else 0.0
        cumulative = [1.0]
        for r in returns:
            cumulative.append(cumulative[-1] * (1 + r))
        peak = cumulative[0]
        max_dd = 0.0
        for value in cumulative:
            peak = max(peak, value)
            if peak > 0:
                max_dd = max(max_dd, (peak - value) / peak)
        return {"sharpe": sharpe, "volatility": vol, "max_drawdown": max_dd}

    def process(self, text: str) -> ArbitrageDetectorResult:
        """Analyze a text/transaction payload deterministically."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        text = text.strip()
        if not text:
            raise ValueError("text must not be empty")

        tokens = [token for token in text.split() if token]
        keyword_set = {token.lower().strip(".,:;()[]{}") for token in tokens}
        risk = 0.0
        recommendations: List[str] = []
        if keyword_set & {"risk", "fraud", "scam", "suspicious"}:
            risk += 0.35
            recommendations.append("Review transaction counterparties and pricing before acting.")
        if keyword_set & {"arbitrage", "spread", "price", "exchange"}:
            recommendations.append("Compare executable prices, fees, slippage, and settlement latency across venues.")
        if not recommendations:
            recommendations.append("Provide structured venue prices or transfer data for arbitrage analysis.")

        result = ArbitrageDetectorResult(
            result_id=str(uuid.uuid4()),
            analysis={"status": "processed", "token_count": len(tokens), "input_hash": self._hash_transaction(text)},
            recommendations=recommendations,
            risk_score=min(1.0, max(0.0, risk)),
        )
        self.results.append(result)
        self._save_state()
        return result

    def _save_state(self) -> None:
        payload = {"version": 1, "results": [{"result_id": r.result_id, "analysis": r.analysis, "recommendations": r.recommendations, "risk_score": r.risk_score} for r in self.results]}
        fd, temporary = tempfile.mkstemp(prefix=".arbitrage.", dir=self.data_dir, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._state_file)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            with self._state_file.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
            if state.get("version") != 1:
                return
            self.results = [ArbitrageDetectorResult(
                result_id=str(item["result_id"]),
                analysis=dict(item.get("analysis", {})),
                recommendations=[str(v) for v in item.get("recommendations", [])],
                risk_score=min(1.0, max(0.0, float(item["risk_score"]))),
            ) for item in state.get("results", [])]
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring invalid arbitrage detector state: %s", exc)


_arbitrage_detector: Optional[ArbitrageDetectorSystem] = None


def get_arbitrage_detector() -> Optional[ArbitrageDetectorSystem]:
    return _arbitrage_detector


def initialize_arbitrage_detector(data_dir) -> ArbitrageDetectorSystem:
    global _arbitrage_detector
    _arbitrage_detector = ArbitrageDetectorSystem(data_dir)
    return _arbitrage_detector
