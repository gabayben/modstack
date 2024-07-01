from email.message import Message as EmailMessage
import re

from modstack.artifacts import Artifact, ArtifactSource
from modstack.data import extract_email_addresses
from modstack.core import module
from modstack.utils.regex import EMAIL_ADDRESS_REGEX

@module
def email_partitioner(source: ArtifactSource, **kwargs) -> list[Artifact]:
    pass

def _partition_email_header(message: EmailMessage) -> list[Artifact]:
    pass

def _parse_email_address(data: str) -> tuple[str, str]:
    name = re.split(f'<{EMAIL_ADDRESS_REGEX}>', data.lower())[0].title().strip()
    email_address = extract_email_addresses(data)[0]
    return name, email_address