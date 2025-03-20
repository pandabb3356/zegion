from pathlib import Path

from agents import Runner, trace
from loguru import logger

from .agents import AgentManager
from .tool import (
    extract_code_from_block,
)
from .writer import WriterType, find_writer_class


async def generate_doc(title: str, code_dir: Path, writer_type: WriterType):
    """
    Orchestrates the steps to generate and upload documentation:
    1. Reads and extracts code structure.
    2. Generates code summary.
    3. Formats the summary into Markdown.
    4. Converts Markdown to Notion blocks.
    5. Uploads the blocks to Notion.
    """

    agent_manager = AgentManager()
    agent_manager.register_agents()
    writer_class = find_writer_class(writer_type)

    with trace(f"Generating documentation for {title}..."):
        # Step 1: Read and extract code structure
        logger.info("【Step 1】Reading code and extracting structure...")
        result_reader = await Runner.run(
            agent_manager.get_code_reader(), input=str(code_dir)
        )
        extracted_json = result_reader.final_output  # JSON format code structure

        # Step 2: Generate code summary
        logger.info("【Step 2】Generating code summary...")
        result_summary = await Runner.run(
            agent_manager.get_code_understanding(), input=extracted_json
        )
        summary_text = result_summary.final_output

        # Step 3: Format into Markdown
        logger.info("【Step 3】Formatting into Markdown...")
        result_markdown = await Runner.run(
            agent_manager.get_doc_formatting(), input=summary_text
        )
        markdown_doc = extract_code_from_block(result_markdown.final_output)

        # Step 4: Start to write
        logger.info(f"【Step 4】Start to write by {writer_type.value.title()}...")
        article = writer_class.to_article(
            title=title,
            content=markdown_doc,
        )
        article_writer = writer_class.initialize()
        article_writer.write(article)
