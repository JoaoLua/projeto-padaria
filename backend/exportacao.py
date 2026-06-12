import csv
import os
import time
from datetime import datetime
from tkinter import filedialog, messagebox

from backend.vendas import listar_vendas, obter_detalhes_venda
from backend.insumos import listar_insumos
from backend.financeiro import listar_despesas, listar_recebimentos
from backend.produtos import listar_produtos, obter_ficha_tecnica


def _timestamp_para_data(ts: int) -> str:
    """Converte Unix Timestamp para string legível no formato dd/mm/aaaa hh:mm."""
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(ts)


def _abrir_dialogo_salvar(titulo: str, nome_sugerido: str) -> str | None:
    """
    Abre o diálogo nativo de salvar arquivo do SO e retorna o caminho
    escolhido pelo usuário, ou None se cancelado.
    """
    caminho = filedialog.asksaveasfilename(
        title=titulo,
        defaultextension=".csv",
        initialfile=nome_sugerido,
        filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")]
    )
    return caminho if caminho else None


def _escrever_csv(caminho: str, cabecalho: list[str], linhas: list[list]) -> None:
    """
    Escreve o arquivo CSV com separador ponto-e-vírgula (padrão PT-BR)
    e encoding UTF-8-BOM para compatibilidade com Excel e Power BI.
    """
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(cabecalho)
        writer.writerows(linhas)


# ---------------------------------------------------------------------------
# Funções públicas de exportação — chamadas diretamente pelas views
# ---------------------------------------------------------------------------

def exportar_vendas() -> None:
    """
    Exporta o histórico de vendas (cabeçalhos) para CSV.
    Cada linha representa uma venda com: ID, Operador, Valor Total,
    Forma de Pagamento e Data/Hora.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Vendas — Escolha onde salvar",
        nome_sugerido=f"vendas_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        dados = listar_vendas()
        cabecalho = ["id_venda", "operador", "valor_total", "forma_pagamento", "data_venda"]
        linhas = [
            [
                v["id_venda"],
                v["usuario_nome"],
                f"{v['valor_total']:.2f}".replace(".", ","),
                v["forma_pagamento"],
                _timestamp_para_data(v["data_venda"])
            ]
            for v in dados
        ]
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} vendas exportadas com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar vendas:\n{e}")


def exportar_itens_venda() -> None:
    """
    Exporta todos os itens de todas as vendas — tabela fato detalhada para Power BI.
    Cada linha: id_venda, data_venda, produto, quantidade, valor_unitario, subtotal.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Itens de Venda — Escolha onde salvar",
        nome_sugerido=f"itens_venda_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        vendas = listar_vendas()
        cabecalho = [
            "id_venda", "data_venda", "operador", "forma_pagamento",
            "produto", "quantidade", "valor_unitario", "subtotal"
        ]
        linhas = []
        for v in vendas:
            itens = obter_detalhes_venda(v["id_venda"])
            data_fmt = _timestamp_para_data(v["data_venda"])
            for item in itens:
                linhas.append([
                    v["id_venda"],
                    data_fmt,
                    v["usuario_nome"],
                    v["forma_pagamento"],
                    item["produto_nome"],
                    str(item["quantidade"]).replace(".", ","),
                    f"{item['valor_unitario']:.2f}".replace(".", ","),
                    f"{item['subtotal']:.2f}".replace(".", ","),
                ])
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} itens exportados com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar itens de venda:\n{e}")


def exportar_estoque() -> None:
    """
    Exporta o inventário atual de insumos para CSV.
    Cada linha: ID, nome, categoria, unidade, quantidade_atual, estoque_minimo, ultima_atualizacao.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Estoque — Escolha onde salvar",
        nome_sugerido=f"estoque_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        dados = listar_insumos()
        cabecalho = [
            "id_insumo", "nome", "categoria", "unidade_medida",
            "quantidade_atual", "estoque_minimo", "ultima_atualizacao"
        ]
        linhas = [
            [
                i["id_insumo"],
                i["nome"],
                i["categoria"],
                i["unidade_medida"],
                str(i["quantidade_atual"]).replace(".", ","),
                str(i["estoque_minimo"]).replace(".", ","),
                _timestamp_para_data(i["data_atualizacao"])
            ]
            for i in dados
        ]
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} insumos exportados com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar estoque:\n{e}")


def exportar_despesas() -> None:
    """
    Exporta todas as despesas registradas para CSV.
    Cada linha: ID, descricao, valor, data, categoria, operador.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Despesas — Escolha onde salvar",
        nome_sugerido=f"despesas_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        dados = listar_despesas()
        cabecalho = ["id_despesa", "descricao", "valor", "data", "categoria", "operador"]
        linhas = [
            [
                d["id"],
                d["descricao"],
                f"{d['valor_despesa']:.2f}".replace(".", ","),
                _timestamp_para_data(d["data_despesa"]),
                d["categoria_nome"],
                d["usuario_nome"]
            ]
            for d in dados
        ]
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} despesas exportadas com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar despesas:\n{e}")


def exportar_recebimentos() -> None:
    """
    Exporta todos os recebimentos avulsos para CSV.
    Cada linha: ID, descricao, valor, data, categoria, operador.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Recebimentos — Escolha onde salvar",
        nome_sugerido=f"recebimentos_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        dados = listar_recebimentos()
        cabecalho = ["id_recebimento", "descricao", "valor", "data", "categoria", "operador"]
        linhas = [
            [
                r["id"],
                r["descricao"],
                f"{r['valor_recebido']:.2f}".replace(".", ","),
                _timestamp_para_data(r["data_recebimento"]),
                r["categoria"],
                r["usuario_nome"]
            ]
            for r in dados
        ]
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} recebimentos exportados com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar recebimentos:\n{e}")


def exportar_produtos() -> None:
    """
    Exporta o catálogo de produtos para CSV.
    Cada linha: ID, nome, categoria, preco_venda, custo_producao.
    """
    caminho = _abrir_dialogo_salvar(
        titulo="Exportar Produtos — Escolha onde salvar",
        nome_sugerido=f"produtos_{time.strftime('%Y%m%d')}.csv"
    )
    if not caminho:
        return

    try:
        dados = listar_produtos()
        cabecalho = ["id_produto", "nome", "categoria", "preco_venda", "custo_producao"]
        linhas = [
            [
                p["id"],
                p["nome"],
                p["categoria_nome"],
                f"{p['preco_venda']:.2f}".replace(".", ","),
                f"{p['custo_producao']:.2f}".replace(".", ","),
            ]
            for p in dados
        ]
        _escrever_csv(caminho, cabecalho, linhas)
        messagebox.showinfo(
            "Exportação Concluída",
            f"{len(linhas)} produtos exportados com sucesso!\n\n{caminho}"
        )
    except Exception as e:
        messagebox.showerror("Erro na Exportação", f"Falha ao exportar produtos:\n{e}")