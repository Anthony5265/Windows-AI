"""
LangChain Integration for Windows AI
Full integration with LangChain ecosystem
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChainConfig:
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    streaming: bool = True

class LangChainManager:
    """Manages LangChain integration for Windows AI"""

    def __init__(self):
        self.chains: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.tools: List[Any] = []
        self.memory_stores: Dict[str, Any] = {}
        self.vector_stores: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LangChain with all components"""
        if self._initialized:
            return

        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from langchain_anthropic import ChatAnthropic
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
            from langchain.agents import AgentExecutor, create_react_agent
            from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
            from langchain_community.utilities import WikipediaAPIWrapper

            # Initialize default LLMs
            self.llms = {
                'openai': ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7),
                'anthropic': ChatAnthropic(model="claude-3-sonnet-20240229"),
                'google': ChatGoogleGenerativeAI(model="gemini-pro"),
            }

            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings()

            # Initialize default tools
            self.tools = [
                DuckDuckGoSearchRun(),
                WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
            ]

            # Initialize memory
            self.memory_stores['default'] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

            self._initialized = True
            logger.info("LangChain integration initialized successfully")

        except ImportError as e:
            logger.warning(f"LangChain not fully available: {e}")
            self._initialized = False

    async def create_chain(
        self,
        name: str,
        chain_type: str = "conversation",
        llm_provider: str = "openai",
        tools: Optional[List[Any]] = None,
        memory: bool = True
    ) -> Any:
        """Create a new LangChain chain"""
        from langchain.chains import ConversationChain, LLMChain
        from langchain.prompts import PromptTemplate, ChatPromptTemplate

        llm = self.llms.get(llm_provider, self.llms['openai'])

        if chain_type == "conversation":
            chain = ConversationChain(
                llm=llm,
                memory=self.memory_stores.get('default') if memory else None,
                verbose=True
            )
        elif chain_type == "qa":
            from langchain.chains import RetrievalQA
            chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self._get_retriever()
            )
        else:
            prompt = PromptTemplate(
                input_variables=["input"],
                template="{input}"
            )
            chain = LLMChain(llm=llm, prompt=prompt)

        self.chains[name] = chain
        return chain

    async def create_agent(
        self,
        name: str,
        agent_type: str = "react",
        llm_provider: str = "openai",
        tools: Optional[List[Any]] = None
    ) -> Any:
        """Create a LangChain agent"""
        from langchain.agents import AgentExecutor, create_react_agent, create_openai_functions_agent
        from langchain import hub

        llm = self.llms.get(llm_provider, self.llms['openai'])
        agent_tools = tools or self.tools

        if agent_type == "react":
            prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, agent_tools, prompt)
        elif agent_type == "openai_functions":
            prompt = hub.pull("hwchase17/openai-functions-agent")
            agent = create_openai_functions_agent(llm, agent_tools, prompt)
        else:
            prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, agent_tools, prompt)

        executor = AgentExecutor(
            agent=agent,
            tools=agent_tools,
            verbose=True,
            handle_parsing_errors=True
        )

        self.agents[name] = executor
        return executor

    async def run_chain(self, name: str, input_text: str) -> str:
        """Run a chain by name"""
        chain = self.chains.get(name)
        if not chain:
            raise ValueError(f"Chain '{name}' not found")

        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: chain.invoke({"input": input_text})
        )
        return result.get("output", result.get("text", str(result)))

    async def run_agent(self, name: str, input_text: str) -> str:
        """Run an agent by name"""
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")

        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: agent.invoke({"input": input_text})
        )
        return result.get("output", str(result))

    async def create_rag_chain(
        self,
        name: str,
        documents: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Any:
        """Create a RAG (Retrieval Augmented Generation) chain"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain.chains import RetrievalQA

        # Split documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        texts = splitter.create_documents(documents)

        # Create vector store
        vector_store = FAISS.from_documents(texts, self.embeddings)
        self.vector_stores[name] = vector_store

        # Create RAG chain
        chain = RetrievalQA.from_chain_type(
            llm=self.llms['openai'],
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4})
        )

        self.chains[name] = chain
        return chain

    def _get_retriever(self):
        """Get default retriever"""
        if self.vector_stores:
            return list(self.vector_stores.values())[0].as_retriever()
        return None

    async def add_custom_tool(self, tool: Any):
        """Add a custom tool to the toolkit"""
        self.tools.append(tool)

    def get_available_models(self) -> List[str]:
        """Get list of available LLM providers"""
        return list(self.llms.keys())

    def get_chains(self) -> List[str]:
        """Get list of created chains"""
        return list(self.chains.keys())

    def get_agents(self) -> List[str]:
        """Get list of created agents"""
        return list(self.agents.keys())
