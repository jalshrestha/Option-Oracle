"""
Alpaca Market Data Client
Real-time and historical market data integration
"""
import asyncio
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
import time
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
import yfinance as yf

from config.settings import settings
from config.logging import get_data_logger

logger = get_data_logger()


class AlpacaMarketDataClient:
    """Real-time market data client using Alpaca API with yfinance fallback"""
    
    def __init__(self):
        self.alpaca_data_client = None
        self.alpaca_trading_client = None
        if settings.alpaca_api_key and settings.alpaca_secret_key:
            try:
                self.alpaca_data_client = StockHistoricalDataClient(
                    api_key=settings.alpaca_api_key,
                    secret_key=settings.alpaca_secret_key
                )
                self.alpaca_trading_client = TradingClient(
                    api_key=settings.alpaca_api_key,
                    secret_key=settings.alpaca_secret_key,
                    paper=True  # Using paper trading
                )
                logger.info("Alpaca market data client initialized")
            except Exception as e:
                logger.warning(f"Alpaca client init failed: {e} — falling back to yfinance only")
        else:
            logger.warning("Alpaca API keys not configured — using yfinance fallback only")
        # Cache: symbol -> (yf.Ticker, created_at_timestamp)
        self._ticker_cache: Dict[str, tuple] = {}
        self._ticker_cache_ttl = 300  # 5 minutes

    async def _get_ticker(self, symbol: str) -> "yf.Ticker":
        """Return a cached yfinance Ticker, refreshing after TTL expires."""
        entry = self._ticker_cache.get(symbol)
        if entry and (time.monotonic() - entry[1]) < self._ticker_cache_ttl:
            return entry[0]
        ticker = await asyncio.to_thread(yf.Ticker, symbol)
        self._ticker_cache[symbol] = (ticker, time.monotonic())
        return ticker
    
    async def get_current_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for symbol"""
        symbol = symbol.upper()
        try:
            # Try Alpaca first for price data
            if not self.alpaca_data_client:
                raise ValueError("Alpaca not configured")
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.alpaca_data_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                
                # Get all data from yfinance first, then supplement with Alpaca bid/ask if good
                try:
                    ticker = await self._get_ticker(symbol)
                    info = await asyncio.to_thread(lambda: ticker.info) or {}
                    volume = int(info.get('volume', 0))
                    yf_price = float(info.get('currentPrice', info.get('regularMarketPrice', 0)))
                    previous_close = float(info.get('previousClose', info.get('regularMarketPreviousClose', yf_price)))
                    yf_change = float(info.get('regularMarketChange', 0))
                    yf_change_percent = float(info.get('regularMarketChangePercent', 0))
                    company_name = info.get('longName', info.get('shortName', f"{symbol} Inc"))
                except:
                    yf_price = 0
                    volume = 0
                    previous_close = 0
                    yf_change = 0
                    yf_change_percent = 0
                    company_name = f"{symbol} Inc"
                
                # Calculate Alpaca mid-price from bid/ask
                alpaca_price = float(quote.ask_price + quote.bid_price) / 2
                
                # Use yfinance price if it's reasonable, otherwise try Alpaca price
                if yf_price > 0.01 and yf_price < 100000:
                    last_price = yf_price
                elif alpaca_price > 0.01 and alpaca_price < 100000:
                    last_price = alpaca_price
                else:
                    logger.warning(f"No good price found for {symbol} - using yfinance fallback")
                    raise Exception("Price validation failed")
                
                return {
                    'symbol': symbol,
                    'price': last_price,
                    'previous_close': previous_close,
                    'change': yf_change,
                    'change_percent': yf_change_percent,
                    'company_name': company_name,
                    'bid': float(quote.bid_price),
                    'ask': float(quote.ask_price),
                    'volume': volume,  # Real volume from yfinance
                    'timestamp': quote.timestamp.isoformat(),
                    'source': 'alpaca_price_yfinance_volume'
                }
                
        except Exception as e:
            logger.warning(f"Alpaca quote failed for {symbol}: {e}")
        
        # Fallback to yfinance for everything
        try:
            ticker = await self._get_ticker(symbol)
            info = await asyncio.to_thread(lambda: ticker.info) or {}
            
            # Get change data from yfinance
            current_price = float(info.get('currentPrice', info.get('regularMarketPrice', 0)))
            previous_close = float(info.get('previousClose', info.get('regularMarketPreviousClose', current_price)))
            change = float(info.get('regularMarketChange', current_price - previous_close))
            change_percent = float(info.get('regularMarketChangePercent', 0))
            
            return {
                'symbol': symbol,
                'price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'company_name': info.get('longName', info.get('shortName', f"{symbol} Inc")),
                'bid': float(info.get('bid', 0)),
                'ask': float(info.get('ask', 0)),
                'volume': int(info.get('volume', 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return self._get_fallback_quote(symbol)
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical price data"""
        
        try:
            # Map periods to Alpaca timeframes
            timeframe_map = {
                "1d": TimeFrame.Day,
                "1h": TimeFrame.Hour,
                "15m": TimeFrame.Minute,
                "5m": TimeFrame.Minute
            }
            
            timeframe = timeframe_map.get(interval, TimeFrame.Day)
            
            # Calculate start/end dates
            if period == "1y":
                start_date = datetime.now() - timedelta(days=365)
            elif period == "6mo":
                start_date = datetime.now() - timedelta(days=180)
            elif period == "3mo":
                start_date = datetime.now() - timedelta(days=90)
            elif period == "1mo":
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Try Alpaca first
            if not self.alpaca_data_client:
                raise ValueError("Alpaca not configured")
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start_date,
                end=datetime.now()
            )
            
            bars = self.alpaca_data_client.get_stock_bars(request)
            
            if symbol in bars.df.index.get_level_values('symbol'):
                df = bars.df[bars.df.index.get_level_values('symbol') == symbol]
                df.index = df.index.droplevel('symbol')
                return df
                
        except Exception as e:
            logger.warning(f"Alpaca historical data failed for {symbol}: {e}")
        
        # Fallback to yfinance
        try:
            ticker = await self._get_ticker(symbol)
            df = await asyncio.to_thread(ticker.history, period=period, interval=interval)
            logger.info(f"Retrieved {len(df)} bars for {symbol} via yfinance")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators using professional stock-indicators library"""
        
        try:
            # Get historical data
            df = await self.get_historical_data(symbol, period="1y", interval="1d")  # More data for better indicators
            
            if df.empty:
                return self._get_fallback_indicators(symbol)
            
            # Use professional indicators calculator
            from src.indicators.technical_calculator import technical_calculator
            indicators = technical_calculator.calculate_comprehensive_indicators(df, symbol)
            if (
                str(indicators.get('source', '')).lower() == 'unavailable'
                or indicators.get('data_points') == 0
                or indicators.get('current_price') is None
            ):
                logger.warning(
                    f"Professional indicators unavailable for {symbol}; using basic candle indicators"
                )
                return await self._get_basic_indicators(symbol)
            
            logger.info(f"Professional technical indicators calculated for {symbol}: {indicators.get('data_points', 0)} bars")
            return indicators
            
        except Exception as e:
            logger.error(f"Professional technical indicators calculation failed for {symbol}: {e}")
            # Try basic calculation as fallback
            try:
                return await self._get_basic_indicators(symbol)
            except:
                return self._get_fallback_indicators(symbol)
    
    async def _get_basic_indicators(self, symbol: str) -> Dict[str, Any]:
        """Fallback to basic indicator calculation"""
        
        try:
            df = await self.get_historical_data(symbol, period="3mo", interval="1d")
            if df.empty:
                return self._get_fallback_indicators(symbol)

            close = df['Close'] if 'Close' in df.columns else df['close']
            high = df['High'] if 'High' in df.columns else df['high']
            low = df['Low'] if 'Low' in df.columns else df['low']
            volume_series = (
                df['Volume'] if 'Volume' in df.columns
                else df['volume'] if 'volume' in df.columns
                else pd.Series([None] * len(df), index=df.index)
            )
            returns = close.pct_change().dropna()
            delta = close.diff()
            gains = delta.clip(lower=0).rolling(14).mean()
            losses = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gains / losses.replace(0, pd.NA)
            rsi_series = 100 - (100 / (1 + rs))
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_series = ema12 - ema26
            macd_signal = macd_series.ewm(span=9, adjust=False).mean()
            typical_price = (high + low + close) / 3
            volume_for_vwap = volume_series.fillna(0)
            vwap = (
                (typical_price * volume_for_vwap).cumsum() / volume_for_vwap.cumsum().replace(0, pd.NA)
            ).iloc[-1]
            current_volume = volume_series.iloc[-1] if pd.notna(volume_series.iloc[-1]) else None
            avg_volume = volume_series.rolling(20).mean().iloc[-1] if len(volume_series) >= 20 else None
            
            # Basic calculations only
            indicators = {
                'current_price': float(close.iloc[-1]),
                'change_percent': ((float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2])) * 100 if len(df) > 1 else 0.0,
                'volume': int(current_volume) if current_volume is not None else None,
                'current_volume': int(current_volume) if current_volume is not None else None,
                'avg_volume': float(avg_volume) if avg_volume is not None and pd.notna(avg_volume) else None,
                'volume_ratio': float(current_volume / avg_volume) if current_volume and avg_volume and pd.notna(avg_volume) else None,
                'ma5': float(close.rolling(5).mean().iloc[-1]) if len(df) >= 5 else float(close.iloc[-1]),
                'ma20': float(close.rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(close.iloc[-1]),
                'ma50': float(close.rolling(50).mean().iloc[-1]) if len(df) >= 50 else float(close.iloc[-1]),
                'ma200': float(close.rolling(200).mean().iloc[-1]) if len(df) >= 200 else float(close.iloc[-1]),
                'resistance': float(high.rolling(20).max().iloc[-1]) if len(df) >= 20 else float(high.iloc[-1]),
                'support': float(low.rolling(20).min().iloc[-1]) if len(df) >= 20 else float(low.iloc[-1]),
                'source': 'basic_candle_indicators',
                'volatility': float(returns.std() * (252 ** 0.5) * 100) if len(returns) > 1 else None,
                'rsi': float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else None,
                'macd': float(macd_series.iloc[-1]) if pd.notna(macd_series.iloc[-1]) else None,
                'macd_signal': float(macd_signal.iloc[-1]) if pd.notna(macd_signal.iloc[-1]) else None,
                'macd_histogram': float(macd_series.iloc[-1] - macd_signal.iloc[-1]) if pd.notna(macd_series.iloc[-1]) and pd.notna(macd_signal.iloc[-1]) else None,
                'vwap': float(vwap) if pd.notna(vwap) else float(close.iloc[-1]),
                'data_points': len(df),
                'data_quality': {
                    'source_status': 'limited',
                    'source': 'basic_candle_indicators',
                    'confidence_cap': 0.55,
                    'is_fallback': False,
                    'warnings': ['Professional indicator library unavailable; using basic candle calculations'],
                },
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Basic indicators calculation failed: {e}")
            return self._get_fallback_indicators(symbol)
    
    async def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Get options chain data (using yfinance)"""
        
        try:
            ticker = await self._get_ticker(symbol)

            # Get options expiration dates (blocking network call)
            expiration_dates = await asyncio.to_thread(lambda: ticker.options)

            if not expiration_dates:
                return {
                    'symbol': symbol,
                    'options_chain': [],
                    'total_options': 0,
                    'put_call_ratio': None,
                    'total_call_volume': 0,
                    'total_put_volume': 0,
                    'expirations': [],
                    'source': 'yfinance_options_unavailable',
                    'last_updated': datetime.now().isoformat(),
                    'data_quality': {
                        'source_status': 'unavailable',
                        'source': 'yfinance_options',
                        'is_fallback': True,
                        'confidence_cap': 0.0,
                        'warnings': ['No listed options expirations returned by provider'],
                    },
                    'error': 'No options data available',
                }

            # Get current stock price (reuse cached info)
            info = await asyncio.to_thread(lambda: ticker.info) or {}
            current_price = float(info.get('currentPrice', 100))
            
            # Process multiple expirations (up to 3)
            all_options = []
            summary_data = {
                'total_call_volume': 0,
                'total_put_volume': 0,
                'expirations_processed': []
            }
            
            for exp_date in expiration_dates[:3]:  # Process first 3 expirations
                try:
                    options_chain = await asyncio.to_thread(ticker.option_chain, exp_date)
                    calls_df = options_chain.calls
                    puts_df = options_chain.puts
                    
                    def _opt_row_to_dict(row: dict, opt_type: str, suffix: str) -> dict:
                        return {
                            'symbol': f"{symbol}_{exp_date}_{suffix}{row['strike']}",
                            'underlying_symbol': symbol,
                            'strike_price': float(row['strike']),
                            'option_type': opt_type,
                            'expiration_date': exp_date,
                            'last_price': float(row.get('lastPrice', 0)),
                            'bid': float(row.get('bid', 0)),
                            'ask': float(row.get('ask', 0)),
                            'volume': int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                            'open_interest': int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest')) else 0,
                            'implied_volatility': float(row.get('impliedVolatility', 0.25)),
                            'in_the_money': row.get('inTheMoney', False),
                        }

                    all_options.extend(
                        _opt_row_to_dict(r, 'call', 'C') for r in calls_df.to_dict('records')
                    )
                    all_options.extend(
                        _opt_row_to_dict(r, 'put', 'P') for r in puts_df.to_dict('records')
                    )
                    
                    # Update summary
                    call_volume = calls_df['volume'].fillna(0).sum()
                    put_volume = puts_df['volume'].fillna(0).sum()
                    summary_data['total_call_volume'] += int(call_volume)
                    summary_data['total_put_volume'] += int(put_volume)
                    summary_data['expirations_processed'].append(exp_date)
                    
                except Exception as e:
                    logger.warning(f"Failed to process expiration {exp_date} for {symbol}: {e}")
                    continue
            
            # Calculate put/call ratio
            put_call_ratio = (summary_data['total_put_volume'] / 
                            max(summary_data['total_call_volume'], 1))
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'options_chain': all_options,
                'total_options': len(all_options),
                'put_call_ratio': put_call_ratio,
                'total_call_volume': summary_data['total_call_volume'],
                'total_put_volume': summary_data['total_put_volume'],
                'expirations': summary_data['expirations_processed'],
                'source': 'yfinance_real_options',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Options data retrieval failed for {symbol}: {e}")
            return self._get_fallback_options_data(symbol)
    
    def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Unavailable quote payload when all APIs fail."""
        return {
            'symbol': symbol,
            'price': None,
            'previous_close': None,
            'change': None,
            'change_percent': None,
            'company_name': symbol,
            'bid': None,
            'ask': None,
            'volume': None,
            'timestamp': datetime.now().isoformat(),
            'source': 'unavailable',
            'data_quality': {
                'source_status': 'unavailable',
                'source': 'market_data_provider',
                'is_fallback': True,
                'confidence_cap': 0.0,
                'warnings': ['No valid quote returned by Alpaca or yfinance'],
            },
            'error': 'Quote unavailable',
        }
    
    def _get_fallback_indicators(self, symbol: str) -> Dict[str, Any]:
        """Unavailable technical indicator payload when calculation fails."""
        return {
            'symbol': symbol,
            'current_price': None,
            'change_percent': None,
            'ma5': None,
            'ma20': None,
            'ma50': None,
            'ma200': None,
            'rsi': None,
            'macd': None,
            'macd_signal': None,
            'macd_histogram': None,
            'bb_upper': None,
            'bb_middle': None,
            'bb_lower': None,
            'bb_position': None,
            'vwap': None,
            'volatility': None,
            'avg_volume': None,
            'current_volume': None,
            'volume_ratio': None,
            'resistance': None,
            'support': None,
            'source': 'unavailable',
            'data_quality': {
                'source_status': 'unavailable',
                'source': 'historical_price_provider',
                'is_fallback': True,
                'confidence_cap': 0.0,
                'warnings': ['Historical candles unavailable; technical indicators not calculated'],
            },
            'error': 'Technical indicators unavailable',
        }
    
    def _get_fallback_options_data(self, symbol: str) -> Dict[str, Any]:
        """Unavailable options payload when APIs fail."""
        return {
            'symbol': symbol,
            'expiration': None,
            'current_price': None,
            'put_call_ratio': None,
            'total_call_volume': 0,
            'total_put_volume': 0,
            'call_count': 0,
            'put_count': 0,
            'atm_calls': [],
            'atm_puts': [],
            'options_chain': [],
            'total_options': 0,
            'expirations': [],
            'source': 'unavailable',
            'last_updated': datetime.now().isoformat(),
            'data_quality': {
                'source_status': 'unavailable',
                'source': 'options_provider',
                'is_fallback': True,
                'confidence_cap': 0.0,
                'warnings': ['Options chain unavailable'],
            },
            'error': 'Options data unavailable',
        }
