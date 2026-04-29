"""workshop_agent – Customizable AI agent framework for Bedrock AgentCore.

Entry point when called as ``python -m workshop_agent``.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("workshop-agent")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
