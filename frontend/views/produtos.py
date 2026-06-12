import tkinter as tk
from tkinter import ttk, messagebox
from backend.produtos import listar_produtos, inserir_produto, vincular_ficha_tecnica, obter_ficha_tecnica
from backend.categorias import listar_categorias_produto
from backend.insumos import listar_insumos
from backend.exportacao import exportar_produtos

class ProdutosView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.categorias_cache = []
        self.produtos_cache = []
        self.insumos_cache = []
        self.temp_insumos_list = [] # List of dicts: {"id_insumo", "nome", "quantidade"}
        
        self._build_ui()
        
    def _build_ui(self):
        # Título da tela
        lbl_titulo = ttk.Label(self, text="Cadastro de Produtos e Fichas Técnicas", font=("Arial", 16, "bold"))
        lbl_titulo.pack(pady=10)
        
        # Container principal (Dividido em duas colunas)
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Coluna da Esquerda: Formulário de Cadastro (Largura fixa sugerida: 420px)
        self.left_frame = ttk.Frame(container, width=420)
        self.left_frame.pack(side="left", fill="both", padx=10, pady=5)
        self.left_frame.pack_propagate(False) # Mantém a largura especificada
        
        # Coluna da Direita: Listagem e Detalhes
        self.right_frame = ttk.Frame(container)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)
        
        # Construir cada painel
        self._build_form_cadastro()
        self._build_listagem_detalhes()
        
    def _build_form_cadastro(self):
        # LabeledFrame Dados Básicos
        f_dados = ttk.LabelFrame(self.left_frame, text=" Dados do Produto ", padding=10)
        f_dados.pack(fill="x", pady=5)
        
        f_dados.columnconfigure(1, weight=1)
        
        ttk.Label(f_dados, text="Nome:").grid(row=0, column=0, sticky="w", pady=5)
        self.p_nome = ttk.Entry(f_dados)
        self.p_nome.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(f_dados, text="Preço Venda:").grid(row=1, column=0, sticky="w", pady=5)
        self.p_preco = ttk.Entry(f_dados)
        self.p_preco.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(f_dados, text="Categoria:").grid(row=2, column=0, sticky="w", pady=5)
        self.p_cat = ttk.Combobox(f_dados, state="readonly")
        self.p_cat.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Checkbox para ativar ficha técnica
        self.var_has_recipe = tk.BooleanVar(value=False)
        self.chk_recipe = ttk.Checkbutton(
            self.left_frame, 
            text="Este produto possui receita (ficha técnica)?", 
            variable=self.var_has_recipe,
            command=self.toggle_recipe_frame
        )
        self.chk_recipe.pack(anchor="w", pady=10)
        
        # LabeledFrame Ficha Técnica Builder
        self.f_recipe = ttk.LabelFrame(self.left_frame, text=" Ingredientes da Receita ", padding=10)
        self.f_recipe.pack(fill="both", expand=True, pady=5)
        
        # Form de adição de insumo na receita temporária
        f_add_insumo = ttk.Frame(self.f_recipe)
        f_add_insumo.pack(fill="x", pady=5)
        
        ttk.Label(f_add_insumo, text="Insumo:").grid(row=0, column=0, sticky="w", pady=2)
        self.combo_insumo = ttk.Combobox(f_add_insumo, state="readonly", width=25)
        self.combo_insumo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(f_add_insumo, text="Qtd:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_insumo_qtd = ttk.Entry(f_add_insumo, width=10)
        self.entry_insumo_qtd.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.btn_add_temp = ttk.Button(f_add_insumo, text="Adicionar", command=self.add_temp_insumo)
        self.btn_add_temp.grid(row=1, column=1, sticky="e", padx=5, pady=2)
        
        # Tabela temporária de insumos no formulário
        columns = ("Insumo", "Quantidade")
        self.tree_temp = ttk.Treeview(self.f_recipe, columns=columns, show="headings", height=5)
        self.tree_temp.heading("Insumo", text="Insumo")
        self.tree_temp.heading("Quantidade", text="Quantidade")
        self.tree_temp.column("Insumo", anchor="w")
        self.tree_temp.column("Quantidade", anchor="center", width=100)
        self.tree_temp.pack(fill="both", expand=True, pady=5)
        
        self.btn_rem_temp = ttk.Button(self.f_recipe, text="Remover Selecionado", command=self.remove_temp_insumo)
        self.btn_rem_temp.pack(anchor="e", pady=2)
        
        # Botão principal de cadastro
        self.btn_cadastrar = ttk.Button(self.left_frame, text="Cadastrar Produto Completo", command=self.salvar_produto_completo)
        self.btn_cadastrar.pack(fill="x", pady=10)
        
        # Inicializa o estado dos campos da receita desativado
        self.toggle_recipe_frame()
        
    def _build_listagem_detalhes(self):
        # Tabela de Produtos Cadastrados
        f_lista = ttk.LabelFrame(self.right_frame, text=" Produtos no Catálogo ", padding=10)
        f_lista.pack(fill="both", expand=True, pady=5)
        
        columns = ("ID", "Nome", "Preço Venda", "Categoria", "Possui Receita?")
        self.tree_prod = ttk.Treeview(f_lista, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree_prod.heading(col, text=col)
            self.tree_prod.column(col, anchor="center")
        self.tree_prod.column("Nome", anchor="w", width=150)
        self.tree_prod.pack(fill="both", expand=True, pady=5)

        btn_csv = ttk.Button(f_lista, text="⬇ Exportar CSV", command=exportar_produtos)
        btn_csv.pack(anchor="e", padx=5, pady=(0, 5))

        # Bind de seleção para mostrar a receita detalhada
        self.tree_prod.bind("<<TreeviewSelect>>", self.mostrar_detalhes_produto)
        
        # Detalhes da Ficha Técnica do Produto Selecionado
        self.f_detalhes = ttk.LabelFrame(self.right_frame, text=" Receita / Ficha Técnica (Detalhes) ", padding=10)
        self.f_detalhes.pack(fill="x", pady=5)
        
        columns_det = ("Insumo", "Unidade", "Qtd. Necessária")
        self.tree_detalhes_ficha = ttk.Treeview(self.f_detalhes, columns=columns_det, show="headings", height=5)
        for col in columns_det:
            self.tree_detalhes_ficha.heading(col, text=col)
            self.tree_detalhes_ficha.column(col, anchor="center")
        self.tree_detalhes_ficha.column("Insumo", anchor="w", width=180)
        self.tree_detalhes_ficha.pack(fill="both", expand=True, pady=5)
        
    def toggle_recipe_frame(self):
        state = "normal" if self.var_has_recipe.get() else "disabled"
        self._set_state_recursive(self.f_recipe, state)
        if not self.var_has_recipe.get():
            self.temp_insumos_list.clear()
            self._atualizar_tabela_temp()
            self.entry_insumo_qtd.delete(0, tk.END)
            self.combo_insumo.set("")
            
    def _set_state_recursive(self, widget, state):
        try:
            # ttk widgets e widgets nativos suportam configuração de state
            widget.configure(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, state)
            
    def add_temp_insumo(self):
        idx = self.combo_insumo.current()
        if idx == -1:
            messagebox.showwarning("Aviso", "Selecione um insumo.")
            return
            
        try:
            qtd = float(self.entry_insumo_qtd.get().replace(",", "."))
            if qtd <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Informe uma quantidade válida.")
            return
            
        insumo = self.insumos_cache[idx]
        id_insumo = insumo["id_insumo"]
        nome_insumo = insumo["nome"]
        unidade = insumo["unidade_medida"]
        
        # Verificar duplicados na lista temporária
        for item in self.temp_insumos_list:
            if item["id_insumo"] == id_insumo:
                item["quantidade"] += qtd
                self._atualizar_tabela_temp()
                self.entry_insumo_qtd.delete(0, tk.END)
                return
                
        self.temp_insumos_list.append({
            "id_insumo": id_insumo,
            "nome": f"{nome_insumo} ({unidade})",
            "quantidade": qtd
        })
        self._atualizar_tabela_temp()
        self.entry_insumo_qtd.delete(0, tk.END)
        
    def remove_temp_insumo(self):
        selected = self.tree_temp.selection()
        if not selected: return
        
        indices = [self.tree_temp.index(item) for item in selected]
        for idx in sorted(indices, reverse=True):
            del self.temp_insumos_list[idx]
            
        self._atualizar_tabela_temp()
        
    def _atualizar_tabela_temp(self):
        for item in self.tree_temp.get_children():
            self.tree_temp.delete(item)
        for item in self.temp_insumos_list:
            self.tree_temp.insert("", "end", values=(item["nome"], item["quantidade"]))
            
    def salvar_produto_completo(self):
        nome = self.p_nome.get().strip()
        idx_cat = self.p_cat.current()
        
        try:
            preco = float(self.p_preco.get().replace(",", "."))
            if not nome or idx_cat == -1 or preco < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Preencha os dados básicos do produto corretamente.")
            return
            
        # Validar se marcou que possui receita mas não inseriu nenhum ingrediente
        has_recipe = self.var_has_recipe.get()
        if has_recipe and not self.temp_insumos_list:
            messagebox.showwarning("Aviso", "Adicione pelo menos um ingrediente na receita ou desmarque a opção.")
            return
            
        id_cat = self.categorias_cache[idx_cat]['id']
        
        try:
            # 1. Insere o produto
            id_produto = inserir_produto(id_cat, nome, preco, 0.0)
            
            # 2. Se possuir receita, insere no banco
            if has_recipe:
                for item in self.temp_insumos_list:
                    vincular_ficha_tecnica(id_produto, item["id_insumo"], item["quantidade"])
                    
            messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
            
            # Limpa o formulário
            self.p_nome.delete(0, tk.END)
            self.p_preco.delete(0, tk.END)
            self.p_cat.set("")
            self.var_has_recipe.set(False)
            self.toggle_recipe_frame()
            
            # Atualiza o catálogo
            self.carregar_dados()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao cadastrar produto:\n{e}")
            
    def carregar_dados(self):
        try:
            self.categorias_cache = listar_categorias_produto()
            self.p_cat['values'] = [c['nome'] for c in self.categorias_cache]
            
            self.insumos_cache = listar_insumos()
            self.combo_insumo['values'] = [f"{i['nome']} ({i['unidade_medida']})" for i in self.insumos_cache]
            
            self.produtos_cache = listar_produtos()
            
            # Recarregar tabela principal de produtos
            for item in self.tree_prod.get_children():
                self.tree_prod.delete(item)
                
            for p in self.produtos_cache:
                # Verificar se possui receita chamando o backend ou buscando do cache
                ficha = obter_ficha_tecnica(p['id'])
                possui_receita = "Sim" if len(ficha) > 0 else "Não"
                
                self.tree_prod.insert("", "end", values=(
                    p['id'], 
                    p['nome'], 
                    f"R$ {p['preco_venda']:.2f}", 
                    p['categoria_nome'],
                    possui_receita
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}")
            
    def mostrar_detalhes_produto(self, event=None):
        selected = self.tree_prod.selection()
        for item in self.tree_detalhes_ficha.get_children():
            self.tree_detalhes_ficha.delete(item)
            
        if not selected: return
        
        idx = self.tree_prod.index(selected[0])
        id_produto = self.produtos_cache[idx]['id']
        
        try:
            ficha = obter_ficha_tecnica(id_produto)
            for f in ficha:
                self.tree_detalhes_ficha.insert("", "end", values=(
                    f['insumo_nome'], 
                    f['unidade_medida'], 
                    f['quantidade_necessaria']
                ))
        except Exception as e:
            pass
            
    def on_show(self):
        self.carregar_dados()