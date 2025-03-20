import enum

from .base import BaseArticleWriter
from .notion import NotionArticleWriter


class WriterNotFoundException(Exception):
    pass


class WriterType(enum.StrEnum):
    notion = "notion"
    none = "none"

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return cls.none


MAPPING: dict[WriterType, type[BaseArticleWriter]] = {
    WriterType.notion: NotionArticleWriter,
}


def find_writer_class(writer_type: WriterType) -> type[BaseArticleWriter]:
    if writer_type not in MAPPING:
        raise WriterNotFoundException
    return MAPPING[writer_type]
