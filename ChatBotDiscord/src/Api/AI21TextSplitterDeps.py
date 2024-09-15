import logging
from typing import (
    Any,
    Iterable,
    List,
    Optional,
)

from ai21.models import DocumentType
from langchain_core.pydantic_v1 import SecretStr
from langchain_text_splitters import TextSplitter
from .AI21BaseDeps import AI21Base

logger = logging.getLogger(__name__)


class AI21SemanticTextSplitter(TextSplitter):
    """Splitting text into coherent and readable units,
    based on distinct topics and lines
    """

    def __init__(
        self,
        chunk_size: int = 0,
        chunk_overlap: int = 0,
        client: Optional[Any] = None,
        api_key: Optional[SecretStr] = None,
        api_host: Optional[str] = None,
        timeout_sec: Optional[float] = None,
        num_retries: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )

        self._segmentation = AI21Base(
            client=client,
            api_key=api_key,
            api_host=api_host,
            timeout_sec=timeout_sec,
            num_retries=num_retries,
        ).client.segmentation

    def split_text(self, source: str) -> List[str]:
        """Split text into multiple components.

        Args:
            source: Specifies the text input for text segmentation
        """
        response = self._segmentation.create(
            source=source, source_type=DocumentType.TEXT
        )

        segments = [segment.segment_text for segment in response.segments]

        if self._chunk_size > 0:
            return self._merge_splits_no_seperator(segments)

        return segments
