"""Integration modules for popular frameworks"""

try:
    from .langchain import LangChainWrapper

    __all__ = ["LangChainWrapper"]
except ImportError:
    # LangChain not installed
    __all__ = []
