from zegion.config import (
    Config,
    NotionConfig,
    OpenAIConfig,
    get_default_openai_model,
    get_notion_config,
    get_openai_config,
    load_config,
)


def test_default_openai_model():
    default_model = get_default_openai_model()
    assert default_model == "gpt-4o-mini"


def test_get_openai_config_defaults():
    openai_config = get_openai_config()
    assert openai_config.default_model == "gpt-4o-mini"


def test_get_notion_config_defaults():
    notion_config = get_notion_config()
    assert notion_config.api_key == ""
    assert notion_config.parent_page_id == ""


def test_load_config_merging():
    new_config = Config(
        notion=NotionConfig(api_key="new_api_key", parent_page_id="new_parent_id"),
        openai=OpenAIConfig(default_model="gpt-3.5"),
    )
    merged_config = load_config(new_config)

    assert merged_config.notion.api_key == "new_api_key"
    assert merged_config.notion.parent_page_id == "new_parent_id"
    assert merged_config.openai.default_model == "gpt-3.5"
