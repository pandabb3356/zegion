from functools import partialmethod

from agents import Agent

from zegion.config import get_default_openai_model
from zegion.tool import read_code_directory


class AgentName:
    """Enum for different types of agents."""

    CODE_READER = "Code Reader Agent"
    CODE_UNDERSTANDING = "Code Understanding Agent"
    DOCUMENTATION_FORMATTING = "Documentation Formatting Agent"


class AgentManager:
    """Manager for handling and generating various agents.

    This class allows for the registration, retrieval, and creation of agents, as well as registering default agents.

    Attributes:
        agents (dict): A dictionary mapping agent names to their Agent instances.
    """

    def __init__(self):
        """Initializes the AgentManager with an empty registry and registers default agents."""
        self.agents = {}

    def _register_agents(self, agent_list: list[Agent]):
        """Registers an Agent with the manager.

        Args:
            agent_list (list[Agent]): A list of Agent instances to be registered.
        """
        for agent in agent_list:
            self.agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent:
        """Retrieves an Agent by its name.

        Args:
            name (str): The name of the agent to retrieve.

        Returns:
            Agent: The corresponding Agent instance if found; otherwise, None.
        """
        return self.agents.get(name)

    def register_agents(self):
        """Registers the default agents for code reading, understanding, and documentation formatting."""

        model_name = get_default_openai_model()

        # Code Reader Agent: Reads and parses the code directory.
        code_reader_agent = Agent(
            name=AgentName.CODE_READER,
            model=model_name,
            instructions=(
                "Use the provided tools to read all Python files from the specified directory, "
                "extract function and class definitions, parameters, and docstrings, and return the results in JSON format."
            ),
            tools=[read_code_directory],
        )

        # Code Understanding Agent: Generates detailed summaries and explains the overall flow.
        code_understanding_agent = Agent(
            name=AgentName.CODE_UNDERSTANDING,
            model=model_name,
            instructions=(
                "You are an expert in code analysis. Please parse the provided JSON structure, and generate detailed summaries for each file. "
                "Your explanation should include a list of functions (with parameters and descriptions) and classes with their method summaries, "
                "as well as a comprehensive explanation of the overall code flow. Describe how the system processes the code from reading to documentation generation, "
                "and explain the core logic and design decisions behind it. "
                "Additionally, include a Mermaid flowchart that visually represents the main process flow, showing how each module interacts."
            ),
        )

        # Documentation Formatting Agent: Converts summaries to Markdown format.
        doc_formatting_agent = Agent(
            name=AgentName.DOCUMENTATION_FORMATTING,
            model=model_name,
            instructions=(
                "You are a professional technical writer. Please convert the following code summaries into a Markdown format, "
                "using appropriate headers and bullet points to organize the content."
            ),
        )

        # Register the default agents.
        self._register_agents(
            [
                code_reader_agent,
                code_understanding_agent,
                doc_formatting_agent,
            ]
        )

    get_code_reader = partialmethod(get_agent, name=AgentName.CODE_READER)
    get_code_understanding = partialmethod(get_agent, name=AgentName.CODE_UNDERSTANDING)
    get_doc_formatting = partialmethod(
        get_agent, name=AgentName.DOCUMENTATION_FORMATTING
    )
