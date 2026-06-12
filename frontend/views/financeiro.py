import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from backend.financeiro import listar_despesas, inserir_despesa, listar_recebimentos, inserir_recebimento
from backend.categorias import listar_categorias_financeiras
from backend.exportacao import exportar_despesas, exportar_recebimentos

class FinanceiroView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        
    def _build_ui(self):
        lbl_titulo = ttk.Label(self, text="Módulo Financeiro", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_despesas = ttk.Frame(notebook)
        self.tab_receitas = ttk.Frame(notebook)
        
        notebook.add(self.tab_despesas, text="Despesas")
        notebook.add(self.tab_receitas, text="Recebimentos Avulsos")
        
        self._build_despesas(self.tab_despesas)
        self._build_receitas(self.tab_receitas)
        
    def _build_despesas(self, parent):
        frame_add = ttk.LabelFrame(parent, text=" Nova Despesa ", padding=10)
        frame_add.pack(fill="x", pady=5)
        
        ttk.Label(frame_add, text="Descrição:").grid(row=0, column=0, padx=5)
        self.d_desc = ttk.Entry(frame_add, width=20)
        self.d_desc.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_add, text="Valor:").grid(row=0, column=2, padx=5)
        self.d_val = ttk.Entry(frame_add, width=10)
        self.d_val.grid(row=0, column=3, padx=5)
        
        ttk.Label(frame_add, text="Categoria:").grid(row=0, column=4, padx=5)
        self.d_cat = ttk.Combobox(frame_add, state="readonly")
        self.d_cat.grid(row=0, column=5, padx=5)
        
        btn_salvar = ttk.Button(frame_add, text="Registrar", command=self.salvar_despesa)
        btn_salvar.grid(row=0, column=6, padx=10)
        
        columns = ("ID", "Descrição", "Valor", "Data", "Categoria")
        self.tree_d = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns: self.tree_d.heading(col, text=col)
        self.tree_d.pack(fill="both", expand=True, pady=5)

        btn_csv_d = ttk.Button(parent, text="⬇ Exportar CSV", command=exportar_despesas)
        btn_csv_d.pack(anchor="e", padx=5, pady=(0, 5))
        frame_add = ttk.LabelFrame(parent, text=" Novo Recebimento ", padding=10)
        frame_add.pack(fill="x", pady=5)
        
        ttk.Label(frame_add, text="Descrição:").grid(row=0, column=0, padx=5)
        self.r_desc = ttk.Entry(frame_add, width=20)
        self.r_desc.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_add, text="Valor:").grid(row=0, column=2, padx=5)
        self.r_val = ttk.Entry(frame_add, width=10)
        self.r_val.grid(row=0, column=3, padx=5)
        
        ttk.Label(frame_add, text="Categoria:").grid(row=0, column=4, padx=5)
        self.r_cat = ttk.Combobox(frame_add, state="readonly")
        self.r_cat.grid(row=0, column=5, padx=5)
        
        btn_salvar = ttk.Button(frame_add, text="Registrar", command=self.salvar_receita)
        btn_salvar.grid(row=0, column=6, padx=10)
        
        columns = ("ID", "Descrição", "Valor", "Data", "Categoria")
        self.tree_r = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns: self.tree_r.heading(col, text=col)
        self.tree_r.pack(fill="both", expand=True, pady=5)

        btn_csv_r = ttk.Button(parent, text="⬇ Exportar CSV", command=exportar_recebimentos)
        btn_csv_r.pack(anchor="e", padx=5, pady=(0, 5))
        
    def on_show(self):
        self.categorias_cache = []
        self.carregar_dados()
        
    def carregar_dados(self):
        try:
            self.categorias_cache = listar_categorias_financeiras()
            
            # Filtra por tipo
            cats_d = [c['nome'] for c in self.categorias_cache if c['tipo_movimentacao'] == 'SAIDA']
            cats_r = [c['nome'] for c in self.categorias_cache if c['tipo_movimentacao'] == 'ENTRADA']
            
            self.d_cat['values'] = cats_d
            self.r_cat['values'] = cats_r
            
            for item in self.tree_d.get_children(): self.tree_d.delete(item)
            for d in listar_despesas():
                try:
                    data_f = datetime.fromtimestamp(d['data_despesa']).strftime('%d/%m/%Y %H:%M')
                except Exception:
                    data_f = str(d['data_despesa'])
                self.tree_d.insert("", "end", values=(d['id'], d['descricao'], f"R$ {d['valor_despesa']:.2f}", data_f, d['categoria_nome']))
                
            for item in self.tree_r.get_children(): self.tree_r.delete(item)
            for r in listar_recebimentos():
                try:
                    data_f = datetime.fromtimestamp(r['data_recebimento']).strftime('%d/%m/%Y %H:%M')
                except Exception:
                    data_f = str(r['data_recebimento'])
                self.tree_r.insert("", "end", values=(r['id'], r['descricao'], f"R$ {r['valor_recebido']:.2f}", data_f, r['categoria']))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha no carregamento:\n{e}")
            
    def salvar_despesa(self):
        desc = self.d_desc.get().strip()
        cat_nome = self.d_cat.get()
        if not desc or not cat_nome:
            messagebox.showwarning("Aviso", "Preencha corretamente.")
            return
        try:
            val = float(self.d_val.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Aviso", "Valor inválido.")
            return
        
        id_cat = next((c['id'] for c in self.categorias_cache if c['nome'] == cat_nome and c['tipo_movimentacao'] == 'SAIDA'), None)
        if not id_cat: return
        id_usuario = self.controller.usuario_logado['id'] if self.controller.usuario_logado else 1
        
        try:
            inserir_despesa(id_cat, id_usuario, desc, val)
            messagebox.showinfo("Sucesso", "Despesa registrada!")
            self.d_desc.delete(0, tk.END)
            self.d_val.delete(0, tk.END)
            self.d_cat.set("")
            self.carregar_dados()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao registrar:\n{e}")
            
    def salvar_receita(self):
        desc = self.r_desc.get().strip()
        cat_nome = self.r_cat.get()
        if not desc or not cat_nome: return
        try:
            val = float(self.r_val.get().replace(",", "."))
        except ValueError: return
        
        id_usuario = self.controller.usuario_logado['id'] if self.controller.usuario_logado else 1
        
        try:
            inserir_recebimento(id_usuario, cat_nome, desc, val)
            messagebox.showinfo("Sucesso", "Recebimento registrado!")
            self.r_desc.delete(0, tk.END)
            self.r_val.delete(0, tk.END)
            self.r_cat.set("")
            self.carregar_dados()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao registrar:\n{e}")