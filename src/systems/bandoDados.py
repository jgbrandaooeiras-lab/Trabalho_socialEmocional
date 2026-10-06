"""Compatibilidade para o módulo legado de banco de dados.

A implementação real está em banco_dados.py. Alias para compatibilidade de código legado e evitar problemas de circular imports.
"""

from .banco_dados import *  # noqa: F401,F403

 