# Sistema de Gestão de Padaria (ERP & PDV)

Este é um sistema desktop completo para controle e gestão de padarias, desenvolvido utilizando **Python**, **Tkinter** (para a interface gráfica nativa) e **SQLite** (para armazenamento persistente de dados).

O projeto é estruturado de forma modularizada, separando a lógica de negócios e persistência (Backend) da interface visual (Frontend). Adicionalmente, possui integração nativa com o **Power BI** para relatórios e análises analíticas de faturamento e estoque.

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.x
*   **Interface Gráfica (GUI):** Tkinter & TTK (Themed Tkinter)
*   **Banco de Dados:** SQLite3
*   **Integração Analítica:** Power BI Desktop (via arquivos CSV exportados).

---

## 📁 Estrutura do Projeto

```text
projeto-padaria/
│
├── main.py                 # Ponto de entrada do sistema (GUI)
├── exportar_tudo.py        # Script standalone para exportar dados para CSV
├── Dashboard_padaria.pbix  # Dashboard analítico pronto para o Power BI
├── .gitignore              # Impede o envio de caches e base de dados local
├── README.md               # Este arquivo de documentação
│
├── banco/
│   ├── setup.py            # Script DDL para criar e inicializar as tabelas
│   └── padaria.db          # Arquivo SQLite gerado localmente (ignorado pelo git)
│
├── backend/
│   ├── conexao.py          # Gerenciamento de contexto da conexão SQLite
│   ├── usuarios.py         # Cadastro, listagem e autenticação de usuários
│   ├── produtos.py         # Cadastro de produtos e ficha técnica
│   ├── insumos.py          # Controle de estoque de matérias-primas
│   ├── vendas.py           # Registro de vendas e baixa automática de insumos
│   ├── financeiro.py       # Fluxo de caixa, despesas e receitas avulsas
│   ├── exportacao.py       # Funções auxiliares de exportação de tabelas para CSV
│   └── simulador.py        # Script para popular banco com dados massivos de teste (Fase 3)
│
├── exportacoes/            # Diretório contendo os arquivos CSV para o Power BI
│   ├── vendas.csv
│   ├── itens_venda.csv
│   ├── estoque.csv
│   └── ...
│
└── frontend/
    ├── app.py              # Controlador principal da janela Tkinter (Navegação de telas)
    └── views/              # Telas individuais da aplicação (Frames do Tkinter)
        ├── login.py        # Autenticação de usuários
        ├── menu.py         # Menu lateral e sidebar de navegação
        ├── pdv.py          # Frente de caixa (Carrinho, cálculo de totais e venda)
        ├── estoque.py      # Painel de controle de estoque de insumos
        ├── produtos.py     # Cadastro unificado de produtos e fichas técnicas
        ├── financeiro.py   # Registro de despesas e recebimentos avulsas (com botões de CSV)
        └── cadastros.py    # Telas de suporte (Categorias de produto/financeiras e novos usuários)
```

---

## 🚀 Como Rodar o Projeto em Qualquer Máquina

Siga as instruções passo a passo para configurar e rodar o projeto do zero:

### 1. Clonar o Repositório
Abra um terminal (Prompt de Comando ou PowerShell) e execute o comando:
```bash
git clone https://github.com/JoaoLua/projeto-padaria.git
cd projeto-padaria
```

### 2. Inicializar o Banco de Dados
Como o banco de dados local (`padaria.db`) está adicionado ao `.gitignore` para evitar envio de dados de cache de forma binária, você precisará inicializar a estrutura de tabelas em sua máquina rodando o script de configuração:
```bash
python banco/setup.py
```
*Este comando criará o arquivo `padaria.db` dentro da pasta `banco` com todas as tabelas e relacionamentos necessários.*

### 3. (Opcional) Popular o Banco com Dados Simulados
Se você deseja popular o banco de dados com dados reais de teste para fins de demonstração (incluindo insumos, categorias e histórico de vendas):
```bash
python backend/simulador.py
```
*Isso gerará transações de venda fictícias e inserirá usuários padrões para que o sistema não inicie totalmente vazio.*

### 4. Executar o Sistema
Para abrir a interface gráfica do programa, execute:
```bash
python main.py
```

---

## 🔑 Credenciais de Acesso Padrão

Após inicializar e rodar o simulador, você pode acessar o sistema utilizando a seguinte credencial padrão:

*   **Administrador:**
    *   **Login:** `admin`
    *   **Senha:** `123`

---

## 📊 Integração com Power BI (Painel de Indicadores)

O projeto possui um painel analítico avançado criado no Power BI Desktop (`Dashboard_padaria.pbix`). Para carregar seus dados locais nele:

### 1. Exportar Dados para CSV
Você pode exportar todas as tabelas do banco de dados SQLite para arquivos CSV formatados em PT-BR (separador `;` e codificação `UTF-8 BOM`) de duas formas:
- **Pela Interface Gráfica:** Clicando nos botões **⬇ Exportar CSV** disponíveis nas tabelas do sistema.
- **Pelo Terminal (Standalone):** Rodando o script unificado na raiz do projeto:
  ```bash
  python exportar_tudo.py
  ```
*Todos os arquivos CSV serão salvos automaticamente na pasta `./exportacoes/`.*

### 2. Atualizar o Relatório no Power BI
1. Instale o [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (caso ainda não o possua).
2. Abra o arquivo **`Dashboard_padaria.pbix`** na raiz do projeto.
3. No menu superior, clique em **Atualizar** (Refresh) para recarregar todos os dados a partir dos arquivos CSV salvos na pasta `exportacoes`.
4. *Nota:* Se o Power BI exibir um erro de caminho ao tentar ler os arquivos, vá em **Transformar Dados** > **Configurações da Fonte de Dados**, clique em **Alterar Fonte** e selecione o caminho absoluto da pasta `exportacoes` em seu computador.
