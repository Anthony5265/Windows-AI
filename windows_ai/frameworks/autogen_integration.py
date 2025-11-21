"""
AutoGen Integration for Windows AI
Microsoft's multi-agent conversation framework
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AutoGenConfig:
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120

class AutoGenManager:
    """Manages Microsoft AutoGen integration"""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.group_chats: Dict[str, Any] = {}
        self._config: Optional[AutoGenConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AutoGen components"""
        if self._initialized:
            return

        try:
            from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

            self._config = AutoGenConfig(**(config or {}))

            # LLM configuration
            self.llm_config = {
                "config_list": [
                    {"model": self._config.model, "api_key": ""}  # Will use env var
                ],
                "temperature": self._config.temperature,
                "timeout": self._config.timeout,
            }

            self._initialized = True
            logger.info("AutoGen integration initialized successfully")

        except ImportError as e:
            logger.warning(f"AutoGen not fully available: {e}")

    async def create_assistant(
        self,
        name: str,
        system_message: str,
        llm_config: Optional[Dict] = None
    ) -> Any:
        """Create an AutoGen assistant agent"""
        from autogen import AssistantAgent

        agent = AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config or self.llm_config
        )

        self.agents[name] = agent
        return agent

    async def create_user_proxy(
        self,
        name: str,
        human_input_mode: str = "NEVER",
        max_consecutive_auto_reply: int = 10,
        code_execution_config: Optional[Dict] = None
    ) -> Any:
        """Create an AutoGen user proxy agent"""
        from autogen import UserProxyAgent

        exec_config = code_execution_config or {
            "work_dir": "workspace",
            "use_docker": False,
        }

        agent = UserProxyAgent(
            name=name,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            code_execution_config=exec_config
        )

        self.agents[name] = agent
        return agent

    async def create_group_chat(
        self,
        name: str,
        agent_names: List[str],
        max_round: int = 12,
        speaker_selection_method: str = "auto"
    ) -> Any:
        """Create a group chat with multiple agents"""
        from autogen import GroupChat, GroupChatManager

        agents = [self.agents[n] for n in agent_names if n in self.agents]

        if len(agents) < 2:
            raise ValueError("Group chat requires at least 2 agents")

        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=max_round,
            speaker_selection_method=speaker_selection_method
        )

        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self.llm_config
        )

        self.group_chats[name] = {"chat": group_chat, "manager": manager}
        return manager

    async def start_conversation(
        self,
        initiator_name: str,
        recipient_name: str,
        message: str
    ) -> str:
        """Start a two-agent conversation"""
        initiator = self.agents.get(initiator_name)
        recipient = self.agents.get(recipient_name)

        if not initiator or not recipient:
            raise ValueError("Invalid agent names")

        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: initiator.initiate_chat(recipient, message=message)
        )

        # Extract conversation summary
        return self._extract_summary(result)

    async def start_group_conversation(
        self,
        group_name: str,
        initiator_name: str,
        message: str
    ) -> str:
        """Start a group chat conversation"""
        group = self.group_chats.get(group_name)
        initiator = self.agents.get(initiator_name)

        if not group or not initiator:
            raise ValueError("Invalid group or initiator")

        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: initiator.initiate_chat(group["manager"], message=message)
        )

        return self._extract_summary(result)

    async def create_coding_team(self) -> Dict[str, Any]:
        """Create a pre-configured coding team"""
        # Create planner
        await self.create_assistant(
            name="planner",
            system_message="""You are a helpful AI assistant that plans coding tasks.
            Break down complex problems into smaller steps.
            Provide clear, actionable plans for implementation."""
        )

        # Create coder
        await self.create_assistant(
            name="coder",
            system_message="""You are an expert programmer.
            Write clean, efficient, well-documented code.
            Follow best practices and design patterns."""
        )

        # Create reviewer
        await self.create_assistant(
            name="reviewer",
            system_message="""You are a code reviewer.
            Review code for bugs, security issues, and improvements.
            Suggest optimizations and best practices."""
        )

        # Create executor
        await self.create_user_proxy(
            name="executor",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5
        )

        # Create group chat
        manager = await self.create_group_chat(
            name="coding_team",
            agent_names=["planner", "coder", "reviewer", "executor"]
        )

        return {
            "planner": self.agents["planner"],
            "coder": self.agents["coder"],
            "reviewer": self.agents["reviewer"],
            "executor": self.agents["executor"],
            "manager": manager
        }

    async def create_research_team(self) -> Dict[str, Any]:
        """Create a pre-configured research team"""
        await self.create_assistant(
            name="researcher",
            system_message="""You are a research analyst.
            Gather information, analyze data, and provide insights.
            Be thorough and cite sources when possible."""
        )

        await self.create_assistant(
            name="critic",
            system_message="""You are a critical thinker.
            Evaluate research for accuracy and completeness.
            Identify gaps and suggest improvements."""
        )

        await self.create_assistant(
            name="writer",
            system_message="""You are a technical writer.
            Synthesize research into clear, well-organized reports.
            Make complex topics accessible."""
        )

        await self.create_user_proxy(
            name="user_proxy",
            human_input_mode="NEVER"
        )

        manager = await self.create_group_chat(
            name="research_team",
            agent_names=["researcher", "critic", "writer", "user_proxy"]
        )

        return {
            "researcher": self.agents["researcher"],
            "critic": self.agents["critic"],
            "writer": self.agents["writer"],
            "manager": manager
        }

    def _extract_summary(self, chat_result: Any) -> str:
        """Extract summary from chat result"""
        if hasattr(chat_result, 'summary'):
            return chat_result.summary
        if hasattr(chat_result, 'chat_history'):
            messages = chat_result.chat_history
            if messages:
                return messages[-1].get('content', str(chat_result))
        return str(chat_result)

    def get_agents(self) -> List[str]:
        """Get list of created agents"""
        return list(self.agents.keys())

    def get_group_chats(self) -> List[str]:
        """Get list of created group chats"""
        return list(self.group_chats.keys())
