import asyncio
import enum
import sys
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from zegion import WriterType, generate_doc
from zegion.config import Config, load_config

app = typer.Typer()


class LogLevel(enum.StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@app.command()
def write(
    src: Annotated[
        Path,
        typer.Option("--src", "-s", help="The path to the source code directory."),
    ],
    title: Annotated[
        str, typer.Option("--title", "-t", help="The title of the documentation.")
    ],
    writer_type: Annotated[
        WriterType,
        typer.Option("--writer", "-w", help="The type of documentation writer to use."),
    ],
    notion_api_key: Annotated[
        str | None, typer.Option(help="The Notion API key.")
    ] = None,
    notion_parent_page_id: Annotated[
        str | None, typer.Option(help="The Notion parent page ID.")
    ] = None,
    openai_model: Annotated[
        str, typer.Option(help="The default OpenAI model.")
    ] = "gpt-4o-mini",
    log_level: Annotated[
        LogLevel,
        typer.Option(help="The log level to use.", show_choices=True),
    ] = "WARNING",
):
    """Generate documentation from the source code directory and provided title.

    This command builds a configuration using the provided CLI options,
    loads the configuration, and then triggers the documentation generation process.
    """
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    c = Config.parse_obj(
        {
            "notion": {
                "api_key": notion_api_key,
                "parent_page_id": notion_parent_page_id,
            },
            "openai": {
                "default_model": openai_model,
            },
        },
    )
    load_config(c)
    asyncio.run(
        generate_doc(
            title=title,
            code_dir=src,
            writer_type=writer_type,
        )
    )


def run():
    app()
