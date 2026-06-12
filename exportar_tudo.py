"""
exportar_tudo.py
----------------
Script standalone para exportar todos os dados do banco SQLite para CSV,
sem precisar abrir a interface gráfica.

Uso:
    python exportar_tudo.py             # exporta para ./exportacoes/
    python exportar_tudo.py --pasta C:/Users/Fulano/Desktop/powerbi

Os arquivos gerados usam separador ; e encoding UTF-8 BOM —
prontos para importar no Power BI e abrir no Excel sem configuração.
"""

import csv
import os
import sys
import time
import argparse
from datetime import datetime

# Garante que as importações do projeto funcionem independente de onde o script é chamado
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.vendas import listar_vendas, obter_detalhes_venda, listar_todos_itens_venda
from backend.insumos import listar_insumos
from backend.financeiro import listar_despesas, listar_recebimentos
from backend.produtos import listar_produtos, obter_ficha_tecnica
from backend.categorias import listar_categorias_produto, listar_categorias_financeiras
from backend.usuarios import listar_usuarios


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def ts_para_data(ts) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(ts)


def fmt_decimal(valor) -> str:
    """Formata float com vírgula decimal (padrão PT-BR para Power BI / Excel)."""
    try:
        return f"{float(valor):.2f}".replace(".", ",")
    except Exception:
        return str(valor)


def salvar_csv(caminho: str, cabecalho: list, linhas: list) -> int:
    """Escreve o CSV e retorna a quantidade de linhas gravadas."""
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(cabecalho)
        writer.writerows(linhas)
    return len(linhas)


def log(nome: str, qtd: int, caminho: str):
    print(f"  ✓  {nome:<30} {qtd:>7} linhas  →  {caminho}")


# ---------------------------------------------------------------------------
# Exportações individuais
# ---------------------------------------------------------------------------

def exportar_vendas(pasta: str):
    dados = listar_vendas()
    cabecalho = ["id_venda", "operador", "valor_total", "forma_pagamento", "data_venda"]
    linhas = [
        [
            v["id_venda"],
            v["usuario_nome"],
            fmt_decimal(v["valor_total"]),
            v["forma_pagamento"],
            ts_para_data(v["data_venda"]),
        ]
        for v in dados
    ]
    caminho = os.path.join(pasta, "vendas.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("vendas.csv", qtd, caminho)


def exportar_itens_venda(pasta: str):
    """
    Tabela fato detalhada — a mais importante para o Power BI.
    Cada linha = um produto dentro de uma venda.
    Usa uma única query com JOIN para máxima performance.
    """
    dados = listar_todos_itens_venda()
    cabecalho = [
        "id_venda", "data_venda", "operador", "forma_pagamento",
        "produto", "quantidade", "valor_unitario", "subtotal"
    ]
    linhas = [
        [
            i["id_venda"],
            ts_para_data(i["data_venda"]),
            i["usuario_nome"],
            i["forma_pagamento"],
            i["produto_nome"],
            fmt_decimal(i["quantidade"]),
            fmt_decimal(i["valor_unitario"]),
            fmt_decimal(i["subtotal"]),
        ]
        for i in dados
    ]
    caminho = os.path.join(pasta, "itens_venda.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("itens_venda.csv", qtd, caminho)


def exportar_estoque(pasta: str):
    dados = listar_insumos()
    cabecalho = [
        "id_insumo", "nome", "unidade_medida",
        "quantidade_atual", "estoque_minimo", "ultima_atualizacao"
    ]
    linhas = [
        [
            i["id_insumo"],
            i["nome"],
            i["unidade_medida"],
            fmt_decimal(i["quantidade_atual"]),
            fmt_decimal(i["estoque_minimo"]),
            ts_para_data(i["data_atualizacao"]),
        ]
        for i in dados
    ]
    caminho = os.path.join(pasta, "estoque.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("estoque.csv", qtd, caminho)


def exportar_produtos(pasta: str):
    dados = listar_produtos()
    cabecalho = ["id_produto", "nome", "categoria", "preco_venda", "custo_producao"]
    linhas = [
        [
            p["id"],
            p["nome"],
            p["categoria_nome"],
            fmt_decimal(p["preco_venda"]),
            fmt_decimal(p["custo_producao"]),
        ]
        for p in dados
    ]
    caminho = os.path.join(pasta, "produtos.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("produtos.csv", qtd, caminho)


def exportar_ficha_tecnica(pasta: str):
    """Exporta o vínculo produto ↔ insumo — útil para análise de custo no Power BI."""
    produtos = listar_produtos()
    cabecalho = ["id_produto", "produto_nome", "id_insumo", "insumo_nome", "unidade_medida", "quantidade_necessaria"]
    linhas = []
    for p in produtos:
        ficha = obter_ficha_tecnica(p["id"])
        for f in ficha:
            linhas.append([
                p["id"],
                p["nome"],
                f["id_insumo"],
                f["insumo_nome"],
                f["unidade_medida"],
                fmt_decimal(f["quantidade_necessaria"]),
            ])
    caminho = os.path.join(pasta, "ficha_tecnica.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("ficha_tecnica.csv", qtd, caminho)


def exportar_despesas(pasta: str):
    dados = listar_despesas()
    cabecalho = ["id_despesa", "descricao", "valor", "data", "categoria", "operador"]
    linhas = [
        [
            d["id"],
            d["descricao"],
            fmt_decimal(d["valor_despesa"]),
            ts_para_data(d["data_despesa"]),
            d["categoria_nome"],
            d["usuario_nome"],
        ]
        for d in dados
    ]
    caminho = os.path.join(pasta, "despesas.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("despesas.csv", qtd, caminho)


def exportar_recebimentos(pasta: str):
    dados = listar_recebimentos()
    cabecalho = ["id_recebimento", "descricao", "valor", "data", "categoria", "operador"]
    linhas = [
        [
            r["id"],
            r["descricao"],
            fmt_decimal(r["valor_recebido"]),
            ts_para_data(r["data_recebimento"]),
            r["categoria"],
            r["usuario_nome"],
        ]
        for r in dados
    ]
    caminho = os.path.join(pasta, "recebimentos.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("recebimentos.csv", qtd, caminho)


def exportar_categorias(pasta: str):
    cp = listar_categorias_produto()
    cabecalho = ["id", "nome", "descricao", "tipo"]
    linhas = [[c["id"], c["nome"], c.get("descricao", ""), "produto"] for c in cp]

    cf = listar_categorias_financeiras()
    for c in cf:
        linhas.append([c["id"], c["nome"], "", c["tipo_movimentacao"]])

    caminho = os.path.join(pasta, "categorias.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("categorias.csv", qtd, caminho)


def exportar_usuarios(pasta: str):
    """Exporta usuários sem a senha — seguro para incluir no Power BI."""
    dados = listar_usuarios()
    cabecalho = ["id_usuario", "nome", "login", "funcao"]
    linhas = [[u["id"], u["nome"], u["login"], u.get("funcao", "")] for u in dados]
    caminho = os.path.join(pasta, "usuarios.csv")
    qtd = salvar_csv(caminho, cabecalho, linhas)
    log("usuarios.csv", qtd, caminho)


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Exporta todos os dados do banco para CSV.")
    parser.add_argument(
        "--pasta",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "exportacoes"),
        help="Pasta de destino dos arquivos CSV (padrão: ./exportacoes/)"
    )
    args = parser.parse_args()
    pasta = args.pasta

    os.makedirs(pasta, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Exportação de Dados — Sistema Padaria")
    print(f"  Destino: {pasta}")
    print(f"{'='*60}\n")

    inicio = time.time()

    exportar_usuarios(pasta)
    exportar_categorias(pasta)
    exportar_produtos(pasta)
    exportar_ficha_tecnica(pasta)
    exportar_estoque(pasta)
    exportar_despesas(pasta)
    exportar_recebimentos(pasta)
    exportar_vendas(pasta)
    exportar_itens_venda(pasta)

    duracao = time.time() - inicio
    print(f"\n{'='*60}")
    print(f"  Exportação concluída em {duracao:.1f}s")
    print(f"  Arquivos salvos em: {pasta}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()