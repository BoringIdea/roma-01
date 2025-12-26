"""
Chat service for AI assistant functionality.

Provides a simple interface for users to chat with AI about trading strategies,
prompts, and platform features.
"""

import asyncio
import dspy
from typing import Optional, TYPE_CHECKING
from loguru import logger
from roma_trading.config import get_settings
from roma_trading.agents import AgentManager
from roma_trading.prompts import render_prompt
from roma_trading.core.token_analysis_handler import TokenAnalysisHandler

if TYPE_CHECKING:
    pass  # Keep for future type-only imports


class ChatResponse(dspy.Signature):
    """AI assistant response signature for chat."""
    system_context: str = dspy.InputField(desc="System context and instructions")
    user_message: str = dspy.InputField(desc="User's message")
    response: str = dspy.OutputField(desc="AI assistant's helpful response")


class ChatService:
    """Service for handling chat requests with AI assistant."""
    
    def __init__(self, agent_manager: "AgentManager"):
        self.agent_manager = agent_manager
        self.token_handler = TokenAnalysisHandler(agent_manager)
    
    def _get_llm(self):
        """Build an LM instance for this request without configuring DSPy globally."""
        
        # Try to get LLM from a running agent by reusing its config
        agents = self.agent_manager.get_all_agents()
        for agent_info in agents:
            try:
                agent = self.agent_manager.get_agent(agent_info["id"])
                if agent.is_running:
                    # Use agent's LLM config to initialize our own LLM
                    llm_config = agent.config["llm"]
                    provider = llm_config["provider"]
                    model = llm_config.get("model", "")
                    api_key = llm_config["api_key"]
                    
                    logger.info(f"Using LLM from running agent: {agent_info['id']} ({provider})")
                    
                    # Initialize LLM based on provider
                    if provider == "deepseek":
                        lm = dspy.LM(
                            f"deepseek/{model}" if model else "deepseek/deepseek-chat",
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    elif provider == "qwen":
                        # Qwen uses DashScope API (OpenAI-compatible)
                        # Support different regions: china uses dashscope.aliyuncs.com, others use dashscope-intl.aliyuncs.com
                        model_name = model if model else "qwen-max"
                        location = llm_config.get("location", "china").lower()
                        if location == "china":
                            api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                        else:
                            api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                        
                        # Use "dashscope/" prefix for DashScope models
                        lm = dspy.LM(
                            f"dashscope/{model_name}",
                            api_base=api_base,
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    elif provider == "anthropic":
                        lm = dspy.LM(
                            f"anthropic/{model}" if model else "anthropic/claude-sonnet-4.5",
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    elif provider == "xai":
                        lm = dspy.LM(
                            f"xai/{model}" if model else "xai/grok-4",
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    elif provider == "google":
                        lm = dspy.LM(
                            f"gemini/{model}" if model else "gemini/gemini-2.5-pro",
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    elif provider == "openai":
                        lm = dspy.LM(
                            f"openai/{model}" if model else "openai/gpt-5",
                            api_key=api_key,
                            temperature=0.7,
                            max_tokens=2000,
                        )
                    else:
                        continue
                    
                    return lm
            except Exception as e:
                logger.debug(f"Could not use agent {agent_info['id']} LLM: {e}")
                continue
        
        # If no running agent, try to initialize from first agent's config
        if agents:
            try:
                first_agent = self.agent_manager.get_agent(agents[0]["id"])
                llm_config = first_agent.config["llm"]
                provider = llm_config["provider"]
                model = llm_config.get("model", "")
                api_key = llm_config["api_key"]
                
                logger.info(f"Using LLM from agent config: {agents[0]['id']} ({provider})")
                
                # Initialize LLM based on provider (same logic as above)
                if provider == "deepseek":
                    lm = dspy.LM(
                        f"deepseek/{model}" if model else "deepseek/deepseek-chat",
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                elif provider == "qwen":
                    # Qwen uses DashScope API (OpenAI-compatible)
                    # Support different regions: china uses dashscope.aliyuncs.com, others use dashscope-intl.aliyuncs.com
                    model_name = model if model else "qwen-max"
                    location = llm_config.get("location", "china").lower()
                    if location == "china":
                        api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                    else:
                        api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                    
                    # Use "dashscope/" prefix for DashScope models
                    lm = dspy.LM(
                        f"dashscope/{model_name}",
                        api_base=api_base,
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                elif provider == "anthropic":
                    lm = dspy.LM(
                        f"anthropic/{model}" if model else "anthropic/claude-sonnet-4.5",
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                elif provider == "xai":
                    lm = dspy.LM(
                        f"xai/{model}" if model else "xai/grok-4",
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                elif provider == "google":
                    lm = dspy.LM(
                        f"gemini/{model}" if model else "gemini/gemini-2.5-pro",
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                elif provider == "openai":
                    lm = dspy.LM(
                        f"openai/{model}" if model else "openai/gpt-5",
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
                
                return lm
            except Exception as e:
                logger.debug(f"Could not initialize LLM from agent config: {e}")
        
        # Fallback: try to initialize from settings
        settings = get_settings()
        if settings.deepseek_api_key:
            logger.info("Initializing chat LLM from DeepSeek settings")
            lm = dspy.LM(
                "deepseek/deepseek-chat",
                api_key=settings.deepseek_api_key,
                temperature=0.7,
                max_tokens=2000,
            )
            return lm
        
        raise RuntimeError("No LLM available for chat. Please ensure at least one agent is configured.")

    def get_llm(self):
        """Expose LLM construction for other services (e.g., strategy advisor)."""
        return self._get_llm()

    async def chat(self, message: str, language: str = "en") -> str:
        """
        Process a chat message and return AI response.
        
        Args:
            message: User's message
            language: Language preference ("en" or "zh")
            
        Returns:
            AI assistant's response
        """
        try:
            # Check if this is a token analysis request
            if self.token_handler.detect_analysis_request(message):
                token_symbol = self.token_handler.extract_token_symbol(message)
                logger.debug(f"Analysis request detected. Message: {message}, Token: {token_symbol}")
                
                if token_symbol:
                    # Perform token analysis
                    logger.info(f"Detected token analysis request for {token_symbol}")
                    return await self._handle_token_analysis(
                        message, token_symbol, language
                    )
                else:
                    logger.debug(f"Analysis request detected but no token symbol found in: {message}")
            
            # Default to general chat
            return await asyncio.to_thread(
                self._chat_sync, message, language
            )
                
        except Exception as e:
            logger.error(f"Error in chat service: {e}", exc_info=True)
            raise

    async def _handle_token_analysis(
        self, 
        message: str, 
        symbol: str, 
        language: str
    ) -> str:
        """Handle token analysis request."""
        try:
            # Fetch token data
            token_data = await self.token_handler.fetch_token_data(symbol)
            
            # Format analysis prompt
            analysis_prompt = self.token_handler.format_analysis_prompt(
                token_data, language
            )
            
            # Generate AI response with analysis
            return await asyncio.to_thread(
                self._chat_sync_with_context,
                message,
                analysis_prompt,
                language
            )
        except ValueError as e:
            # Token not found or invalid symbol
            logger.warning(f"Token analysis failed for {symbol}: {e}")
            if language == "zh":
                error_msg = f"抱歉，无法找到代币 {symbol}。该代币可能不在当前交易所支持列表中，或者代币符号不正确。请检查代币符号后重试。"
            else:
                error_msg = f"Sorry, I couldn't find token {symbol}. This token may not be available on the current exchange, or the symbol may be incorrect. Please check the token symbol and try again."
            return error_msg
        except Exception as e:
            logger.error(f"Token analysis failed for {symbol}: {e}", exc_info=True)
            # Fallback to general chat with error message
            if language == "zh":
                error_msg = f"分析 {symbol} 时遇到错误：{str(e)}。请稍后重试或检查代币符号是否正确。"
            else:
                error_msg = f"I encountered an error analyzing {symbol}: {str(e)}. Please try again later or check if the token symbol is correct."
            return await asyncio.to_thread(
                self._chat_sync, 
                error_msg,
                language
            )
    
    def _chat_sync_with_context(
        self, 
        message: str, 
        context: str, 
        language: str
    ) -> str:
        """Run chat with additional context for token analysis."""
        lm = self._get_llm()
        
        # Load enhanced system prompt for token analysis
        try:
            system_prompt = render_prompt("chat_token_analysis", language=language)
        except ValueError:
            # Fallback to general chat prompt if token analysis prompt not found
            logger.warning(f"Token analysis prompt not found, using general chat prompt")
            system_prompt = render_prompt("chat", language=language)
        
        # Combine context with user message
        full_message = f"{context}\n\nUser Question: {message}"
        
        with dspy.context(lm=lm):
            chat_module = dspy.ChainOfThought(ChatResponse)
            result = chat_module(
                system_context=system_prompt,
                user_message=full_message
            )
        
        return result.response.strip()
    
    def _chat_sync(self, message: str, language: str = "en") -> str:
        """Run chat module synchronously inside a worker thread."""
        lm = self._get_llm()

        system_prompt = render_prompt("chat", language=language)

        with dspy.context(lm=lm):
            chat_module = dspy.ChainOfThought(ChatResponse)
            result = chat_module(
                system_context=system_prompt,
                user_message=message
            )

        return result.response.strip()


# Global chat service instance (will be initialized in main.py)
chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get global chat service instance."""
    global chat_service
    if chat_service is None:
        raise RuntimeError("Chat service not initialized. Call initialize_chat_service() first.")
    return chat_service


def initialize_chat_service(agent_manager: "AgentManager"):
    """Initialize global chat service."""
    global chat_service
    chat_service = ChatService(agent_manager)
    logger.info("Chat service initialized")
