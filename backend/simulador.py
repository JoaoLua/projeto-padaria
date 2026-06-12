import os
import sys
import sqlite3
import random
import time
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.conexao import conectar
from banco.setup import criar_tabelas

# ---------------------------------------------------------------------------
# Tabelas de distribuição — aqui mora a "realidade" da simulação
# ---------------------------------------------------------------------------

# Formas de pagamento: Pix domina, dinheiro é minoria
FORMAS_PAGAMENTO = ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"]
PESO_PAGAMENTO   = [0.42,  0.28,                 0.20,               0.10]

# Horários: pico no café da manhã (7-9h) e almoço (11-13h), fraco à tarde
HORAS_DIA   = list(range(6, 20))
PESO_HORAS  = [0.04, 0.14, 0.13, 0.06, 0.10, 0.11, 0.07, 0.06,
               0.06, 0.06, 0.05, 0.05, 0.04, 0.03]

# Dias da semana: sábado e sexta vendem mais, domingo quase nada
# 0=segunda ... 6=domingo
PESO_DIA_SEMANA = [0.14, 0.13, 0.14, 0.15, 0.17, 0.20, 0.07]

# Meses: dezembro e janeiro têm pico (festas + férias), junho/julho menor
PESO_MES = {1: 1.30, 2: 1.00, 3: 1.00, 4: 0.95, 5: 0.90, 6: 0.85,
            7: 0.85, 8: 0.90, 9: 0.95, 10: 1.00, 11: 1.10, 12: 1.40}


def _escolher_data(hoje: datetime, dias_retroativos: int) -> datetime:
    """
    Escolhe uma data retroativa com peso por dia da semana e mês,
    e horário com pico no café da manhã e almoço.
    """
    # Monta lista de datas disponíveis com peso relativo
    datas = []
    pesos = []
    for d in range(dias_retroativos):
        dt = hoje - timedelta(days=d)
        peso_semana = PESO_DIA_SEMANA[dt.weekday()]
        peso_mes    = PESO_MES.get(dt.month, 1.0)
        datas.append(dt)
        pesos.append(peso_semana * peso_mes)

    data_escolhida = random.choices(datas, weights=pesos, k=1)[0]
    hora   = random.choices(HORAS_DIA, weights=PESO_HORAS, k=1)[0]
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return data_escolhida.replace(hour=hora, minute=minuto, second=segundo, microsecond=0)


def executar_simulacao(total_vendas: int = 10000):
    """
    Popula o banco com dados retroativos realistas para os últimos 6 meses.
    Distribuições não-uniformes em pagamento, horário, dia da semana,
    sazonalidade mensal e popularidade de produto.
    """
    tempo_inicial = time.time()

    criar_tabelas()

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # ------------------------------------------------------------------
        # 2. Limpeza
        # ------------------------------------------------------------------
        print("Limpando dados anteriores...")
        for tabela in ["itens_venda", "vendas", "despesas", "recebimentos",
                       "produto_insumos", "produtos", "insumos",
                       "categorias_produto", "categorias_financeiras"]:
            cursor.execute(f"DELETE FROM {tabela};")

        # ------------------------------------------------------------------
        # 3. Usuário
        # ------------------------------------------------------------------
        cursor.execute("SELECT id_usuario FROM usuarios;")
        usuarios_existentes = cursor.fetchall()

        if not usuarios_existentes:
            cursor.execute(
                "INSERT INTO usuarios (nome, login, senha, funcao) VALUES (?, ?, ?, ?);",
                ("Usuario Teste", "admin", "123", "admin")
            )
            id_usuario_teste = cursor.lastrowid
            print(f"Usuário de testes único 'admin' criado (ID: {id_usuario_teste}).")
        else:
            id_usuario_teste = usuarios_existentes[0][0]

        cursor.execute("SELECT id_usuario FROM usuarios;")
        ids_usuarios = [row[0] for row in cursor.fetchall()]

        # ------------------------------------------------------------------
        # 4. Categorias de Produto
        # ------------------------------------------------------------------
        categorias_prod = [
            ("Panificação",  "Pães, bolos e doces fabricados na padaria"),
            ("Laticínios",   "Leites, queijos, manteigas e iogurtes"),
            ("Bebidas",      "Sucos, refrigerantes, águas e cafés"),
            ("Secos",        "Mercearia de prateleira e doces industriais"),
            ("Perecíveis",   "Salgados assados, lanches e frios"),
            ("Limpeza",      "Produtos de higiene e limpeza do local"),
            ("Embalagens",   "Sacolas, copos, papéis e caixas para viagem"),
        ]
        cat_prod_map = {}
        for nome, desc in categorias_prod:
            cursor.execute(
                "INSERT INTO categorias_produto (nome, descricao) VALUES (?, ?);",
                (nome, desc)
            )
            cat_prod_map[nome] = cursor.lastrowid

        # ------------------------------------------------------------------
        # 5. Categorias Financeiras
        # ------------------------------------------------------------------
        categorias_fin = [
            ("Contas de Consumo",   "SAIDA"),
            ("Fornecedores",        "SAIDA"),
            ("Aluguel",             "SAIDA"),
            ("Folha de Pagamento",  "SAIDA"),
            ("Manutenção",          "SAIDA"),
            ("Aporte de Capital",   "ENTRADA"),
            ("Encomendas Especiais","ENTRADA"),
        ]
        cat_fin_map = {}
        for nome, tipo in categorias_fin:
            cursor.execute(
                "INSERT INTO categorias_financeiras (nome, tipo_movimentacao) VALUES (?, ?);",
                (nome, tipo)
            )
            cat_fin_map[nome] = cursor.lastrowid

        # ------------------------------------------------------------------
        # 6. Insumos
        # ------------------------------------------------------------------
        insumos_data = [
            ("Farinha de Trigo",  150.0, "KG",  20.0),
            ("Açúcar Refinado",   100.0, "KG",  10.0),
            ("Ovos",              300.0, "UN",  24.0),
            ("Manteiga",           60.0, "KG",   8.0),
            ("Leite Integral",    120.0, "L",   15.0),
        ]
        data_atual = int(time.time())
        insumos_map = {}
        for nome, qtd_ini, unid, est_min in insumos_data:
            cursor.execute(
                """
                INSERT INTO insumos (nome, quantidade_atual, unidade_medida, estoque_minimo, data_atualizacao)
                VALUES (?, ?, ?, ?, ?);
                """,
                (nome, qtd_ini, unid, est_min, data_atual)
            )
            insumos_map[nome] = cursor.lastrowid

        # ------------------------------------------------------------------
        # 7. Produtos — cada um com um PESO de popularidade
        # ------------------------------------------------------------------
        # (nome, preco_venda, custo_producao, categoria, receita_ou_None, PESO)
        # Peso reflete demanda relativa: pão francês é o carro-chefe
        produtos_com_ficha = [
            ("Pão Francês 50g",          0.50,  0.15, "Panificação",
             [("Farinha de Trigo", 0.045)],                                    35.0),
            ("Pão de Queijo Tradicional", 3.00,  1.00, "Panificação",
             [("Ovos", 0.4), ("Manteiga", 0.012)],                             15.0),
            ("Sonho de Creme",            5.50,  1.90, "Panificação",
             [("Farinha de Trigo", 0.070), ("Açúcar Refinado", 0.025),
              ("Ovos", 0.5), ("Manteiga", 0.010)],                              8.0),
            ("Croissant Presunto/Queijo", 7.50,  2.50, "Panificação",
             [("Farinha de Trigo", 0.090), ("Manteiga", 0.040)],                6.0),
            ("Coxinha de Frango",         6.00,  2.00, "Perecíveis",
             [("Farinha de Trigo", 0.075), ("Manteiga", 0.010)],                7.0),
            ("Esfiha de Carne Assada",    6.50,  2.30, "Perecíveis",
             [("Farinha de Trigo", 0.075), ("Manteiga", 0.010)],                5.0),
            ("Pão de Forma Artesanal",    8.00,  2.80, "Panificação",
             [("Farinha de Trigo", 0.350), ("Manteiga", 0.025)],                4.0),
            ("Bolo de Cenoura",          18.00,  6.00, "Panificação",
             [("Farinha de Trigo", 0.200), ("Açúcar Refinado", 0.150),
              ("Ovos", 3.0), ("Manteiga", 0.050)],                              2.0),
            ("Rosca de Coco Doce",       13.50,  4.50, "Panificação",
             [("Farinha de Trigo", 0.240), ("Açúcar Refinado", 0.090),
              ("Ovos", 1.0), ("Manteiga", 0.020)],                              2.0),
            ("Bolo de Chocolate",        22.00,  7.50, "Panificação",
             [("Farinha de Trigo", 0.220), ("Açúcar Refinado", 0.200),
              ("Ovos", 3.0), ("Manteiga", 0.060)],                              1.5),
        ]

        produtos_sem_ficha = [
            ("Café Espresso Carioca",        4.50, 1.10, "Bebidas",    20.0),
            ("Água Mineral sem Gás 500ml",   3.00, 0.80, "Bebidas",    10.0),
            ("Refrigerante Coca-Cola Lata",  5.00, 2.20, "Bebidas",     6.0),
            ("Ice Tea Pêssego 450ml",        5.50, 2.40, "Bebidas",     4.0),
            ("Suco de Uva Del Valle 1L",     7.50, 3.90, "Bebidas",     3.0),
            ("Cerveja Heineken Lata 350ml",  7.50, 3.90, "Bebidas",     2.0),
            ("Alfajor Artesanal",            6.00, 2.80, "Secos",       3.0),
            ("Barra de Chocolate Lacta 90g", 8.50, 4.20, "Secos",       2.0),
            ("Sacola Ecológica Retornável",  2.50, 0.60, "Embalagens",  1.5),
            ("Saco de Gelo Cubo 5kg",       12.00, 4.50, "Secos",       0.5),
        ]

        # produtos_cache = lista de dicts com id, preco e peso
        produtos_cache = []

        for nome, preco_venda, custo_prod, cat_nome, receita, peso in produtos_com_ficha:
            cursor.execute(
                "INSERT INTO produtos (id_categoria_produto, nome, preco_venda, custo_producao) VALUES (?, ?, ?, ?);",
                (cat_prod_map[cat_nome], nome, preco_venda, custo_prod)
            )
            id_prod = cursor.lastrowid
            produtos_cache.append({"id": id_prod, "preco_venda": preco_venda, "peso": peso})
            for ins_nome, qtd_nec in receita:
                cursor.execute(
                    "INSERT INTO produto_insumos (id_produto, id_insumo, quantidade_necessaria) VALUES (?, ?, ?);",
                    (id_prod, insumos_map[ins_nome], qtd_nec)
                )

        for nome, preco_venda, custo_prod, cat_nome, peso in produtos_sem_ficha:
            cursor.execute(
                "INSERT INTO produtos (id_categoria_produto, nome, preco_venda, custo_producao) VALUES (?, ?, ?, ?);",
                (cat_prod_map[cat_nome], nome, preco_venda, custo_prod)
            )
            id_prod = cursor.lastrowid
            produtos_cache.append({"id": id_prod, "preco_venda": preco_venda, "peso": peso})

        print(f"Cadastrados {len(produtos_cache)} produtos base no catálogo.")

        pesos_produtos = [p["peso"] for p in produtos_cache]

        # ------------------------------------------------------------------
        # 8. Despesas e Recebimentos
        # ------------------------------------------------------------------
        hoje = datetime.now()
        despesas_data = []
        recebimentos_data = []
        total_despesas_injetadas = 0
        total_recebimentos_injetados = 0

        for m in range(6):
            data_mes = hoje - timedelta(days=m * 30)

            # Folha — dia 5, valor com leve variação (hora extra etc.)
            ts = int(data_mes.replace(day=5, hour=10, minute=0, second=0).timestamp())
            despesas_data.append((cat_fin_map["Folha de Pagamento"], random.choice(ids_usuarios),
                                  "Salários dos Funcionários",
                                  round(random.uniform(4800.00, 5600.00), 2), ts))
            total_despesas_injetadas += 1

            # Aluguel — fixo
            ts = int(data_mes.replace(day=10, hour=10, minute=0, second=0).timestamp())
            despesas_data.append((cat_fin_map["Aluguel"], random.choice(ids_usuarios),
                                  "Aluguel do Ponto Comercial", 3200.00, ts))
            total_despesas_injetadas += 1

            # Energia/água — varia mais no verão (dez-fev)
            fator_calor = 1.3 if data_mes.month in (12, 1, 2) else 1.0
            ts = int(data_mes.replace(day=18, hour=14, minute=0, second=0).timestamp())
            despesas_data.append((cat_fin_map["Contas de Consumo"], random.choice(ids_usuarios),
                                  "Conta mensal de Energia e Água",
                                  round(random.uniform(500.00, 950.00) * fator_calor, 2), ts))
            total_despesas_injetadas += 1

            # Fornecedores — 2x por mês, valor maior em dezembro
            fator_forn = 1.4 if data_mes.month == 12 else 1.0
            for _ in range(2):
                dia = random.randint(1, 28)
                ts = int(data_mes.replace(day=dia, hour=11, minute=0, second=0).timestamp())
                despesas_data.append((cat_fin_map["Fornecedores"], random.choice(ids_usuarios),
                                      f"Compra de insumos - lote #{random.randint(100, 999)}",
                                      round(random.uniform(1200.00, 2800.00) * fator_forn, 2), ts))
                total_despesas_injetadas += 1

            # Manutenção — bimestral
            if m % 2 == 0:
                ts = int(data_mes.replace(day=22, hour=15, minute=0, second=0).timestamp())
                despesas_data.append((cat_fin_map["Manutenção"], random.choice(ids_usuarios),
                                      "Manutenção de Forno Industrial",
                                      round(random.uniform(200.00, 600.00), 2), ts))
                total_despesas_injetadas += 1

            # Aportes de capital
            if m in (1, 4):
                ts = int(data_mes.replace(day=2, hour=9, minute=0, second=0).timestamp())
                recebimentos_data.append((random.choice(ids_usuarios), "Aporte de Capital",
                                          "Aporte de sócio investidor", 5000.00, ts))
                total_recebimentos_injetados += 1

            # Encomendas — 3x por mês, mais caras em dezembro
            fator_enc = 1.5 if data_mes.month == 12 else 1.0
            for _ in range(3):
                dia = random.randint(1, 28)
                ts = int(data_mes.replace(day=dia, hour=16, minute=0, second=0).timestamp())
                recebimentos_data.append((random.choice(ids_usuarios), "Encomendas Especiais",
                                          f"Festa de Aniversário - Encomenda #{random.randint(10, 99)}",
                                          round(random.uniform(250.00, 800.00) * fator_enc, 2), ts))
                total_recebimentos_injetados += 1

        cursor.executemany(
            "INSERT INTO despesas (id_categoria_financeira, id_usuario, descricao, valor_despesa, data_despesa) VALUES (?, ?, ?, ?, ?);",
            despesas_data
        )
        cursor.executemany(
            "INSERT INTO recebimentos (id_usuario, categoria, descricao, valor_recebido, data_recebimento) VALUES (?, ?, ?, ?, ?);",
            recebimentos_data
        )

        # ------------------------------------------------------------------
        # 9. Vendas com distribuições realistas
        # ------------------------------------------------------------------
        print(f"Iniciando simulação de {total_vendas} vendas com distribuições realistas...")

        vendas_list      = []
        itens_venda_list = []

        cursor.execute("SELECT COALESCE(MAX(id_venda), 0) FROM vendas;")
        proximo_venda_id = cursor.fetchone()[0] + 1

        for i in range(total_vendas):
            id_venda = proximo_venda_id + i

            id_usuario     = random.choice(ids_usuarios)
            forma_pagamento = random.choices(FORMAS_PAGAMENTO, weights=PESO_PAGAMENTO, k=1)[0]
            data_venda_dt  = _escolher_data(hoje, 180)
            data_venda     = int(data_venda_dt.timestamp())

            # Número de produtos: compras rápidas (1-2 itens) são mais comuns
            num_produtos = random.choices([1, 2, 3, 4], weights=[0.45, 0.30, 0.15, 0.10], k=1)[0]

            # Seleciona produtos com peso de popularidade (com reposição p/ não limitar)
            produtos_venda_idx = random.choices(range(len(produtos_cache)),
                                                weights=pesos_produtos, k=num_produtos)
            # Remove duplicatas mantendo ordem
            vistos = set()
            produtos_venda = []
            for idx in produtos_venda_idx:
                if idx not in vistos:
                    vistos.add(idx)
                    produtos_venda.append(produtos_cache[idx])

            valor_total = 0.0
            for p in produtos_venda:
                preco_unit = p["preco_venda"]
                # Pães comprados em maior quantidade; itens caros quase sempre qty=1
                if preco_unit <= 1.00:
                    quantidade = float(random.choices([4, 6, 8, 10, 12], weights=[0.30, 0.30, 0.20, 0.12, 0.08], k=1)[0])
                elif preco_unit <= 5.00:
                    quantidade = float(random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10], k=1)[0])
                else:
                    quantidade = 1.0

                subtotal = round(quantidade * preco_unit, 2)
                valor_total += subtotal
                itens_venda_list.append((id_venda, p["id"], quantidade, preco_unit, subtotal))

            vendas_list.append((id_venda, id_usuario, round(valor_total, 2), forma_pagamento, data_venda))

        print("Gravando vendas (Bulk Insert)...")

        cursor.executemany(
            "INSERT INTO vendas (id_venda, id_usuario, valor_total, forma_pagamento, data_venda) VALUES (?, ?, ?, ?, ?);",
            vendas_list
        )
        cursor.executemany(
            "INSERT INTO itens_venda (id_venda, id_produto, quantidade, valor_unitario, subtotal) VALUES (?, ?, ?, ?, ?);",
            itens_venda_list
        )

        conn.commit()

    tempo_gasto = time.time() - tempo_inicial

    print("\n" + "=" * 50)
    print("STATUS DA INJEÇÃO: Concluído com sucesso!")
    print("=" * 50)
    print(f"Total de Usuários no Banco:               {len(ids_usuarios)}")
    print(f"Total de Categorias de Produtos:          {len(categorias_prod)}")
    print(f"Total de Categorias Financeiras:          {len(categorias_fin)}")
    print(f"Total de Produtos Criados:                {len(produtos_cache)}")
    print(f"Total de Insumos Criados:                 {len(insumos_data)}")
    print(f"Total de Despesas Injetadas:              {total_despesas_injetadas}")
    print(f"Total de Recebimentos Injetados:          {total_recebimentos_injetados}")
    print(f"Total de Cupons de Vendas Commitados:     {len(vendas_list)}")
    print(f"Total de Linhas de Itens de Venda:        {len(itens_venda_list)}")
    print(f"Tempo Total Gasto (Bulk Insert):          {tempo_gasto:.2f} segundos")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    executar_simulacao()