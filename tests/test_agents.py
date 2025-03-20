from unittest import mock

from zegion.agents import AgentManager, AgentName
from zegion.tool import read_code_directory


@mock.patch("zegion.agents.get_default_openai_model")
def test_register_agents(mock_get_default_openai_model):
    mock_get_default_openai_model.return_value = dummy_model = "dummy-model"

    manager = AgentManager()

    # Verify that the agents dictionary is initially empty.
    assert manager.agents == {}

    # Register the default agents.
    manager.register_agents()

    # Verify that the three default agents are registered.
    assert AgentName.CODE_READER in manager.agents
    assert AgentName.CODE_UNDERSTANDING in manager.agents
    assert AgentName.DOCUMENTATION_FORMATTING in manager.agents

    # Verify properties of the Code Reader Agent.
    code_reader = manager.agents[AgentName.CODE_READER]
    # The agent's model should match the dummy model.
    assert code_reader.model == dummy_model
    # The tool list should include the read_code_directory tool.
    assert read_code_directory in code_reader.tools
    # Instructions should mention "read all Python files".
    assert "read all Python files" in code_reader.instructions

    # Verify properties of the Code Understanding Agent.
    code_understanding = manager.agents[AgentName.CODE_UNDERSTANDING]
    # The agent's model should match the dummy model.
    assert code_understanding.model == dummy_model
    # Instructions should mention "code analysis".
    assert "code analysis" in code_understanding.instructions

    # Verify properties of the Documentation Formatting Agent.
    doc_formatting = manager.agents[AgentName.DOCUMENTATION_FORMATTING]
    # The agent's model should match the dummy model.
    assert doc_formatting.model == dummy_model
    # Instructions should mention "Markdown".
    assert "Markdown" in doc_formatting.instructions


def test_get_agent_partial_methods():
    manager = AgentManager()
    manager.register_agents()

    # Retrieve agents using the partial methods.
    code_reader = manager.get_code_reader()
    code_understanding = manager.get_code_understanding()
    doc_formatting = manager.get_doc_formatting()

    # Verify that the partial method returns the same agent as the generic get_agent method.
    assert code_reader is manager.get_agent(AgentName.CODE_READER)
    assert code_understanding is manager.get_agent(AgentName.CODE_UNDERSTANDING)
    assert doc_formatting is manager.get_agent(AgentName.DOCUMENTATION_FORMATTING)
