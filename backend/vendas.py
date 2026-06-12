import sqlite3
import time
from backend.conexao import conectar

def registrar_venda(id_usuario: int, itens_carrinho: list[dict], forma_pagamento: str) -> int:
    """
    Registra uma venda no banco de dados de forma atômica (transação ACID).
    Garante o cálculo do valor total, a inserção dos itens e a baixa de estoque
    de insumos associados via ficha técnica. Se alguma operação falhar, toda a
    transação sofrerá rollback automaticamente.
    """
    if not itens_carrinho:
        raise ValueError("O carrinho de compras não pode estar vazio.")
        
    data_venda = int(time.time())
    valor_total = sum(item["quantidade"] * item["valor_unitario"] for item in itens_carrinho)
    
    with conectar() as conn:
        cursor = conn.cursor()
        
        # 1. Inserir cabeçalho da venda (Master)
        cursor.execute(
            """
            INSERT INTO vendas (id_usuario, valor_total, forma_pagamento, data_venda)
            VALUES (?, ?, ?, ?);
            """,
            (id_usuario, valor_total, forma_pagamento, data_venda)
        )
        id_venda = cursor.lastrowid
        
        # 2. Inserir itens da venda e dar baixa nos insumos correspondentes (Detail)
        for item in itens_carrinho:
            id_produto = item["id_produto"]
            quantidade_vendida = item["quantidade"]
            valor_unitario = item["valor_unitario"]
            subtotal = quantidade_vendida * valor_unitario
            
            # Inserir o item da venda
            cursor.execute(
                """
                INSERT INTO itens_venda (id_venda, id_produto, quantidade, valor_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?);
                """,
                (id_venda, id_produto, quantidade_vendida, valor_unitario, subtotal)
            )
            
            # Consultar a ficha técnica do produto
            cursor.execute(
                """
                SELECT id_insumo, quantidade_necessaria
                FROM produto_insumos
                WHERE id_produto = ?;
                """,
                (id_produto,)
            )
            ficha_tecnica = cursor.fetchall()
            
            # Subtrair quantidade consumida de cada insumo
            for id_insumo, quantidade_necessaria in ficha_tecnica:
                quantidade_reduzir = quantidade_vendida * quantidade_necessaria
                cursor.execute(
                    """
                    UPDATE insumos
                    SET quantidade_atual = quantidade_atual - ?, data_atualizacao = ?
                    WHERE id_insumo = ?;
                    """,
                    (quantidade_reduzir, data_venda, id_insumo)
                )
                
        return id_venda

def listar_vendas(data_inicio: int = None, data_fim: int = None) -> list[dict]:
    """
    Retorna o histórico de vendas realizadas, fazendo JOIN com a tabela usuarios
    para trazer o nome do operador de caixa. Permite filtragem opcional por período.
    """
    query = """
        SELECT v.id_venda, u.nome AS usuario_nome, v.valor_total, v.forma_pagamento, v.data_venda
        FROM vendas v
        INNER JOIN usuarios u ON v.id_usuario = u.id_usuario
    """
    conditions = []
    params = []
    
    if data_inicio is not None:
        conditions.append("v.data_venda >= ?")
        params.append(data_inicio)
    if data_fim is not None:
        conditions.append("v.data_venda <= ?")
        params.append(data_fim)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY v.data_venda DESC;"
    
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def listar_todos_itens_venda() -> list[dict]:
    """
    Retorna todos os itens de todas as vendas em uma única query com JOIN.
    Usado exclusivamente pelo exportar_tudo.py para performance —
    evita N queries individuais (uma por venda).
    """
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                v.id_venda,
                v.data_venda,
                u.nome  AS usuario_nome,
                v.forma_pagamento,
                p.nome  AS produto_nome,
                iv.quantidade,
                iv.valor_unitario,
                iv.subtotal
            FROM itens_venda iv
            INNER JOIN vendas   v ON iv.id_venda   = v.id_venda
            INNER JOIN produtos p ON iv.id_produto = p.id_produto
            INNER JOIN usuarios u ON v.id_usuario  = u.id_usuario
            ORDER BY v.id_venda;
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def obter_detalhes_venda(id_venda: int) -> list[dict]:
    """
    Retorna os detalhes dos itens de uma venda específica (cupom fiscal),
    trazendo o nome do produto via JOIN com a tabela produtos.
    """
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.nome AS produto_nome, iv.quantidade, iv.valor_unitario, iv.subtotal
            FROM itens_venda iv
            INNER JOIN produtos p ON iv.id_produto = p.id_produto
            WHERE iv.id_venda = ?;
            """,
            (id_venda,)
        )
        return [dict(row) for row in cursor.fetchall()]