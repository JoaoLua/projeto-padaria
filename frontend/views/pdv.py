import tkinter as tk
from tkinter import ttk, messagebox
from backend.produtos import listar_produtos
from backend.vendas import registrar_venda
from backend.exportacao import exportar_vendas, exportar_itens_venda

class PDVView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.carrinho = [] # Lista de dicts {id_produto, nome, preco, quantidade, subtotal}
        self.produtos_disponiveis = []
        self._build_ui()
        
    def _build_ui(self):
        lbl_titulo = ttk.Label(self, text="Frente de Caixa (PDV)", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)
        
        # Frame superior: Busca e Adição
        frame_add = ttk.Frame(self)
        frame_add.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_add, text="Produto:").pack(side="left", padx=5)
        self.combo_produtos = ttk.Combobox(frame_add, state="readonly", width=40)
        self.combo_produtos.pack(side="left", padx=5)
        
        ttk.Label(frame_add, text="Qtd:").pack(side="left", padx=5)
        self.entry_qtd = ttk.Entry(frame_add, width=5)
        self.entry_qtd.insert(0, "1")
        self.entry_qtd.pack(side="left", padx=5)
        
        btn_add = ttk.Button(frame_add, text="Adicionar ao Carrinho", command=self.adicionar_item)
        btn_add.pack(side="left", padx=10)
        
        # Frame central: Tabela do Carrinho
        columns = ("ID", "Produto", "Qtd", "Preço Unit.", "Subtotal")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Botão de remover item selecionado
        btn_remover = ttk.Button(self, text="Remover Item Selecionado", command=self.remover_item)
        btn_remover.pack(anchor="e", padx=10)
        
        # Frame inferior: Finalização
        frame_fim = ttk.LabelFrame(self, text=" Finalizar Venda ", padding=(10, 10))
        frame_fim.pack(fill="x", padx=10, pady=10)
        
        self.lbl_total = ttk.Label(frame_fim, text="Total: R$ 0.00", font=("Arial", 14, "bold"))
        self.lbl_total.pack(side="left", padx=10)
        
        ttk.Label(frame_fim, text="Pagamento:").pack(side="left", padx=5)
        self.combo_pagto = ttk.Combobox(frame_fim, state="readonly", values=["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])
        self.combo_pagto.current(0)
        self.combo_pagto.pack(side="left", padx=5)
        
        btn_finalizar = ttk.Button(frame_fim, text="Finalizar Venda", command=self.finalizar_venda)
        btn_finalizar.pack(side="right", padx=10)

        # Frame de exportação — abaixo da área de finalização
        frame_export = ttk.LabelFrame(self, text=" Exportar Dados para Power BI ", padding=(10, 5))
        frame_export.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(frame_export, text="Gera CSV com separador ';' (UTF-8) pronto para importar no Power BI:").pack(side="left", padx=5)
        btn_exp_vendas = ttk.Button(frame_export, text="⬇ Vendas (resumo)", command=exportar_vendas)
        btn_exp_vendas.pack(side="right", padx=5)
        btn_exp_itens = ttk.Button(frame_export, text="⬇ Itens de Venda (detalhado)", command=exportar_itens_venda)
        btn_exp_itens.pack(side="right", padx=5)
        
    def on_show(self):
        self.carregar_produtos()
        
    def carregar_produtos(self):
        try:
            self.produtos_disponiveis = listar_produtos()
            nomes = [f"{p['id']} - {p['nome']} (R$ {p['preco_venda']:.2f})" for p in self.produtos_disponiveis]
            self.combo_produtos['values'] = nomes
            if nomes:
                self.combo_produtos.current(0)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produtos:\n{e}")
            
    def adicionar_item(self):
        idx = self.combo_produtos.current()
        if idx == -1: return
        
        produto = self.produtos_disponiveis[idx]
        try:
            qtd = float(self.entry_qtd.get().replace(",", "."))
            if qtd <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade inválida.")
            return
            
        item = {
            "id_produto": produto["id"],
            "nome": produto["nome"],
            "preco": float(produto["preco_venda"]),
            "quantidade": qtd,
            "subtotal": float(produto["preco_venda"]) * qtd
        }
        self.carrinho.append(item)
        self.atualizar_tabela()
        self.entry_qtd.delete(0, tk.END)
        self.entry_qtd.insert(0, "1")
        
    def remover_item(self):
        selecionado = self.tree.selection()
        if not selecionado: return
        
        # É importante remover de trás pra frente se houver múltiplos itens
        indices_para_remover = [self.tree.index(item) for item in selecionado]
        for idx in sorted(indices_para_remover, reverse=True):
            del self.carrinho[idx]
            
        self.atualizar_tabela()
        
    def atualizar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        total = 0.0
        for item in self.carrinho:
            self.tree.insert("", "end", values=(
                item["id_produto"], 
                item["nome"], 
                item["quantidade"], 
                f"R$ {item['preco']:.2f}", 
                f"R$ {item['subtotal']:.2f}"
            ))
            total += item["subtotal"]
            
        self.lbl_total.config(text=f"Total: R$ {total:.2f}")
        
    def finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Aviso", "Carrinho vazio.")
            return
            
        metodo_pagto = self.combo_pagto.get()
        id_usuario = self.controller.usuario_logado["id"] if self.controller.usuario_logado else 1
        
        itens_backend = [
            {
                "id_produto": item["id_produto"],
                "quantidade": item["quantidade"],
                "valor_unitario": item["preco"]
            }
            for item in self.carrinho
        ]
        
        try:
            id_venda = registrar_venda(id_usuario, itens_backend, metodo_pagto)
            messagebox.showinfo("Sucesso", f"Venda #{id_venda} registrada com sucesso!")
            self.carrinho.clear()
            self.atualizar_tabela()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao registrar venda:\n{str(e)}")