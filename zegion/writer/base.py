import abc
import enum

from pydantic import BaseModel


class Article(BaseModel):
    title: str
    content: str


class WriteStatus(enum.StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class WrittenResult(BaseModel):
    status: WriteStatus
    error_message: str | None = None


class ArticleWriterOptions(BaseModel):
    # TODO: Add more options
    pass


class BaseArticleWriter(abc.ABC):
    def __init__(self, **kwargs):
        self._options = ArticleWriterOptions.parse_obj(kwargs.get("options") or {})

    @abc.abstractmethod
    def write(self, article: Article):
        raise NotImplementedError

    @classmethod
    def initialize(cls, **kwargs) -> "BaseArticleWriter":
        return cls(**kwargs)

    @classmethod
    def to_article(cls, **kwargs) -> Article:
        return Article(**kwargs)
