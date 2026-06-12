import tkinter as tk
from tkinter import ttk, messagebox
from backend.insumos import listar_insumos, inserir_insumo, atualizar_quantidade_insumo
from backend.exportacao import exportar_estoque

class EstoqueView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        
    def _build_ui(self):
        lbl_titulo = ttk.Label(self, text="Gestão de Estoque (Insumos)", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)
        
        # Tabela
        columns = ("ID", "Nome", "Unid.", "Quantidade", "Estoque Mín.")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Barra de ações
        frame_acoes = ttk.Frame(self)
        frame_acoes.pack(fill="x", padx=10, pady=5)

        btn_refresh = ttk.Button(frame_acoes, text="Atualizar Tabela", command=self.carregar_dados)
        btn_refresh.pack(side="left", padx=5)

        btn_csv = ttk.Button(frame_acoes, text="⬇ Exportar CSV", command=exportar_estoque)
        btn_csv.pack(side="right", padx=5)
        
        # Frame de Ajuste Rápido
        frame_ajuste = ttk.LabelFrame(self, text=" Ajustar Quantidade (Estoque) ", padding=10)
        frame_ajuste.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_ajuste, text="Selecione um item na tabela, digite a variação (ex: 5 para adicionar, -2 para remover) e ajuste:").pack(side="top", anchor="w")
        
        frame_ajuste_linha = ttk.Frame(frame_ajuste)
        frame_ajuste_linha.pack(side="top", fill="x", pady=5)
        
        ttk.Label(frame_ajuste_linha, text="Variação:").pack(side="left", padx=5)
        self.entry_var = ttk.Entry(frame_ajuste_linha, width=10)
        self.entry_var.pack(side="left", padx=5)
        
        btn_ajustar = ttk.Button(frame_ajuste_linha, text="Ajustar", command=self.ajustar_quantidade)
        btn_ajustar.pack(side="left", padx=10)
        
        # Frame de Novo Insumo
        frame_novo = ttk.LabelFrame(self, text=" Novo Insumo ", padding=10)
        frame_novo.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_novo, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_nome = ttk.Entry(frame_novo, width=25)
        self.entry_nome.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame_novo, text="Unidade:").grid(row=0, column=2, padx=5, pady=5)
        self.combo_unid = ttk.Combobox(frame_novo, values=["KG", "UN", "L", "CX"], state="readonly", width=5)
        self.combo_unid.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(frame_novo, text="Estoque Mín:").grid(row=0, column=4, padx=5, pady=5)
        self.entry_est_min = ttk.Entry(frame_novo, width=10)
        self.entry_est_min.insert(0, "10.0")
        self.entry_est_min.grid(row=0, column=5, padx=5, pady=5)
        
        btn_novo = ttk.Button(frame_novo, text="Cadastrar", command=self.cadastrar_insumo)
        btn_novo.grid(row=0, column=6, padx=15, pady=5)
        
    def on_show(self):
        self.carregar_dados()
        
    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            insumos = listar_insumos()
            for i in insumos:
                self.tree.insert("", "end", values=(
                    i['id_insumo'], 
                    i['nome'], 
                    i['unidade_medida'], 
                    i['quantidade_atual'], 
                    i['estoque_minimo']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar insumos:\n{e}")
            
    def ajustar_quantidade(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um insumo na tabela.")
            return
            
        try:
            variacao = float(self.entry_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Aviso", "Valor de variação inválido.")
            return
            
        item_values = self.tree.item(selecionado[0])['values']
        id_insumo = item_values[0]
        
        try:
            atualizar_quantidade_insumo(id_insumo, variacao)
            messagebox.showinfo("Sucesso", "Quantidade atualizada!")
            self.entry_var.delete(0, tk.END)
            self.carregar_dados()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ajustar quantidade:\n{e}")
            
    def cadastrar_insumo(self):
        nome = self.entry_nome.get().strip()
        unid = self.combo_unid.get().strip()
        try:
            est_min = float(self.entry_est_min.get().replace(",", "."))
            if not nome or not unid: raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Preencha todos os campos corretamente.")
            return
            
        try:
            inserir_insumo(nome, 0.0, unid, est_min)
            messagebox.showinfo("Sucesso", "Insumo cadastrado!")
            self.entry_nome.delete(0, tk.END)
            self.combo_unid.set("")
            self.entry_est_min.delete(0, tk.END)
            self.entry_est_min.insert(0, "10.0")
            self.carregar_dados()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao cadastrar insumo:\n{e}")