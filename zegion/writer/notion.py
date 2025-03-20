"""
reference: https://github.com/markomanninen/md2notion/blob/main/md2notionpage/core.py
"""

import re

from loguru import logger
from notion_client import Client as NotionClient
from notion_client.client import ClientOptions

from zegion.config import NotionConfig, get_notion_config
from zegion.writer.base import Article, BaseArticleWriter
from zegion.writer.exception import WriterException


class NotionWriterException(WriterException):
    pass


class NoBlockException(NotionWriterException):
    pass


class CreatePageException(NotionWriterException):
    pass


class AppendBlocksException(NotionWriterException):
    pass


class InlineFormatterPlugin:
    """Base class for inline formatting plugins."""

    def pattern(self):
        """Return the regex pattern that this plugin handles."""
        raise NotImplementedError

    def replace(self, match):
        """Return the corresponding Notion rich text object for a regex match."""
        raise NotImplementedError


class GenericInlinePlugin(InlineFormatterPlugin):
    """
    Generic inline formatting plugin that allows you to specify the regex pattern
    and the corresponding annotations.

    Args:
        pattern (str): The regex pattern to match.
        annotations (dict): Notion text annotations, e.g. {"bold": True, "italic": False, ...}.
        content_groups (tuple): Tuple of group indices to try in order to extract the content.
    """

    def __init__(self, pattern, annotations, content_groups):
        self._pattern = pattern
        self._annotations = annotations
        self._content_groups = content_groups

    def pattern(self):
        return self._pattern

    def replace(self, match):
        content = None
        for idx in self._content_groups:
            content = match.group(idx)
            if content:
                break
        return {
            "type": "text",
            "text": {"content": content, "link": None},
            "annotations": self._annotations.copy(),
        }


class LinkPlugin(InlineFormatterPlugin):
    """Plugin for handling Markdown links."""

    def pattern(self):
        return r"\[(.+?)\]\((.+?)\)"

    def replace(self, match):
        text_content = match.group(1)
        url = match.group(2)
        return {
            "type": "text",
            "text": {"content": text_content, "link": {"url": url}},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
        }


class NotionMarkdownConverter:
    inline_plugins = [
        # Bold + Italic (without code)
        GenericInlinePlugin(
            pattern=r"(__\*(.+?)\*__)|(\*\*_(.+?)_\*\*)",
            annotations={
                "bold": True,
                "italic": True,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            content_groups=(2, 4),
        ),
        # Bold with code formatting (if needed)
        GenericInlinePlugin(
            pattern=r"(\*\*(.+?)\*\*)|(__(.+?)__)",
            annotations={
                "bold": True,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": True,
                "color": "default",
            },
            content_groups=(2, 4),
        ),
        # Bold (plain, without code)
        GenericInlinePlugin(
            pattern=r"(\*\*(.+?)\*\*)|(__(.+?)__)",
            annotations={
                "bold": True,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            content_groups=(2, 4),
        ),
        # Italic
        GenericInlinePlugin(
            pattern=r"(\*(.+?)\*)|(_(.+?)_)",
            annotations={
                "bold": False,
                "italic": True,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            content_groups=(2, 4),
        ),
        # Code
        GenericInlinePlugin(
            pattern=r"`(.+?)`",
            annotations={
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": True,
                "color": "default",
            },
            content_groups=(1,),
        ),
        # Link handling
        LinkPlugin(),
    ]

    def __init__(self):
        pass

    def _replace_part(self, parts, pattern, replace_function):
        """
        Helper method to process parts of text that match a given pattern,
        replacing them using the provided replace function.
        """
        new_parts = []
        for part in parts:
            if isinstance(part, str):
                matches = list(re.finditer(pattern, part))
                prev_end = 0
                for match in matches:
                    if prev_end != match.start():
                        new_parts.append(part[prev_end : match.start()])
                    new_parts.append(replace_function(match))
                    prev_end = match.end()
                new_parts.append(part[prev_end:])
            else:
                new_parts.append(part)
        return new_parts

    def process_inline_formatting(self, text):
        """
        Process inline Markdown formatting using registered plugins and convert it
        into a list of Notion rich text objects.
        """
        text_parts = [text]
        for plugin in self.inline_plugins:
            text_parts = self._replace_part(
                text_parts, plugin.pattern(), plugin.replace
            )
        result = []
        for part in text_parts:
            if isinstance(part, str) and part:
                result.append(
                    {
                        "type": "text",
                        "text": {"content": part, "link": None},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default",
                        },
                    }
                )
            elif isinstance(part, dict):
                result.append(part)
        return result

    def convert_markdown_table_to_latex(self, text):
        """
        Converts a Markdown table to a LaTeX formatted string.
        """
        lines = text.split("\n")
        # Remove header divider if exists.
        if len(lines) > 1 and re.match(r"\|\s*-+\s*\|", lines[1]):
            lines.pop(1)
        table_content = ""
        cells = []
        for row in lines:
            cells = re.findall(r"(?<=\|)(.*?)(?=\|)", row)
            new_row = " & ".join([f"\\textsf{{{cell.strip()}}}" for cell in cells])
            table_content += new_row + " \\\\\\hline\n"
        columns = len(cells)
        table_column = "|c" * columns + "|"
        return f"\\def\\arraystretch{{1.4}}\\begin{{array}}{{{table_column}}}\\hline\n{table_content}\\end{{array}}"

    def parse_markdown_to_notion_blocks(self, markdown):
        """
        Parses Markdown text and converts it into a list of Notion blocks.
        """
        # Process code blocks
        code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
        code_blocks = {}

        def replace_code(match):
            idx = len(code_blocks)
            language = match.group(1) or "plain text"
            content = match.group(2)
            code_blocks[idx] = (language.strip(), content.strip())
            return f"CODE_BLOCK_{idx}"

        markdown = code_block_pattern.sub(replace_code, markdown)

        # Process LaTeX blocks
        latex_block_pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
        latex_blocks = {}

        def replace_latex(match):
            idx = len(latex_blocks)
            latex_blocks[idx] = match.group(1).strip()
            return f"LATEX_BLOCK_{idx}"

        markdown = latex_block_pattern.sub(replace_latex, markdown)

        lines = markdown.split("\n")
        blocks = []
        current_table = []
        in_table = False
        indented_code = []

        for line in lines:
            # Table handling
            if re.match(r"\|\s*[^|]+\s*\|", line):
                current_table.append(line)
                in_table = True
                continue
            elif in_table and not re.match(r"\|\s*[^|]+\s*\|", line):
                in_table = False
                table_md = "\n".join(current_table)
                latex_table = self.convert_markdown_table_to_latex(table_md)
                blocks.append(
                    {"type": "equation", "equation": {"expression": latex_table}}
                )
                current_table = []

            # Handle indented code (4 spaces)
            if line.startswith("    "):
                indented_code.append(line[4:])
                continue
            else:
                if indented_code:
                    code_text = "\n".join(indented_code)
                    blocks.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": "plain text",
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {"content": code_text, "link": None},
                                    }
                                ],
                            },
                        }
                    )
                    indented_code = []

            # Heading handling
            heading_match = re.match(r"^(#{1,3})\s+(.*)", line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                block_type = f"heading_{level}"
                blocks.append(
                    {
                        "object": "block",
                        "type": block_type,
                        block_type: {
                            "rich_text": self.process_inline_formatting(content)
                        },
                    }
                )
                continue

            # Horizontal rule
            if re.match(r"^-{3,}$", line):
                blocks.append({"object": "block", "type": "divider", "divider": {}})
                continue

            # Blockquote handling
            if re.match(r"^> (.*)", line):
                quote_content = re.match(r"^> (.*)", line).group(1)
                blocks.append(
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": self.process_inline_formatting(quote_content)
                        },
                    }
                )
                continue

            # Process replaced code blocks
            if line.startswith("CODE_BLOCK_"):
                idx = int(line.replace("CODE_BLOCK_", ""))
                language, code_text = code_blocks.get(idx, ("plain text", ""))
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": language,
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": code_text, "link": None},
                                }
                            ],
                        },
                    }
                )
                continue

            # Process LaTeX blocks
            if line.startswith("LATEX_BLOCK_"):
                idx = int(line.replace("LATEX_BLOCK_", ""))
                latex_expr = latex_blocks.get(idx, "")
                blocks.append(
                    {
                        "object": "block",
                        "type": "equation",
                        "equation": {"expression": latex_expr},
                    }
                )
                continue

            # Image handling
            image_match = re.search(r"!\[(.*?)\]\((.*?)\)", line)
            if image_match:
                caption, url = image_match.groups()
                image_block = {
                    "object": "block",
                    "type": "image",
                    "image": {"external": {"url": url}},
                }
                if caption:
                    image_block["image"]["caption"] = [
                        {"type": "text", "text": {"content": caption, "link": None}}
                    ]
                blocks.append(image_block)
                continue

            # Remaining text as paragraph
            if line.strip():
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self.process_inline_formatting(line)
                        },
                    }
                )

        # Finalize any pending tables or indented code
        if current_table:
            table_md = "\n".join(current_table)
            latex_table = self.convert_markdown_table_to_latex(table_md)
            blocks.append({"type": "equation", "equation": {"expression": latex_table}})
        if indented_code:
            code_text = "\n".join(indented_code)
            blocks.append(
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "language": "plain text",
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": code_text, "link": None},
                            }
                        ],
                    },
                }
            )
        return blocks

    def parse_md(self, markdown_text):
        """
        Parses Markdown text into Notion blocks.
        """
        return self.parse_markdown_to_notion_blocks(markdown_text.strip())


def convert_markdown_to_notion_blocks(markdown_text: str):
    """
    Converts Markdown text into Notion blocks.
    """
    return NotionMarkdownConverter().parse_md(markdown_text)


class NotionArticleWriter(BaseArticleWriter):
    """
    A writer class that converts article content into Notion blocks and writes them
    to a new Notion page using the Notion API.

    Attributes:
        notion_config (NotionConfig): Configuration object holding Notion API settings.
        notion_client (NotionClient): Client instance for interacting with the Notion API.
    """

    notion_config: NotionConfig

    def __init__(self, **kwargs):
        """
        Initializes a new NotionArticleWriter instance.

        Retrieves the Notion configuration and initializes the Notion client using the
        API key from the configuration.
        """
        super().__init__(**kwargs)

        self.notion_config = (
            get_notion_config()
        )  # Retrieve Notion configuration settings
        self.notion_client = NotionClient(
            options=ClientOptions(auth=self.notion_config.api_key)
        )

    @property
    def api_key(self) -> str | None:
        """
        Returns:
            str | None: The API key from the Notion configuration, or None if not set.
        """
        return self.notion_config.api_key

    @property
    def parent_page_id(self) -> str | None:
        """
        Returns:
            str | None: The parent page ID from the Notion configuration, or None if not set.
        """
        return self.notion_config.parent_page_id

    @staticmethod
    def _chunk_blocks(blocks: list, chunk_size: int = 100):
        """
        Yields successive chunks of blocks.

        Args:
            blocks (list): A list of Notion blocks.
            chunk_size (int, optional): Number of blocks per chunk. Defaults to 100.

        Yields:
            list: A chunk of blocks of size chunk_size.
        """
        for i in range(0, len(blocks), chunk_size):
            yield blocks[i : i + chunk_size]

    def _create_page(self, title: str, blocks: list) -> str | None:
        """
        Creates a Notion page with the first chunk of blocks.

        This method creates a new Notion page using the first 100 blocks and returns the page ID.

        Args:
            title (str): The title of the new Notion page.
            blocks (list): A list of Notion blocks to include in the new page.

        Returns:
            str | None: The ID of the created Notion page if successful, otherwise None.
        """
        first_chunk = next(self._chunk_blocks(blocks), [])
        # Prepare payload for page creation with a default title
        payload = {
            "parent": {"page_id": self.parent_page_id},
            "properties": {"title": [{"text": {"content": title}}]},
            "children": first_chunk,
        }

        response = None
        try:
            response = self.notion_client.pages.create(**payload)
        except Exception as e:
            logger.error(
                f"[{self.__class__.__name__}] Failed to create Notion page. Response: {response}"
            )
            raise CreatePageException from e
        return response.get("id")

    def _append_blocks(self, page_id: str, blocks: list) -> bool:
        """
        Appends remaining blocks to an existing Notion page in chunks.

        After the initial page creation, this method appends additional blocks to the page
        in chunks of 100 blocks.

        Args:
            page_id (str): The ID of the Notion page to update.
            blocks (list): A list of Notion blocks to append.

        Returns:
            bool: True if all blocks are appended successfully, False otherwise.
        """
        for chunk in self._chunk_blocks(blocks, chunk_size=100):
            payload = {"children": chunk}
            response = None
            try:
                response = self.notion_client.blocks.children.append(
                    block_id=page_id, **payload
                )
            except Exception as e:
                logger.error(
                    f"[{self.__class__.__name__}] Failed to append blocks. Response: {response}"
                )
                raise AppendBlocksException from e
        # Log error if appending fails for any chunk
        return True

    def write(self, article: Article):
        """
        Converts article content into Notion blocks and writes them to a new Notion page.

        The method converts the article's markdown content into Notion blocks, creates a new
        page with the first 100 blocks, and appends any additional blocks if necessary.

        Args:
            article (Article): An Article object containing title and content.

        Returns:
            WrittenResult: The result of the write operation indicating success or failure.
        """
        blocks = convert_markdown_to_notion_blocks(article.content)
        # Warn if conversion yields no blocks
        if not blocks:
            raise NoBlockException

        page_id = self._create_page(article.title, blocks)
        # Check if page creation was successful
        if not page_id:
            raise CreatePageException

        # Append remaining blocks if there are more than 100
        if len(blocks) > 100 and not self._append_blocks(page_id, blocks[100:]):
            raise AppendBlocksException

        logger.debug(
            f"[{self.__class__.__name__}] Successfully created Notion page with ID: {page_id}"
        )
