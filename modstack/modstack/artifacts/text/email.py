from abc import ABC
import datetime as dt
from typing import Final, Optional, Union, override

from pydantic import PrivateAttr

from modstack.artifacts import Artifact, ArtifactMetadata, ArtifactType
from modstack.artifacts.text.base import TextBase

class EmailAddress(TextBase):
    """A text artifact for capturing email addresses."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_ADDRESS

class EmailPart(TextBase, ABC):
    """An email part is a section of the email."""

class EmailName(EmailPart, ABC):
    """Base artifact for capturing name from within an email."""

    _email_name: Final[str] = PrivateAttr()
    _email_text: Final[str] = PrivateAttr()

    def __init__(
        self,
        email_name: str,
        email_text: str,
        datestamp: Optional[dt.datetime] = None,
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        metadata = (
            ArtifactMetadata(**{**metadata, 'datastamp': datestamp})
            if datestamp
            else metadata
        )
        super().__init__(
            content=f'{email_name}: {email_text}',
            metadata=metadata,
            **kwargs
        )
        self._email_name = email_name
        self._email_text = email_text

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self.metadata.datestamp:
            return (
                self._email_name == other._email_name
                and self._email_text == other._email_text
                and self.metadata.datestamp == other.metadata.datestamp
            )
        return (
            self._email_name == other._email_name
            and self._email_text == other._email_text
        )

class EmailSender(EmailName):
    """A text artifact for capturing the sender information of an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_SENDER

class EmailRecipient(EmailName):
    """A text artifact for capturing the recipient information of an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_RECIPIENT

class EmailSubject(EmailPart):
    """A text artifact for capturing the subject information of an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_SUBJECT

class EmailMetadata(EmailName):
    """A text artifact for capturing header metadata of an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_METADATA

class ReceivedInfo(EmailName):
    """A text artifact for capturing header information of an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.RECEIVED_INFO

class EmailAttachment(EmailName):
    """A text artifact for capturing the attachment name in an email."""

    @property
    @override
    def category(self) -> str:
        return ArtifactType.EMAIL_ATTACHMENT

class BodyText(EmailPart):
    """
    BodyText is an artifact consisting of multiple, well-formulated sentences.
    This excludes artifacts such as titles, headers, footers, and captions.
    It is the body of an email.
    """

    @property
    @override
    def category(self) -> str:
        return ArtifactType.BODY_TEXT

    def __init__(
        self,
        sentences: list[Union[str, Artifact]],
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        super().__init__(
            content=' '.join([str(s) for s in sentences]),
            metadata=metadata,
            **kwargs
        )