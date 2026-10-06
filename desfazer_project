"""Recria os arquivos do projeto a partir do projeto_completo.txt.

Uso (na pasta onde está o TXT):
    python desfazer_projeto.py                          # recria na pasta atual
    python desfazer_projeto.py projeto_completo.txt pasta_destino

Arquivos que já existem são sobrescritos: faça backup (ou commit) antes.
As imagens dos escudos não vão no TXT; elas devem ficar em assets/escudos/.
"""
import re
import sys
from pathlib import Path

CABECALHO = re.compile(r"^===== (.+) =====\s*$")


def _criar_pasta_se_necessario(pasta: Path):
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        if not pasta.exists() or not pasta.is_dir():
            raise


def main():
    txt = Path(sys.argv[1] if len(sys.argv) > 1 else "projeto_completo.txt")
    destino = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()

    arquivos, atual = {}, None
    for linha in txt.read_text(encoding="utf-8").splitlines(keepends=True):
        casou = CABECALHO.match(linha)
        if casou:
            atual = casou.group(1).strip().replace("\\", "/")
            arquivos[atual] = []
        elif atual is not None:
            arquivos[atual].append(linha)

    for caminho, linhas in arquivos.items():
        alvo = (destino / caminho).resolve()
        try:
            alvo.relative_to(destino)
        except ValueError:
            print(f"IGNORADO (caminho inválido): {caminho}")
            continue

        if not linhas:
            _criar_pasta_se_necessario(alvo)
            print(f"pasta: {caminho}")
            continue

        _criar_pasta_se_necessario(alvo.parent)
        existia = alvo.exists()
        # tira a linha em branco que separa um arquivo do próximo no TXT
        conteudo = "".join(linhas).rstrip("\n")
        alvo.write_text(conteudo + "\n" if conteudo else "", encoding="utf-8", newline="\n")
        print(("atualizado: " if existia else "criado:     ") + caminho)

    print(f"\n{len(arquivos)} entradas restauradas em {destino}")


if __name__ == "__main__":
    main()
