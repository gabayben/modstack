from dataclasses import dataclass
from enum import StrEnum

class DeviceType(StrEnum):
    CPU = 'cpu'
    CUDA = 'cuda'
    MPS = 'mps'
    DISK = 'disk'

@dataclass
class Device:
    pass