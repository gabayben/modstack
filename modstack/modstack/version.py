from importlib import metadata

try:
    __version__ = str(metadata.version('modstack'))
except metadata.PackageNotFoundError:
    __version__ = 'main'