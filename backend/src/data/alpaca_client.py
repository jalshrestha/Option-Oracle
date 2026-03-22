"""
Alpaca Market Data Client
Real-time and historical market data integration
"""
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models import Bar, Quote, Trade
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
import yfinance as yf

from config.settings import settings
from config.logging import get_data_logger

logger = get_data_logger()


class AlpacaMarketDataClient:
    """Real-time market data client using Alpaca API with yfinance fallback"""
    
    def __init__(self):
        self.alpaca_data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )
        self.alpaca_trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=True  # Using paper trading
        )
        # Cache: symbol -> (yf.Ticker, created_at_timestamp)
        self._ticker_cache: Dict[str, tuple] = {}
        self._ticker_cache_ttl = 300  # 5 minutes

        logger.info("Alpaca market data client initialized")

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
        try:
            # Try Alpaca first for price data
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.alpaca_data_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                
                # Get all data from yfinance first, then supplement with Alpaca bid/ask if good
                try:
                    ticker = await self._get_ticker(symbol)
                    info = await asyncio.to_thread(lambda: ticker.info)
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
            info = await asyncio.to_thread(lambda: ticker.info)
            
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
            
            # Basic calculations only
            indicators = {
                'current_price': float(df['Close'].iloc[-1]),
                'change_percent': ((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-2])) / float(df['Close'].iloc[-2])) * 100 if len(df) > 1 else 0.0,
                'volume': int(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 1000000,
                'ma20': float(df['Close'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Close'].iloc[-1]),
                'ma50': float(df['Close'].rolling(50).mean().iloc[-1]) if len(df) >= 50 else float(df['Close'].iloc[-1]),
                'resistance': float(df['High'].rolling(20).max().iloc[-1]) if len(df) >= 20 else float(df['High'].iloc[-1]),
                'support': float(df['Low'].rolling(20).min().iloc[-1]) if len(df) >= 20 else float(df['Low'].iloc[-1]),
                'source': 'basic_fallback',
                'volatility': 25.0,
                'rsi': 50.0,
                'macd': 0.0,
                'vwap': float(df['Close'].iloc[-1])
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
                return {'error': 'No options data available'}

            # Get current stock price (reuse cached info)
            info = await asyncio.to_thread(lambda: ticker.info)
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
        """Fallback quote when all APIs fail"""
        return {
            'symbol': symbol,
            'price': 100.0,  # Default price
            'bid': 99.5,
            'ask': 100.5,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _get_fallback_indicators(self, symbol: str) -> Dict[str, Any]:
        """Fallback indicators when calculation fails"""
        base_price = 100.0
        
        return {
            'current_price': base_price,
            'change_percent': 0.0,
            'ma5': base_price,
            'ma20': base_price,
            'ma50': base_price,
            'ma200': base_price,
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'bb_upper': base_price + 5,
            'bb_middle': base_price,
            'bb_lower': base_price - 5,
            'bb_position': 0.5,
            'vwap': base_price,
            'volatility': 25.0,
            'avg_volume': 1000000,
            'current_volume': 1000000,
            'volume_ratio': 1.0,
            'resistance': base_price + 10,
            'support': base_price - 10,
            'source': 'fallback'
        }
    
    def _get_fallback_options_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback options data when APIs fail"""
        return {
            'symbol': symbol,
            'expiration': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'current_price': 100.0,
            'put_call_ratio': 1.0,
            'total_call_volume': 1000,
            'total_put_volume': 1000,
            'call_count': 20,
            'put_count': 20,
            'atm_calls': [],
            'atm_puts': [],
            'source': 'fallback'
        }