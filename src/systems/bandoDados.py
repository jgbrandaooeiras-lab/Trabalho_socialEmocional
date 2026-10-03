"""Compatibilidade para o módulo legado de banco de dados.

A implementação real está em banco_dados.py. Mantemos este alias para não
quebrar imports antigos e para evitar o diagnóstico de arquivos duplicados em
editores que ainda enxergam o nome antigo.
"""

from .banco_dados import *  # noqa: F401,F403

 