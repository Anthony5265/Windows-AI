"""
AI Agents Manager - Multi-Agent Orchestration
Agent frameworks, tool use, planning, memory
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    name: str
    role: str
    goal: str
    backstory: str = ""
    tools: List[str] = field(default_factory=list)
    llm_provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_iterations: int = 10

@dataclass
class Task:
    description: str
    expected_output: str
    agent: str
    context: List[str] = field(default_factory=list)

class AIAgentsManager:
    """Multi-agent orchestration and coordination"""

    def __init__(self):
        self._initialized = False
        self._agents: Dict[str, AgentConfig] = {}
        self._tools: Dict[str, Callable] = {}
        self._memory: Dict[str, List[Dict]] = {}

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._register_default_tools()
        self._initialized = True

    def _register_default_tools(self):
        """Register built-in tools"""
        self._tools["web_search"] = self._tool_web_search
        self._tools["read_file"] = self._tool_read_file
        self._tools["write_file"] = self._tool_write_file
        self._tools["execute_code"] = self._tool_execute_code
        self._tools["http_request"] = self._tool_http_request
        self._tools["calculator"] = self._tool_calculator

    async def _tool_web_search(self, query: str) -> str:
        from windows_ai.integrations.search_engines import SearchEngineManager
        search = SearchEngineManager()
        await search.initialize()
        results = await search.search(query, provider="duckduckgo", num_results=5)
        return "\n".join([f"- {r['title']}: {r['snippet']}" for r in results])

    async def _tool_read_file(self, path: str) -> str:
        with open(path, "r") as f:
            return f.read()

    async def _tool_write_file(self, path: str, content: str) -> str:
        with open(path, "w") as f:
            f.write(content)
        return f"Written to {path}"

    async def _tool_execute_code(self, code: str, language: str = "python") -> str:
        import subprocess
        if language == "python":
            result = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr
        return "Unsupported language"

    async def _tool_http_request(self, url: str, method: str = "GET", data: Dict = None) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data) as response:
                return await response.text()

    async def _tool_calculator(self, expression: str) -> str:
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))
        except:
            return "Error evaluating expression"

    def register_tool(self, name: str, func: Callable):
        """Register a custom tool"""
        self._tools[name] = func

    def create_agent(self, config: AgentConfig) -> str:
        """Create an agent"""
        self._agents[config.name] = config
        self._memory[config.name] = []
        return config.name

    async def run_agent(self, agent_name: str, task: str, context: Dict = None) -> str:
        """Run a single agent on a task"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        agent = self._agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")

        ai = AIProvidersManager()
        await ai.initialize()

        # Build system prompt
        tool_descriptions = "\n".join([
            f"- {name}: {func.__doc__ or 'No description'}"
            for name, func in self._tools.items()
            if name in agent.tools
        ])

        system_prompt = f"""You are {agent.name}, {agent.role}.
Goal: {agent.goal}
{f'Backstory: {agent.backstory}' if agent.backstory else ''}

Available tools:
{tool_descriptions}

To use a tool, respond with:
TOOL: tool_name
INPUT: tool input

When you have the final answer, respond with:
FINAL ANSWER: your answer"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self._memory.get(agent_name, []))
        messages.append({"role": "user", "content": task})

        for iteration in range(agent.max_iterations):
            response = await ai.chat(
                Provider(agent.llm_provider),
                messages,
                model=agent.model,
                temperature=agent.temperature
            )

            content = response["content"]
            messages.append({"role": "assistant", "content": content})

            # Check for final answer
            if "FINAL ANSWER:" in content:
                answer = content.split("FINAL ANSWER:")[-1].strip()
                self._memory[agent_name] = messages[-10:]  # Keep last 10 messages
                return answer

            # Check for tool use
            if "TOOL:" in content:
                lines = content.split("\n")
                tool_name = None
                tool_input = None
                for line in lines:
                    if line.startswith("TOOL:"):
                        tool_name = line.replace("TOOL:", "").strip()
                    elif line.startswith("INPUT:"):
                        tool_input = line.replace("INPUT:", "").strip()

                if tool_name and tool_name in self._tools:
                    try:
                        result = await self._tools[tool_name](tool_input)
                        messages.append({"role": "user", "content": f"Tool result: {result}"})
                    except Exception as e:
                        messages.append({"role": "user", "content": f"Tool error: {str(e)}"})

        return "Max iterations reached"

    async def run_crew(self, tasks: List[Task]) -> Dict[str, str]:
        """Run multiple agents as a crew"""
        results = {}

        for task in tasks:
            # Build context from previous task results
            context_str = ""
            for ctx_task in task.context:
                if ctx_task in results:
                    context_str += f"\nContext from {ctx_task}: {results[ctx_task]}"

            full_task = f"{task.description}\nExpected output: {task.expected_output}{context_str}"
            result = await self.run_agent(task.agent, full_task)
            results[task.description] = result

        return results

    async def run_parallel_agents(self, agents: List[str], task: str) -> Dict[str, str]:
        """Run multiple agents in parallel on the same task"""
        tasks = [self.run_agent(agent, task) for agent in agents]
        results = await asyncio.gather(*tasks)
        return {agent: result for agent, result in zip(agents, results)}

    # ==================== PRE-BUILT AGENTS ====================

    def create_researcher_agent(self, name: str = "Researcher") -> str:
        """Create a research agent"""
        return self.create_agent(AgentConfig(
            name=name,
            role="Expert Research Analyst",
            goal="Gather comprehensive information and provide accurate, well-researched answers",
            backstory="You are a meticulous researcher with expertise in finding and synthesizing information.",
            tools=["web_search", "http_request"],
            llm_provider="openai",
            model="gpt-4o"
        ))

    def create_coder_agent(self, name: str = "Coder") -> str:
        """Create a coding agent"""
        return self.create_agent(AgentConfig(
            name=name,
            role="Senior Software Engineer",
            goal="Write clean, efficient, and well-documented code",
            backstory="You are an experienced developer with expertise in multiple programming languages.",
            tools=["read_file", "write_file", "execute_code"],
            llm_provider="openai",
            model="gpt-4o"
        ))

    def create_writer_agent(self, name: str = "Writer") -> str:
        """Create a writing agent"""
        return self.create_agent(AgentConfig(
            name=name,
            role="Professional Content Writer",
            goal="Create engaging, well-structured content",
            backstory="You are a skilled writer with experience in various content formats.",
            tools=["web_search"],
            llm_provider="openai",
            model="gpt-4o"
        ))

    def create_analyst_agent(self, name: str = "Analyst") -> str:
        """Create a data analysis agent"""
        return self.create_agent(AgentConfig(
            name=name,
            role="Data Analyst",
            goal="Analyze data and provide actionable insights",
            backstory="You are an expert at extracting insights from data.",
            tools=["calculator", "read_file", "execute_code"],
            llm_provider="openai",
            model="gpt-4o"
        ))

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
