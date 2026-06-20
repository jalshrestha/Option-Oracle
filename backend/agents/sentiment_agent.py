"""
Sentiment Analysis Agent
OpenAI Agents SDK v0.3.0 Implementation - REAL DATA ONLY
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from config.logging import get_agents_logger
import asyncio
import json
import re
import requests
import yfinance as yf

logger = get_agents_logger()


class SentimentAnalysisAgent(BaseAgent):
    """AI agent specializing in market sentiment analysis using sourced public data."""
    
    def __init__(self, client):
        super().__init__(client, "Sentiment Analysis")
        
    def _get_system_instructions(self) -> str:
        return """
You are a market sentiment analyst for the Neural Options Oracle++ system.

Your responsibilities:
1. Analyze the provided sourced news and social sentiment data
2. Clearly separate StockTwits/social sentiment from news sentiment
3. Process market psychology indicators from provided market proxies
4. Provide sentiment-based trading insights without inventing missing data

Weight in system: 10% of final decision

OUTPUT FORMAT (JSON):
{
    "aggregate_score": float_between_-1_and_1,
    "confidence": float_between_0_and_1,
    "sources": {
        "news_sentiment": {"score": float, "article_count": int, "details": "string"},
        "stocktwits_sentiment": {"score": float, "message_count": int, "details": "string"},
        "market_psychology": {"score": float, "indicators": "string", "details": "string"}
    },
    "sentiment_trend": "improving|deteriorating|stable",
    "key_factors": ["string1", "string2"],
    "risk_factors": ["string1", "string2"],
    "data_freshness": "YYYY-MM-DD HH:MM:SS"
}
"""
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Get JSON Schema for sentiment analysis response"""
        return {
            "type": "object",
            "properties": {
                "aggregate_score": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "sources": {
                    "type": "object",
                    "properties": {
                        "news_sentiment": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "article_count": {"type": "integer", "minimum": 0},
                                "details": {"type": "string"}
                            },
                            "required": ["score", "article_count", "details"],
                            "additionalProperties": False
                        },
                        "stocktwits_sentiment": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "message_count": {"type": "integer", "minimum": 0},
                                "details": {"type": "string"}
                            },
                            "required": ["score", "message_count", "details"],
                            "additionalProperties": False
                        },
                        "market_psychology": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "indicators": {"type": "string"},
                                "details": {"type": "string"}
                            },
                            "required": ["score", "indicators", "details"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["news_sentiment", "stocktwits_sentiment", "market_psychology"],
                    "additionalProperties": False
                },
                "sentiment_trend": {
                    "type": "string",
                    "enum": ["improving", "deteriorating", "stable"]
                },
                "key_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5
                },
                "risk_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5
                },
                "data_freshness": {
                    "type": "string",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$"
                }
            },
            "required": ["aggregate_score", "confidence", "sources", "sentiment_trend", "key_factors", "risk_factors", "data_freshness"],
            "additionalProperties": False
        }
    
    async def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Analyze market sentiment for the symbol using sourced public data."""
        
        try:
            logger.info(f"Starting REAL sentiment analysis for {symbol}")
            
            if not self.client:
                logger.error("LLM client not available for sentiment analysis")
                return self._get_fallback_sentiment(symbol)
            
            # Get current date for search queries
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Collect real sentiment data from multiple sources
            sentiment_data = await self._collect_real_sentiment_data(symbol, current_date)
            
            # Analyze with GPT
            analysis = await self._analyze_sentiment_with_gpt(sentiment_data, symbol, current_date)
            if analysis.get("fallback") and self._source_quality(sentiment_data).get("usable_source_count", 0) > 0:
                logger.warning("Sentiment LLM response was not usable; using deterministic source-based sentiment")
                analysis = self._build_deterministic_sentiment(sentiment_data)
            
            analysis["_raw_sentiment_data"] = sentiment_data
            analysis = self._validate_sentiment_analysis(analysis, symbol)
            
            logger.info(f"REAL sentiment analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {symbol}: {e}")
            return self._get_fallback_sentiment(symbol)
    
    async def _collect_real_sentiment_data(self, symbol: str, current_date: str) -> Dict[str, Any]:
        """Collect sentiment data from concrete public sources."""
        try:
            tasks = [
                self._search_news_sentiment(symbol, current_date),
                self._search_stocktwits_sentiment(symbol, current_date),
                self._search_market_psychology(symbol, current_date)
            ]
            
            news_data, stocktwits_data, psychology_data = await asyncio.gather(*tasks, return_exceptions=True)
        
            return {
                'news_sentiment': news_data if not isinstance(news_data, Exception) else {},
                'stocktwits_sentiment': stocktwits_data if not isinstance(stocktwits_data, Exception) else {},
                'market_psychology': psychology_data if not isinstance(psychology_data, Exception) else {},
                'search_date': current_date,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error collecting real sentiment data for {symbol}: {e}")
            return {
                'news_sentiment': {},
                'stocktwits_sentiment': {},
                'market_psychology': {},
                'search_date': current_date,
                'symbol': symbol,
                'error': str(e)
            }
    
    async def _search_news_sentiment(self, symbol: str, current_date: str) -> Dict[str, Any]:
        """Fetch recent Yahoo Finance news via yfinance and score headline sentiment."""
        try:
            news_items = await asyncio.to_thread(lambda: yf.Ticker(symbol).news or [])
            parsed_items = []
            scores = []
            for item in news_items[:10]:
                content = item.get("content", item)
                title = content.get("title", "")
                summary = content.get("summary", "") or content.get("description", "")
                text = f"{title}. {summary}".strip()
                score = self._score_text_sentiment(text)
                scores.append(score)
                parsed_items.append({
                    "title": title,
                    "summary": summary[:240],
                    "provider": (content.get("provider") or {}).get("displayName"),
                    "published_at": content.get("pubDate") or content.get("displayTime"),
                    "url": (
                        (content.get("canonicalUrl") or {}).get("url")
                        or (content.get("clickThroughUrl") or {}).get("url")
                    ),
                    "sentiment_score": score,
                })

            score = sum(scores) / len(scores) if scores else 0.0
            return {
                "sentiment_score": score,
                "article_count": len(parsed_items),
                "positive_factors": self._extract_keyword_hits(parsed_items, positive=True),
                "negative_factors": self._extract_keyword_hits(parsed_items, positive=False),
                "analyst_sentiment": self._label_sentiment(score),
                "key_headlines": [item["title"] for item in parsed_items[:5] if item["title"]],
                "items": parsed_items,
                "source": "yfinance_news",
                "is_fallback": False,
            }
            
        except Exception as e:
            logger.error(f"Error searching news sentiment for {symbol}: {e}")
            return {"source": "yfinance_news", "is_fallback": True, "error": str(e)}
    
    async def _search_stocktwits_sentiment(self, symbol: str, current_date: str) -> Dict[str, Any]:
        """Fetch recent public StockTwits symbol stream and score labeled messages."""
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol.upper()}.json"
            def fetch_stocktwits():
                response = requests.get(
                    url,
                    params={"limit": 30},
                    headers={"User-Agent": "OptionOracle/1.0"},
                    timeout=8,
                )
                response.raise_for_status()
                return response.json()

            data = await asyncio.to_thread(fetch_stocktwits)
            messages = data.get("messages", [])
            parsed_messages = []
            bullish = 0
            bearish = 0
            unlabeled_scores = []

            for message in messages:
                body = self._clean_text(message.get("body", ""))
                sentiment = (message.get("entities") or {}).get("sentiment") or {}
                label = str(sentiment.get("basic", "")).lower()
                if label == "bullish":
                    bullish += 1
                    score = 1.0
                elif label == "bearish":
                    bearish += 1
                    score = -1.0
                else:
                    score = self._score_text_sentiment(body)
                    unlabeled_scores.append(score)
                parsed_messages.append({
                    "body": body[:240],
                    "sentiment": label or "unlabeled",
                    "created_at": message.get("created_at"),
                    "score": score,
                })

            labeled_count = bullish + bearish
            if labeled_count:
                score = (bullish - bearish) / labeled_count
            elif unlabeled_scores:
                score = sum(unlabeled_scores) / len(unlabeled_scores)
            else:
                score = 0.0

            total = len(messages) or 1
            return {
                "sentiment_score": score,
                "message_count": len(messages),
                "bullish_percentage": bullish / total * 100,
                "bearish_percentage": bearish / total * 100,
                "trending": len(messages) >= 20,
                "sample_messages": [item["body"] for item in parsed_messages[:5]],
                "messages": parsed_messages[:10],
                "source": "stocktwits_public_stream",
                "is_fallback": False,
            }
            
        except Exception as e:
            logger.error(f"Error searching StockTwits sentiment for {symbol}: {e}")
            return {"source": "stocktwits_public_stream", "is_fallback": True, "error": str(e)}
    
    async def _search_market_psychology(self, symbol: str, current_date: str) -> Dict[str, Any]:
        """Collect market psychology proxy data without pretending to browse."""
        try:
            vix = await asyncio.to_thread(lambda: yf.Ticker("^VIX").history(period="5d"))
            spy = await asyncio.to_thread(lambda: yf.Ticker("SPY").history(period="1mo"))
            vix_level = float(vix["Close"].iloc[-1]) if not vix.empty else 20.0
            vix_prev = float(vix["Close"].iloc[-2]) if len(vix) > 1 else vix_level
            spy_change = 0.0
            if not spy.empty and len(spy) > 1:
                spy_change = (float(spy["Close"].iloc[-1]) - float(spy["Close"].iloc[0])) / float(spy["Close"].iloc[0]) * 100

            market_sentiment = "fearful" if vix_level >= 25 else "greedy" if vix_level <= 15 and spy_change > 0 else "neutral"
            volatility_trend = "increasing" if vix_level > vix_prev else "decreasing" if vix_level < vix_prev else "stable"

            return {
                "vix_level": vix_level,
                "put_call_ratio": None,
                "fear_greed_index": None,
                "market_sentiment": market_sentiment,
                "institutional_flow": "unknown",
                "volatility_trend": volatility_trend,
                "spy_1m_change_percent": spy_change,
                "source": "yfinance_vix_spy_proxy",
                "is_fallback": False,
            }
        except Exception as e:
            logger.error(f"Error collecting market psychology for {symbol}: {e}")
            return {
                "vix_level": 20.0,
                "put_call_ratio": None,
                "fear_greed_index": None,
                "market_sentiment": "neutral",
                "institutional_flow": "unknown",
                "volatility_trend": "stable",
                "source": "fallback",
                "is_fallback": True,
                "error": str(e),
            }

    def _score_text_sentiment(self, text: str) -> float:
        """Small deterministic financial sentiment score for source text."""
        text_lower = text.lower()
        positive_terms = [
            "beat", "beats", "upgrade", "upgraded", "bullish", "surge", "rally",
            "growth", "record", "profit", "strong", "positive", "outperform",
            "raises", "raised", "buy rating", "demand", "delivery beat"
        ]
        negative_terms = [
            "miss", "misses", "downgrade", "downgraded", "bearish", "drop", "falls",
            "lawsuit", "probe", "recall", "weak", "negative", "underperform",
            "cuts", "cut rating", "slump", "concern", "risk"
        ]
        positive = sum(1 for term in positive_terms if term in text_lower)
        negative = sum(1 for term in negative_terms if term in text_lower)
        total = positive + negative
        if total == 0:
            return 0.0
        return max(-1.0, min(1.0, (positive - negative) / total))

    def _extract_keyword_hits(self, items: List[Dict[str, Any]], positive: bool) -> List[str]:
        terms = (
            ["beat", "upgrade", "bullish", "growth", "strong", "outperform", "demand"]
            if positive
            else ["miss", "downgrade", "bearish", "lawsuit", "recall", "weak", "risk"]
        )
        hits = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            for term in terms:
                if term in text and term not in hits:
                    hits.append(term)
            if len(hits) >= 5:
                break
        return hits

    def _label_sentiment(self, score: float) -> str:
        if score > 0.2:
            return "positive"
        if score < -0.2:
            return "negative"
        return "neutral"

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _source_quality(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        news = sentiment_data.get("news_sentiment", {})
        stocktwits = sentiment_data.get("stocktwits_sentiment", {})
        psychology = sentiment_data.get("market_psychology", {})
        usable_sources = [
            source for source in [news, stocktwits, psychology]
            if source and not source.get("is_fallback")
        ]
        if len(usable_sources) >= 2:
            status = "partial" if len(usable_sources) < 3 else "live"
            confidence_cap = 0.75 if status == "live" else 0.55
        elif usable_sources:
            status = "limited"
            confidence_cap = 0.4
        else:
            status = "fallback"
            confidence_cap = 0.2
        return {
            "source_status": status,
            "usable_source_count": len(usable_sources),
            "confidence_cap": confidence_cap,
            "is_fallback": len(usable_sources) == 0,
            "sources": [source.get("source") for source in usable_sources],
        }

    def _build_deterministic_sentiment(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build sentiment directly from collected real sources when LLM formatting fails."""
        news = sentiment_data.get("news_sentiment", {})
        stocktwits = sentiment_data.get("stocktwits_sentiment", {})
        psychology = sentiment_data.get("market_psychology", {})

        components = []
        if news and not news.get("is_fallback"):
            components.append(("news", float(news.get("sentiment_score") or 0.0), 0.4))
        if stocktwits and not stocktwits.get("is_fallback"):
            components.append(("stocktwits", float(stocktwits.get("sentiment_score") or 0.0), 0.35))
        if psychology and not psychology.get("is_fallback"):
            vix_level = psychology.get("vix_level")
            spy_change = psychology.get("spy_1m_change_percent") or 0.0
            try:
                vix_score = -0.35 if float(vix_level) >= 25 else 0.2 if float(vix_level) <= 15 else 0.0
            except (TypeError, ValueError):
                vix_score = 0.0
            psychology_score = max(-1.0, min(1.0, vix_score + float(spy_change) / 50))
            components.append(("market_psychology", psychology_score, 0.25))

        if components:
            total_weight = sum(weight for _, _, weight in components)
            aggregate_score = sum(score * weight for _, score, weight in components) / total_weight
        else:
            aggregate_score = 0.0

        trend = "improving" if aggregate_score > 0.15 else "deteriorating" if aggregate_score < -0.15 else "stable"
        source_names = [name for name, _, _ in components]
        return {
            "aggregate_score": aggregate_score,
            "confidence": min(0.55, 0.2 + 0.12 * len(components)),
            "sources": {
                "news_sentiment": {
                    "score": float(news.get("sentiment_score") or 0.0),
                    "article_count": int(news.get("article_count") or 0),
                    "details": "Yahoo Finance news headline scoring" if news and not news.get("is_fallback") else "News unavailable",
                },
                "stocktwits_sentiment": {
                    "score": float(stocktwits.get("sentiment_score") or 0.0),
                    "message_count": int(stocktwits.get("message_count") or 0),
                    "details": "Public StockTwits stream scoring" if stocktwits and not stocktwits.get("is_fallback") else "StockTwits unavailable",
                },
                "market_psychology": {
                    "score": next((score for name, score, _ in components if name == "market_psychology"), 0.0),
                    "indicators": "VIX and SPY proxy",
                    "details": "Computed from yfinance VIX/SPY proxy" if psychology and not psychology.get("is_fallback") else "Market psychology unavailable",
                },
            },
            "sentiment_trend": trend,
            "key_factors": [f"Used {', '.join(source_names)} real sentiment sources"] if source_names else ["No real sentiment sources available"],
            "risk_factors": ["LLM sentiment formatter failed; deterministic source scoring used"],
            "data_freshness": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    async def _analyze_sentiment_with_gpt(self, sentiment_data: Dict[str, Any], symbol: str, current_date: str) -> Dict[str, Any]:
        """Analyze collected sentiment data with GPT"""
        try:
            # Prepare comprehensive sentiment analysis prompt
            prompt = f"""
            Analyze the collected sentiment data for {symbol} on {current_date}.
            Use only the data below. If a field is missing or fallback, say the source is limited and keep confidence low.
            
            NEWS SENTIMENT DATA:
            {json.dumps(sentiment_data.get('news_sentiment', {}), indent=2)}
            
            STOCKTWITS SENTIMENT DATA:
            {json.dumps(sentiment_data.get('stocktwits_sentiment', {}), indent=2)}
            
            MARKET PSYCHOLOGY DATA:
            {json.dumps(sentiment_data.get('market_psychology', {}), indent=2)}
            
            Based on this sourced data, provide:
            1. Overall aggregate sentiment score (-1 to 1)
            2. Confidence level (0 to 1)
            3. Sentiment trend analysis
            4. Key factors driving sentiment
            5. Risk factors to consider
            
            Return in the exact JSON format specified in the system instructions.
            """
            
            content = await self.client.complete(
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.2,
                json_mode=True,
            )
            return self._parse_json_response(content)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with GPT for {symbol}: {e}")
            return self._get_fallback_response()
    
    def _validate_sentiment_analysis(self, analysis: Dict, symbol: str) -> Dict:
        """Validate sentiment analysis"""
        
        if 'aggregate_score' not in analysis:
            analysis['aggregate_score'] = 0.0
        if 'confidence' not in analysis:
            analysis['confidence'] = 0.5
            
        analysis['aggregate_score'] = max(-1.0, min(1.0, analysis['aggregate_score']))
        model_fallback = bool(analysis.get("fallback"))
        quality = self._source_quality(analysis.pop("_raw_sentiment_data", {}))
        is_fallback = quality["is_fallback"] or model_fallback
        analysis['confidence'] = min(max(0.0, min(1.0, analysis['confidence'])), quality["confidence_cap"])
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['symbol'] = symbol
        analysis['agent'] = self.name
        analysis['data_freshness'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        analysis['data_quality'] = quality
        analysis['source'] = ",".join(quality.get("sources", [])) or "fallback"
        analysis['is_fallback'] = is_fallback
        analysis['fallback'] = is_fallback
        
        return analysis
    
    def _get_fallback_sentiment(self, symbol: str) -> Dict:
        """Fallback sentiment analysis when real data unavailable"""
        return {
            'aggregate_score': 0.0,
            'confidence': 0.2,
            'sources': {
                'news_sentiment': {'score': 0.0, 'article_count': 0, 'details': 'Real-time news data unavailable'},
                'stocktwits_sentiment': {'score': 0.0, 'message_count': 0, 'details': 'StockTwits data unavailable'},
                'market_psychology': {'score': 0.0, 'indicators': 'unavailable', 'details': 'Market psychology data unavailable'}
            },
            'sentiment_trend': 'stable',
            'key_factors': ['Real-time sentiment data unavailable'],
            'risk_factors': ['Limited real-time data'],
            'error': 'Fallback sentiment analysis - real data unavailable',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'agent': self.name,
            'data_freshness': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_quality': {
                'source_status': 'fallback',
                'usable_source_count': 0,
                'confidence_cap': 0.2,
                'is_fallback': True,
                'sources': [],
            },
            'source': 'fallback',
            'is_fallback': True,
        }
