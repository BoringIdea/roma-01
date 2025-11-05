"""
Chat service for AI assistant functionality.

Provides a simple interface for users to chat with AI about trading strategies,
prompts, and platform features.
"""

import dspy
from typing import Optional
from loguru import logger
from roma_trading.config import get_settings
from roma_trading.agents import AgentManager


class ChatResponse(dspy.Signature):
    """AI assistant response signature for chat."""
    system_context: str = dspy.InputField(desc="System context and instructions")
    user_message: str = dspy.InputField(desc="User's message")
    response: str = dspy.OutputField(desc="AI assistant's helpful response")


class ChatService:
    """Service for handling chat requests with AI assistant."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
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
                        lm = dspy.LM(
                            f"qwen/{model}" if model else "qwen/qwen-max",
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
                    lm = dspy.LM(
                        f"qwen/{model}" if model else "qwen/qwen-max",
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
    
    async def chat(self, message: str) -> str:
        """
        Process a chat message and return AI response.
        
        Args:
            message: User's message
            
        Returns:
            AI assistant's response
        """
        try:
            lm = self._get_llm()
            
            # Build system prompt for chat assistant
            system_prompt = """You are a helpful AI assistant for the ROMA-01 cryptocurrency futures trading platform. 
Your role is to help users understand:
- Trading strategies and prompt suggestions
- Risk management concepts
- Platform features and capabilities
- Trading best practices

Provide clear, concise, and helpful responses. If asked about trading prompts, provide practical examples.
If asked about risk management, explain the 4-layer risk management system.
Always be helpful and professional."""

            # Use per-request DSPy context to avoid global configuration conflicts
            with dspy.context(lm=lm):
                chat_module = dspy.ChainOfThought(ChatResponse)
                result = chat_module(
                    system_context=system_prompt,
                    user_message=message
                )
            
            return result.response.strip()
                
        except Exception as e:
            logger.error(f"Error in chat service: {e}", exc_info=True)
            raise


# Global chat service instance (will be initialized in main.py)
chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get global chat service instance."""
    global chat_service
    if chat_service is None:
        raise RuntimeError("Chat service not initialized. Call initialize_chat_service() first.")
    return chat_service


def initialize_chat_service(agent_manager: AgentManager):
    """Initialize global chat service."""
    global chat_service
    chat_service = ChatService(agent_manager)
    logger.info("Chat service initialized")

