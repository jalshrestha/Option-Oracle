"""
AI-Powered Intent Router with Tool Calling
Uses OpenAI's tool calling to intelligently route and process user requests
"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from config.logging import get_api_logger
from langgraph.graph import StateGraph, END

from src.llm.base import ToolCallResult
from src.llm.factory import create_llm_client

logger = get_api_logger()


class ChatGraphState(TypedDict, total=False):
    """Shared state passed between LangGraph chat orchestration nodes."""
    user_message: str
    context: Dict[str, Any]
    llm_result: ToolCallResult
    tool_results: List[Dict[str, Any]]
    response: str
    intent: str
    tools_called: List[str]
    confidence: float
    formatted: bool
    timestamp: str
    symbol: str
    error: bool


class AIIntentRouter:
    """LangGraph-powered chat orchestrator with LLM tool routing."""
    
    def __init__(self):
        self.client = create_llm_client("large")
        self.routing_client = create_llm_client("small")
        
        # Define available tools/functions
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_quote",
                    "description": "Get the latest available market quote/current price for a ticker. Use this for price, quote, current price, or 'what is SYMBOL trading at' requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Stock or ETF symbol to quote (e.g., AAPL, TSLA, SPY)"
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_stock",
                    "description": "Perform comprehensive stock analysis including technical, sentiment, and options flow",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Stock symbol to analyze (e.g., AAPL, TSLA)"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["full", "technical", "sentiment", "options", "risk"],
                                "description": "Type of analysis to perform"
                            },
                            "time_horizon": {
                                "type": "string",
                                "enum": ["short", "medium", "long"],
                                "description": "Investment time horizon"
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explain_concept",
                    "description": "Explain trading or options concepts in educational format",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "description": "Trading concept to explain (e.g., delta, put options, call options)"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Explanation difficulty level"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context for the explanation"
                            }
                        },
                        "required": ["concept"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_market_trends",
                    "description": "Get trending stocks and market overview",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sector": {
                                "type": "string",
                                "description": "Specific sector to focus on (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of trending stocks to return",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "portfolio_analysis",
                    "description": "Analyze user's portfolio performance and positions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["performance", "risk", "rebalancing", "summary"],
                                "description": "Type of portfolio analysis"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_quiz",
                    "description": "Create educational quizzes on trading topics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Quiz topic (e.g., options_basics, technical_analysis)"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Quiz difficulty level"
                            },
                            "question_count": {
                                "type": "integer",
                                "description": "Number of questions to generate",
                                "default": 5
                            }
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "casual_response",
                    "description": "Generate friendly response for casual conversation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The casual message to respond to"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the conversation"
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buy_option",
                    "description": "Analyze and buy a single option for a specific stock",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Stock symbol to buy options for (e.g., AAPL, TSLA)"
                            },
                            "budget": {
                                "type": "number",
                                "description": "Budget available for option purchase (default: 500 if not specified)"
                            },
                            "risk_tolerance": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "description": "User's risk tolerance level"
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buy_multiple_options",
                    "description": "Analyze hot stocks and create optimized options portfolio within budget",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "budget": {
                                "type": "number",
                                "description": "Total budget for options portfolio"
                            },
                            "risk_tolerance": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "description": "User's risk tolerance level"
                            },
                            "diversification": {
                                "type": "string",
                                "enum": ["low", "moderate", "high"],
                                "description": "Desired diversification level"
                            }
                        },
                        "required": ["budget"]
                    }
                }
            }
        ]

        self.graph = self._build_graph()
        logger.info("LangGraph chat orchestrator initialized with tool calling capabilities")

    def _build_graph(self):
        """Build the LangGraph workflow for route -> tools -> writer."""
        graph = StateGraph(ChatGraphState)
        graph.add_node("route", self._route_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("write_response", self._write_response_node)
        graph.add_node("direct_response", self._direct_response_node)
        graph.set_entry_point("route")
        graph.add_conditional_edges(
            "route",
            self._route_next_node,
            {
                "execute_tools": "execute_tools",
                "direct_response": "direct_response",
            },
        )
        graph.add_edge("execute_tools", "write_response")
        graph.add_edge("write_response", END)
        graph.add_edge("direct_response", END)
        return graph.compile()
    
    async def route_and_process(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use LangGraph to determine intent, call tools, and format a response.
        Returns formatted response ready for user display
        """
        try:
            result = await self.graph.ainvoke({
                "user_message": user_message,
                "context": context or {},
            })
            return self._shape_route_result(result)
        except Exception as e:
            logger.error(f"LangGraph chat orchestration failed: {e}")
            return await self._fallback_response(user_message)

    async def route_and_process_events(self, user_message: str, context: Dict[str, Any] = None):
        """Yield actual routing/tool/writer progress events for chat streaming."""
        context = context or {}
        try:
            base_state: ChatGraphState = {"user_message": user_message, "context": context}
            yield {
                "event": "progress",
                "stage": "routing",
                "label": "Reading request",
                "detail": "Classifying intent and selecting the right tool path.",
            }

            route_state = await self._route_node(base_state)
            state: ChatGraphState = {**base_state, **route_state}
            llm_result = state.get("llm_result")

            if not llm_result or not llm_result.tool_calls:
                yield {
                    "event": "progress",
                    "stage": "direct_response",
                    "label": "Writing answer",
                    "detail": "No market tool was needed for this response.",
                }
                final_state = await self._direct_response_node(state)
                yield {"event": "final", "data": self._shape_route_result({**state, **final_state})}
                return

            tool_names = [tool_call.name for tool_call in llm_result.tool_calls]
            yield {
                "event": "progress",
                "stage": "tools_selected",
                "label": "Planning tools",
                "detail": f"Selected: {', '.join(name.replace('_', ' ') for name in tool_names)}.",
                "tools": tool_names,
            }

            tool_results = []
            for tool_call in llm_result.tool_calls:
                normalized_args = self._normalize_tool_arguments(tool_call.name, tool_call.arguments, state)
                label, detail = self._tool_progress_text(tool_call.name, normalized_args)
                yield {
                    "event": "progress",
                    "stage": "tool_start",
                    "tool": tool_call.name,
                    "label": label,
                    "detail": detail,
                    "symbol": normalized_args.get("symbol"),
                }
                tool_result = await self._execute_tool_call(tool_call, state)
                tool_results.append(tool_result)
                status = "complete" if tool_result.get("success") else "failed"
                yield {
                    "event": "progress",
                    "stage": "tool_complete",
                    "tool": tool_call.name,
                    "label": f"{label} {status}",
                    "detail": self._tool_complete_detail(tool_call.name, tool_result),
                    "symbol": tool_result.get("symbol"),
                    "success": tool_result.get("success", False),
                }

            symbol = None
            for result in tool_results:
                if result.get("symbol"):
                    symbol = result["symbol"]
                    break

            state = {
                **state,
                "tool_results": tool_results,
                "tools_called": tool_names,
                "intent": self._determine_intent_from_tools(llm_result.tool_calls),
                "confidence": 0.9,
                **({"symbol": symbol} if symbol else {}),
            }
            yield {
                "event": "progress",
                "stage": "write_response",
                "label": "Writing answer",
                "detail": "Summarizing returned tool data, sources, risks, and next action.",
                "symbol": symbol,
            }
            write_state = await self._write_response_node(state)
            yield {"event": "final", "data": self._shape_route_result({**state, **write_state})}
        except Exception as e:
            logger.error(f"Streaming chat orchestration failed: {e}")
            yield {"event": "error", "data": await self._fallback_response(user_message)}

    def _shape_route_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": result.get("response", ""),
            "intent": result.get("intent", "GENERAL_CHAT"),
            "tools_called": result.get("tools_called", []),
            "tool_results": result.get("tool_results", []),
            "confidence": result.get("confidence", 0.7),
            "formatted": result.get("formatted", True),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            **({"symbol": result["symbol"]} if result.get("symbol") else {}),
            **({"error": True} if result.get("error") else {}),
        }

    def _tool_progress_text(self, tool_name: str, args: Dict[str, Any]) -> tuple[str, str]:
        symbol = args.get("symbol")
        if tool_name == "get_quote":
            return "Fetching quote", f"Checking latest available price for {symbol or 'the symbol'}."
        if tool_name == "analyze_stock":
            return "Running analysis agents", (
                f"Running technical, sentiment, options flow, history, risk, and education agents for {symbol or 'the symbol'}."
            )
        if tool_name == "get_market_trends":
            return "Scanning market watchlist", "Fetching quote-backed movers for the selected watchlist."
        if tool_name == "portfolio_analysis":
            return "Checking portfolio context", "Reading positions available to the current chat session."
        if tool_name == "buy_option":
            return "Checking option trade", f"Evaluating budget, risk, and option candidates for {symbol or 'the symbol'}."
        if tool_name == "buy_multiple_options":
            return "Building option shortlist", "Ranking option candidates within the requested budget."
        if tool_name == "explain_concept":
            return "Preparing explanation", f"Building an explanation for {args.get('concept', 'the concept')}."
        if tool_name == "generate_quiz":
            return "Generating quiz", f"Creating questions for {args.get('topic', 'the topic')}."
        return "Running tool", f"Running {tool_name.replace('_', ' ')}."

    def _tool_complete_detail(self, tool_name: str, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return result.get("error", "The tool returned an error.")
        if tool_name == "get_quote":
            quote = result.get("quote", {})
            return f"Quote received from {quote.get('source', 'market data')}."
        if tool_name == "analyze_stock":
            analysis = result.get("analysis_result", {})
            decision = analysis.get("trade_decision", {}).get("decision", "decision ready")
            quality = analysis.get("data_quality", {}).get("overall", "unknown quality")
            return f"Analysis complete: {decision}, data quality {quality}."
        if tool_name == "get_market_trends":
            return f"Scanned {len(result.get('trends', []))} symbols."
        if tool_name == "portfolio_analysis":
            summary = result.get("summary", {})
            return f"Read {summary.get('position_count', 0)} positions from context."
        return "Tool completed successfully."

    def _routing_system_prompt(self) -> str:
        return """
You are an intelligent assistant for the Neural Options Oracle++ trading platform.

Your job is to understand what the user wants and call the appropriate tools to help them.

Style:
- Be concise, premium, and direct.
- Do not use emojis.
- For casual messages, answer in one short sentence.
- Do not list all platform features unless the user asks what you can do.

Available capabilities:
1. **Stock Analysis** - Analyze any stock symbol with technical indicators, sentiment, options flow
2. **Options Buying** - Buy single options for specific stocks with budget analysis
3. **Multi-Options Buying** - Find and buy best options from hot stocks within budget
4. **Education** - Explain trading concepts, options Greeks, strategies in simple terms  
5. **Market Trends** - Show trending stocks and market overview
6. **Portfolio** - Analyze portfolio performance and risk
7. **Quizzes** - Generate educational quizzes to test knowledge
8. **Casual Chat** - Handle greetings and general conversation

Instructions:
- Use the provided context when the user says "this", "it", "the selected stock", or omits a ticker.
- For price/current quote requests (e.g. "price of TSLA", "what is AAPL trading at"), call get_quote. Do not call analyze_stock for a simple quote.
- For stock analysis requests, extract the symbol and call analyze_stock
- For buying options with budget (e.g., "buy AAPL option with $500"), call buy_option
- For buying best options from hot stocks (e.g., "find best options with $500 budget"), call buy_multiple_options
- For questions about trading concepts, call explain_concept  
- For casual greetings/conversation, call casual_response
- For portfolio requests, call portfolio_analysis
- For quiz requests, call generate_quiz
- For market trends, call get_market_trends

IMPORTANT BUY REQUEST HANDLING:
- If user wants to buy a specific option (e.g., "buy TSLA strike 425"), call buy_option with symbol and infer budget as $500 if not specified
- If user asks for "most profitable option" or "best option with $X budget", call buy_multiple_options
- Always assume a default budget of $500 for option purchases if not explicitly mentioned
- For buy requests, ALWAYS extract: symbol, budget (default $500), risk_tolerance (default "moderate")

Always choose the most appropriate tool(s) for the user's request.
You can call multiple tools if needed.
"""

    async def _route_node(self, state: ChatGraphState) -> ChatGraphState:
        user_message = state["user_message"]
        context = state.get("context", {})
        logger.info(f"LangGraph routing message: '{user_message[:50]}...'")
        llm_result = await self.routing_client.complete_with_tools(
            messages=[
                {"role": "system", "content": self._routing_system_prompt()},
                {
                    "role": "system",
                    "content": (
                        "Runtime context JSON. Use it only when relevant, especially selectedStock: "
                        f"{json.dumps(self._safe_context_for_prompt(context), default=str)}"
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            tools=self.available_tools,
            temperature=0.1,
        )
        return {
            "llm_result": llm_result,
            "timestamp": datetime.now().isoformat(),
        }

    def _route_next_node(self, state: ChatGraphState) -> str:
        llm_result = state.get("llm_result")
        if llm_result and llm_result.tool_calls:
            return "execute_tools"
        return "direct_response"

    async def _execute_tools_node(self, state: ChatGraphState) -> ChatGraphState:
        llm_result = state["llm_result"]
        tool_results = []
        for tool_call in llm_result.tool_calls:
            tool_results.append(await self._execute_tool_call(tool_call, state))

        symbol = None
        for result in tool_results:
            if result.get("symbol"):
                symbol = result["symbol"]
                break

        return {
            "tool_results": tool_results,
            "tools_called": [tc.name for tc in llm_result.tool_calls],
            "intent": self._determine_intent_from_tools(llm_result.tool_calls),
            "confidence": 0.9,
            **({"symbol": symbol} if symbol else {}),
        }

    async def _write_response_node(self, state: ChatGraphState) -> ChatGraphState:
        final_response = await self._format_final_response(
            state["user_message"],
            state["llm_result"],
            state.get("tool_results", []),
        )
        return {
            "response": final_response,
            "formatted": True,
            "timestamp": state.get("timestamp", datetime.now().isoformat()),
        }

    async def _direct_response_node(self, state: ChatGraphState) -> ChatGraphState:
        llm_result = state.get("llm_result")
        return {
            "response": llm_result.content if llm_result else "",
            "intent": "GENERAL_CHAT",
            "tools_called": [],
            "tool_results": [],
            "confidence": 0.7,
            "formatted": True,
            "timestamp": state.get("timestamp", datetime.now().isoformat()),
        }
    
    async def _execute_tool_call(self, tool_call, state: ChatGraphState) -> Dict[str, Any]:
        """Execute a single tool call and return results"""
        function_name = tool_call.name
        arguments = self._normalize_tool_arguments(tool_call.name, tool_call.arguments, state)
        
        logger.info(f"Executing tool: {function_name} with args: {arguments}")
        
        try:
            if function_name == "get_quote":
                return await self._get_quote(arguments)
            elif function_name == "analyze_stock":
                return await self._analyze_stock(arguments)
            elif function_name == "explain_concept":
                return await self._explain_concept(arguments)
            elif function_name == "get_market_trends":
                return await self._get_market_trends(arguments)
            elif function_name == "portfolio_analysis":
                return await self._portfolio_analysis(arguments, state.get("context", {}))
            elif function_name == "generate_quiz":
                return await self._generate_quiz(arguments)
            elif function_name == "casual_response":
                return await self._casual_response(arguments)
            elif function_name == "buy_option":
                return await self._buy_option(arguments)
            elif function_name == "buy_multiple_options":
                return await self._buy_multiple_options(arguments)
            else:
                return {"error": f"Unknown tool: {function_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution failed for {function_name}: {e}")
            return {"error": str(e), "tool": function_name}

    def _safe_context_for_prompt(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Keep routing context small and free of bulky/private fields."""
        allowed_keys = {
            "selectedStock",
            "risk_tolerance",
            "experience",
            "session_id",
            "user_id",
        }
        safe = {key: context.get(key) for key in allowed_keys if context.get(key) is not None}
        positions = context.get("positions") or context.get("portfolio", {}).get("positions")
        if isinstance(positions, list):
            safe["portfolio_position_count"] = len(positions)
            safe["portfolio_symbols"] = [
                str(position.get("symbol", "")).upper()
                for position in positions[:10]
                if position.get("symbol")
            ]
        return safe

    def _normalize_tool_arguments(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: ChatGraphState,
    ) -> Dict[str, Any]:
        """Fill obvious missing args from context or text before tool execution."""
        normalized = dict(arguments or {})
        if tool_name in {"get_quote", "analyze_stock", "buy_option"}:
            symbol = normalized.get("symbol") or self._extract_symbol_from_context_or_text(state)
            if symbol:
                normalized["symbol"] = symbol

        if tool_name == "buy_option":
            normalized.setdefault("budget", 500)
            normalized.setdefault("risk_tolerance", "moderate")
        elif tool_name == "buy_multiple_options":
            normalized.setdefault("risk_tolerance", "moderate")
            normalized.setdefault("diversification", "moderate")
        elif tool_name == "get_market_trends":
            normalized.setdefault("limit", 8)

        return normalized

    def _extract_symbol_from_context_or_text(self, state: ChatGraphState) -> Optional[str]:
        context = state.get("context", {})
        selected = context.get("selectedStock")
        if isinstance(selected, str) and re.fullmatch(r"[A-Za-z]{1,6}", selected.strip()):
            return selected.strip().upper()

        text = state.get("user_message", "")
        ignore = {
            "I", "A", "YO", "HI", "BUY", "SELL", "CALL", "PUT", "PUTS", "CALLS",
            "PRICE", "ANALYZE", "STOCK", "OPTION", "OPTIONS", "THE", "THIS",
        }
        candidates = re.findall(r"\b[A-Za-z]{1,6}\b", text)
        for candidate in candidates:
            upper = candidate.upper()
            if upper not in ignore and candidate.isupper():
                return upper
        return None

    def _trend_symbols_for_sector(self, sector: Optional[str]) -> List[str]:
        sector_key = (sector or "").strip().lower()
        sector_map = {
            "tech": ["NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMD", "TSLA", "QQQ"],
            "technology": ["NVDA", "AAPL", "MSFT", "META", "GOOGL", "AMD", "TSLA", "QQQ"],
            "semis": ["NVDA", "AMD", "AVGO", "MU", "QCOM", "SMH", "TSM", "INTC"],
            "semiconductors": ["NVDA", "AMD", "AVGO", "MU", "QCOM", "SMH", "TSM", "INTC"],
            "energy": ["XOM", "CVX", "COP", "SLB", "OXY", "XLE", "EOG", "MPC"],
            "finance": ["JPM", "BAC", "GS", "MS", "WFC", "XLF", "C", "SCHW"],
            "financials": ["JPM", "BAC", "GS", "MS", "WFC", "XLF", "C", "SCHW"],
        }
        return sector_map.get(
            sector_key,
            ["SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "MSFT", "META", "AMZN", "GOOGL"],
        )

    async def _get_quote(self, args: Dict) -> Dict[str, Any]:
        """Fetch the latest available market quote for a symbol."""
        try:
            from src.data.alpaca_client import AlpacaMarketDataClient

            symbol = args["symbol"].upper()
            quote = await asyncio.wait_for(
                AlpacaMarketDataClient().get_current_quote(symbol),
                timeout=8,
            )
            price = float(quote.get("price") or 0)
            if price <= 0:
                raise ValueError("Quote provider returned no valid price")

            return {
                "tool": "get_quote",
                "symbol": symbol,
                "quote": quote,
                "success": True,
            }
        except Exception as e:
            return {
                "tool": "get_quote",
                "symbol": str(args.get("symbol", "")).upper() or None,
                "error": str(e),
                "success": False,
            }
    
    async def _analyze_stock(self, args: Dict) -> Dict[str, Any]:
        """Execute stock analysis"""
        try:
            from agents.orchestrator import OptionsOracleOrchestrator
            
            symbol = args["symbol"].upper()
            analysis_type = args.get("analysis_type", "full")
            
            # Initialize orchestrator
            orchestrator = OptionsOracleOrchestrator()
            if not orchestrator.initialized:
                await orchestrator.initialize()
            
            # Run analysis
            user_risk_profile = {"risk_tolerance": "moderate", "experience": "beginner"}
            result = await orchestrator.analyze_stock(symbol, user_risk_profile, analysis_type)
            
            return {
                "tool": "analyze_stock",
                "symbol": symbol,
                "analysis_result": result,
                "success": True
            }
            
        except Exception as e:
            return {"tool": "analyze_stock", "error": str(e), "success": False}
    
    async def _explain_concept(self, args: Dict) -> Dict[str, Any]:
        """Execute concept explanation"""
        try:
            from src.api.routes.education import explain_concept as explain_api
            
            concept = args["concept"]
            context = args.get("context", {})
            
            # Call education API
            explanation = await explain_api(concept, context, session={})
            
            return {
                "tool": "explain_concept",
                "concept": concept,
                "explanation": explanation,
                "success": True
            }
            
        except Exception as e:
            return {"tool": "explain_concept", "error": str(e), "success": False}
    
    async def _get_market_trends(self, args: Dict) -> Dict[str, Any]:
        """Get a lightweight market trend snapshot from quote data."""
        try:
            from src.data.alpaca_client import AlpacaMarketDataClient

            client = AlpacaMarketDataClient()
            sector = args.get("sector")
            limit = int(args.get("limit") or 8)
            symbols = self._trend_symbols_for_sector(sector)[: max(1, min(limit, 12))]

            quote_results = await asyncio.gather(
                *[client.get_current_quote(symbol) for symbol in symbols],
                return_exceptions=True,
            )

            trends = []
            for symbol, quote in zip(symbols, quote_results):
                if isinstance(quote, Exception):
                    trends.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(quote),
                    })
                    continue
                trends.append({
                    "symbol": symbol,
                    "price": quote.get("price"),
                    "change": quote.get("change"),
                    "change_percent": quote.get("change_percent"),
                    "volume": quote.get("volume"),
                    "source": quote.get("source"),
                    "timestamp": quote.get("timestamp"),
                    "success": True,
                })

            sorted_trends = sorted(
                trends,
                key=lambda row: abs(float(row.get("change_percent") or 0)),
                reverse=True,
            )
            return {
                "tool": "get_market_trends", 
                "sector": sector or "broad_market_watchlist",
                "trends": sorted_trends,
                "data_quality": {
                    "source_status": "limited",
                    "source": "alpaca_or_yfinance_quotes",
                    "is_fallback": False,
                    "warnings": [
                        "This is a quote-based watchlist snapshot, not full market breadth or social trend data."
                    ],
                },
                "success": True,
            }
            
        except Exception as e:
            return {"tool": "get_market_trends", "error": str(e), "success": False}
    
    async def _portfolio_analysis(self, args: Dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze portfolio data supplied in chat context."""
        try:
            context = context or {}
            positions = context.get("positions") or context.get("portfolio", {}).get("positions") or []
            if not positions:
                return {
                    "tool": "portfolio_analysis",
                    "success": False,
                    "error": "No portfolio positions were provided in chat context.",
                    "data_quality": {
                        "source_status": "unavailable",
                        "source": "chat_context",
                        "is_fallback": True,
                        "warnings": [
                            "Portfolio analysis requires authenticated portfolio context."
                        ],
                    },
                }

            total_market_value = 0.0
            total_unrealized_pnl = 0.0
            by_symbol: Dict[str, Dict[str, Any]] = {}
            for position in positions:
                symbol = str(position.get("symbol", "UNKNOWN")).upper()
                market_value = float(position.get("market_value") or position.get("value") or 0)
                unrealized = float(position.get("unrealized_pnl") or position.get("pnl") or 0)
                total_market_value += market_value
                total_unrealized_pnl += unrealized
                by_symbol[symbol] = {
                    "market_value": round(market_value, 2),
                    "unrealized_pnl": round(unrealized, 2),
                }

            return {
                "tool": "portfolio_analysis",
                "analysis_type": args.get("analysis_type", "summary"),
                "summary": {
                    "position_count": len(positions),
                    "total_market_value": round(total_market_value, 2),
                    "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                    "symbols": by_symbol,
                },
                "data_quality": {
                    "source_status": "limited",
                    "source": "chat_context",
                    "is_fallback": False,
                    "warnings": [
                        "This uses positions supplied to chat context; live account refresh is handled by portfolio endpoints."
                    ],
                },
                "success": True,
            }
            
        except Exception as e:
            return {"tool": "portfolio_analysis", "error": str(e), "success": False}
    
    async def _generate_quiz(self, args: Dict) -> Dict[str, Any]:
        """Generate educational quiz"""
        try:
            from src.api.routes.education import generate_quiz as quiz_api
            from src.api.routes.education import QuizRequest
            
            topic = args["topic"]
            difficulty = args.get("difficulty", "beginner")
            count = args.get("question_count", 5)
            
            request = QuizRequest(topic=topic, difficulty=difficulty, question_count=count)
            quiz = await quiz_api(request, session={})
            
            return {
                "tool": "generate_quiz",
                "quiz": quiz,
                "success": True
            }
            
        except Exception as e:
            return {"tool": "generate_quiz", "error": str(e), "success": False}
    
    async def _casual_response(self, args: Dict) -> Dict[str, Any]:
        """Generate a casual response with the configured LLM."""
        message = args["message"]
        response = await self.routing_client.complete(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Oracle, a concise options-trading assistant. "
                        "Reply naturally to casual chat in one short sentence. "
                        "Do not use emojis. Do not fabricate market prices."
                    ),
                },
                {"role": "user", "content": message},
            ],
            temperature=0.4,
            max_tokens=120,
        )
        return {"tool": "casual_response", "response": response, "success": True}
    
    async def _buy_option(self, args: Dict) -> Dict[str, Any]:
        """Execute single option purchase analysis"""
        try:
            from src.agents.buy_agent import analyze_option_buy
            
            symbol = args["symbol"].upper()
            budget = float(args.get("budget", 500))  # Default to $500 if not specified
            risk_tolerance = args.get("risk_tolerance", "moderate")
            
            preferences = {
                "risk_tolerance": risk_tolerance,
                "strategy": "growth",
                "time_horizon": "short"
            }
            
            analysis = await analyze_option_buy(symbol, budget, preferences)
            
            return {
                "tool": "buy_option",
                "symbol": symbol,
                "budget": budget,
                "analysis": analysis,
                "requires_confirmation": True,
                "success": True
            }
            
        except Exception as e:
            return {"tool": "buy_option", "error": str(e), "success": False}
    
    async def _buy_multiple_options(self, args: Dict) -> Dict[str, Any]:
        """Execute multi-options portfolio analysis"""
        try:
            from src.agents.multi_options_buy_agent import analyze_multi_options_buy
            
            budget = float(args["budget"])
            risk_tolerance = args.get("risk_tolerance", "moderate")
            diversification = args.get("diversification", "moderate")
            
            preferences = {
                "risk_tolerance": risk_tolerance,
                "diversification": diversification,
                "strategy": "growth"
            }
            
            portfolio = await analyze_multi_options_buy(budget, preferences)
            
            return {
                "tool": "buy_multiple_options",
                "budget": budget,
                "portfolio": portfolio,
                "requires_confirmation": True,
                "success": True
            }
            
        except Exception as e:
            return {"tool": "buy_multiple_options", "error": str(e), "success": False}
    
    async def _format_final_response(
        self, 
        user_message: str, 
        ai_message, 
        tool_results: List[Dict]
    ) -> str:
        """Let OpenAI format the final human-readable response"""
        try:
            if len(tool_results) == 1 and tool_results[0].get("tool") == "casual_response":
                return tool_results[0].get("response", "")

            # Create context for final formatting
            compact_results = self._compact_tool_results_for_prompt(tool_results)
            
            format_prompt = f"""
Based on the user's request and the tool results, provide a clear, helpful response in markdown format.

User asked: "{user_message}"

Tool results: {json.dumps(compact_results, indent=2)}

Instructions:
1. Write in a friendly, conversational tone
2. Keep the response concise and do not use emojis
3. Use markdown formatting for readability when it helps
4. If get_quote was used, answer with the price, change, percent change, and data source only. Do not add technical analysis.
5. If stock analysis was performed, lead with trade_decision, signal, confidence, current price, data quality, scenario, technical levels, options flow, key risks, and next action
6. If explaining concepts, make it easy to understand
7. Include relevant data and insights from tool results
8. End with one helpful next step
9. If data_quality is weak, fallback, unavailable, or limited, say so plainly and do not imply institutional flow or live social data

Keep the answer under 700 words.
"""

            formatted = await self.client.complete(
                messages=[{"role": "user", "content": format_prompt}],
                temperature=0.3,
                max_tokens=1600,
            )
            if formatted and formatted.strip():
                return formatted
            logger.warning("Response formatter returned empty content; using deterministic fallback")
            return self._create_fallback_formatted_response(tool_results)
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            return self._create_fallback_formatted_response(tool_results)

    def _compact_tool_results_for_prompt(self, tool_results: List[Dict]) -> List[Dict[str, Any]]:
        """Trim deeply nested tool output before giving it to the writer LLM."""
        compact = []
        for result in tool_results:
            tool = result.get("tool")
            if tool == "analyze_stock" and result.get("analysis_result"):
                analysis = result["analysis_result"]
                agent_results = analysis.get("agent_results", {})
                technical = agent_results.get("technical", {})
                flow = agent_results.get("flow", {})
                sentiment = agent_results.get("sentiment", {})
                history = agent_results.get("history", {})
                signal = analysis.get("signal", {})
                compact.append({
                    "tool": tool,
                    "success": result.get("success", False),
                    "symbol": result.get("symbol"),
                    "market_scenario": analysis.get("market_scenario"),
                    "confidence": analysis.get("confidence"),
                    "decision_score": analysis.get("decision_score"),
                    "signal": signal,
                    "trade_decision": analysis.get("trade_decision"),
                    "data_quality": analysis.get("data_quality"),
                    "technical": {
                        "scenario": technical.get("scenario"),
                        "weighted_score": technical.get("weighted_score"),
                        "confidence": technical.get("confidence"),
                        "support_resistance": technical.get("support_resistance"),
                        "volume_analysis": technical.get("volume_analysis"),
                        "key_insights": technical.get("key_insights", [])[:3],
                        "market_data_snapshot": {
                            "current_price": technical.get("market_data_snapshot", {}).get("current_price"),
                            "change_percent": technical.get("market_data_snapshot", {}).get("change_percent"),
                            "source": technical.get("market_data_snapshot", {}).get("source"),
                        },
                    },
                    "options_flow": {
                        "flow_score": flow.get("flow_score"),
                        "confidence": flow.get("confidence"),
                        "unusual_activity": flow.get("unusual_activity"),
                        "metrics": flow.get("metrics"),
                        "flow_sentiment": flow.get("flow_sentiment"),
                        "key_insights": flow.get("key_insights", [])[:3],
                        "data_quality": flow.get("data_quality"),
                        "source": flow.get("source"),
                        "is_fallback": flow.get("is_fallback"),
                    },
                    "sentiment": {
                        "aggregate_score": sentiment.get("aggregate_score"),
                        "confidence": sentiment.get("confidence"),
                        "sentiment_trend": sentiment.get("sentiment_trend"),
                        "key_factors": sentiment.get("key_factors", [])[:3],
                        "risk_factors": sentiment.get("risk_factors", [])[:3],
                        "data_quality": sentiment.get("data_quality"),
                        "source": sentiment.get("source"),
                        "is_fallback": sentiment.get("is_fallback"),
                    },
                    "history": {
                        "pattern_score": history.get("pattern_score"),
                        "confidence": history.get("confidence"),
                        "dominant_pattern": history.get("dominant_pattern"),
                        "key_levels": history.get("key_levels"),
                        "pattern_insights": history.get("pattern_insights", [])[:3],
                    },
                    "strike_recommendations": analysis.get("strike_recommendations", [])[:3],
                })
            else:
                compact.append(result)
        return compact
    
    def _create_fallback_formatted_response(self, tool_results: List[Dict]) -> str:
        """Create a basic formatted response if AI formatting fails"""
        response = "## Analysis Complete\n\n"
        
        for result in tool_results:
            if result.get("success"):
                tool = result.get("tool", "analysis")
                if tool == "get_quote":
                    quote = result.get("quote", {})
                    symbol = result.get("symbol", "symbol")
                    price = float(quote.get("price") or 0)
                    change = float(quote.get("change") or 0)
                    change_percent = float(quote.get("change_percent") or 0)
                    source = quote.get("source", "market data")
                    return (
                        f"**{symbol}** is trading at **${price:,.2f}**.\n\n"
                        f"Change: {change:+.2f} ({change_percent:+.2f}%).\n\n"
                        f"_Source: {source}._"
                    )
                response += f"**{tool.replace('_', ' ').title()}** completed successfully\n\n"
                
                if "analysis_result" in result:
                    analysis = result["analysis_result"]
                    signal = analysis.get("signal", {})
                    trade_decision = analysis.get("trade_decision", {})
                    decision = trade_decision.get("decision", "NO_TRADE")
                    direction = trade_decision.get("direction", "neutral")
                    data_quality = trade_decision.get("data_quality") or analysis.get("data_quality", {}).get("overall", "unknown")
                    response += f"- **Decision**: {decision} ({direction})\n"
                    response += f"- **Signal**: {signal.get('direction', 'HOLD')}\n"
                    response += f"- **Confidence**: {analysis.get('confidence', 0):.1%}\n"
                    response += f"- **Data quality**: {data_quality}\n"
                    if trade_decision.get("entry_trigger"):
                        response += f"- **Next action**: {trade_decision['entry_trigger']}\n"
                    rationale = trade_decision.get("rationale", [])
                    if rationale:
                        response += "\n" + " ".join(rationale[:3]) + "\n\n"
            else:
                response += f"**{result.get('tool', 'Tool')}** encountered an error\n\n"
        
        return response
    
    def _determine_intent_from_tools(self, tool_calls) -> str:
        """Determine intent based on tools called"""
        if not tool_calls:
            return "GENERAL_CHAT"
        
        tool_names = [tc.name for tc in tool_calls]
        
        if "get_quote" in tool_names:
            return "QUOTE"
        elif "analyze_stock" in tool_names:
            return "STOCK_ANALYSIS"
        elif "buy_option" in tool_names:
            return "OPTIONS_BUYING"
        elif "buy_multiple_options" in tool_names:
            return "PORTFOLIO_BUYING"
        elif "explain_concept" in tool_names:
            return "OPTIONS_EDUCATION"
        elif "get_market_trends" in tool_names:
            return "MARKET_TRENDS"
        elif "portfolio_analysis" in tool_names:
            return "PORTFOLIO_MANAGEMENT"
        elif "generate_quiz" in tool_names:
            return "QUIZ_LEARNING"
        else:
            return "GENERAL_CHAT"
    
    async def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """Fallback response when AI routing fails"""
        return {
            "response": f"I encountered an issue processing your request: '{user_message}'. Please try asking about a specific stock symbol or trading concept.",
            "intent": "ERROR",
            "tools_called": [],
            "confidence": 0.0,
            "formatted": True,
            "timestamp": datetime.now().isoformat(),
            "error": True
        }


# Global instance
ai_intent_router = AIIntentRouter()

async def route_with_ai(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main function to route messages using AI with tool calling
    """
    return await ai_intent_router.route_and_process(message, context or {})
