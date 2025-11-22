"""
CrewAI Integration for Windows AI
Multi-agent collaborative AI teams
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentRole:
    role: str
    goal: str
    backstory: str
    tools: List[str] = None

class CrewAIManager:
    """Manages CrewAI integration for multi-agent collaboration"""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.crews: Dict[str, Any] = {}
        self.tasks: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CrewAI components"""
        if self._initialized:
            return

        try:
            from crewai import Agent, Task, Crew, Process
            from crewai_tools import SerperDevTool, WebsiteSearchTool

            self._crewai_available = True
            self._initialized = True
            logger.info("CrewAI integration initialized successfully")

        except ImportError as e:
            logger.warning(f"CrewAI not fully available: {e}")
            self._crewai_available = False

    async def create_agent(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[Any]] = None,
        llm_model: str = "gpt-4-turbo-preview",
        allow_delegation: bool = True,
        verbose: bool = True
    ) -> Any:
        """Create a CrewAI agent"""
        from crewai import Agent

        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            llm=llm_model,
            allow_delegation=allow_delegation,
            verbose=verbose
        )

        self.agents[name] = agent
        return agent

    async def create_task(
        self,
        name: str,
        description: str,
        agent_name: str,
        expected_output: str,
        context: Optional[List[str]] = None
    ) -> Any:
        """Create a task for an agent"""
        from crewai import Task

        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        # Get context tasks if specified
        context_tasks = []
        if context:
            for ctx_name in context:
                if ctx_name in self.tasks:
                    context_tasks.append(self.tasks[ctx_name])

        task = Task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            context=context_tasks if context_tasks else None
        )

        self.tasks[name] = task
        return task

    async def create_crew(
        self,
        name: str,
        agent_names: List[str],
        task_names: List[str],
        process: str = "sequential",
        verbose: bool = True
    ) -> Any:
        """Create a crew of agents"""
        from crewai import Crew, Process

        agents = [self.agents[n] for n in agent_names if n in self.agents]
        tasks = [self.tasks[n] for n in task_names if n in self.tasks]

        if not agents:
            raise ValueError("No valid agents provided")
        if not tasks:
            raise ValueError("No valid tasks provided")

        process_type = Process.sequential if process == "sequential" else Process.hierarchical

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=process_type,
            verbose=verbose
        )

        self.crews[name] = crew
        return crew

    async def run_crew(self, name: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        """Execute a crew"""
        crew = self.crews.get(name)
        if not crew:
            raise ValueError(f"Crew '{name}' not found")

        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: crew.kickoff(inputs=inputs or {})
        )
        return str(result)

    async def create_research_crew(self, topic: str) -> str:
        """Create and run a pre-configured research crew"""
        # Create researcher agent
        await self.create_agent(
            name="researcher",
            role="Senior Research Analyst",
            goal=f"Research and analyze {topic} thoroughly",
            backstory="Expert researcher with deep analytical skills"
        )

        # Create writer agent
        await self.create_agent(
            name="writer",
            role="Content Writer",
            goal="Create comprehensive reports from research",
            backstory="Skilled writer who transforms research into clear content"
        )

        # Create tasks
        await self.create_task(
            name="research_task",
            description=f"Research {topic} and gather key information",
            agent_name="researcher",
            expected_output="Detailed research findings"
        )

        await self.create_task(
            name="write_task",
            description="Write a comprehensive report based on research",
            agent_name="writer",
            expected_output="Well-structured report",
            context=["research_task"]
        )

        # Create and run crew
        await self.create_crew(
            name="research_crew",
            agent_names=["researcher", "writer"],
            task_names=["research_task", "write_task"]
        )

        return await self.run_crew("research_crew")

    async def create_coding_crew(self, task_description: str) -> str:
        """Create and run a pre-configured coding crew"""
        # Create architect agent
        await self.create_agent(
            name="architect",
            role="Software Architect",
            goal="Design robust software solutions",
            backstory="Senior architect with 20 years of experience"
        )

        # Create developer agent
        await self.create_agent(
            name="developer",
            role="Senior Developer",
            goal="Implement high-quality code",
            backstory="Expert programmer in multiple languages"
        )

        # Create reviewer agent
        await self.create_agent(
            name="reviewer",
            role="Code Reviewer",
            goal="Ensure code quality and best practices",
            backstory="Quality-focused engineer"
        )

        # Create tasks
        await self.create_task(
            name="design_task",
            description=f"Design solution for: {task_description}",
            agent_name="architect",
            expected_output="Architecture design document"
        )

        await self.create_task(
            name="implement_task",
            description="Implement the designed solution",
            agent_name="developer",
            expected_output="Working code implementation",
            context=["design_task"]
        )

        await self.create_task(
            name="review_task",
            description="Review and improve the code",
            agent_name="reviewer",
            expected_output="Reviewed and improved code",
            context=["implement_task"]
        )

        # Create and run crew
        await self.create_crew(
            name="coding_crew",
            agent_names=["architect", "developer", "reviewer"],
            task_names=["design_task", "implement_task", "review_task"]
        )

        return await self.run_crew("coding_crew")

    def get_agents(self) -> List[str]:
        """Get list of created agents"""
        return list(self.agents.keys())

    def get_crews(self) -> List[str]:
        """Get list of created crews"""
        return list(self.crews.keys())
