from email.message import Message as EmailMessage
import re

from modstack.artifacts import Artifact
from modstack.artifacts.layout import Element
from modstack.data.transform import PartitionOptions, extract_email_addresses
from modstack.modules import Modules
from modstack.utils.regex import EMAIL_ADDRESS_REGEX

class EmailPartitioner(Modules.Sync[Artifact, list[Element], PartitionOptions]):
    def _invoke(self, email: Artifact, **kwargs) -> list[Element]:
        pass

def _partition_email_header(artifact: EmailMessage) -> list[Element]:
    pass

def _parse_email_address(data: str) -> tuple[str, str]:
    name = re.split(f'<{EMAIL_ADDRESS_REGEX}>', data.lower())[0].title().strip()
    email_address = extract_email_addresses(data)[0]
    return name, email_address