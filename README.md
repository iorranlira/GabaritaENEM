# 🤖 GabaritaENEM — AI Student Assistant

Backend inteligente do GabaritaENEM, simula um tutor acadêmico baseado em múltiplos agentes especializados para auxiliar estudantes na preparação para o ENEM.

---

## 🎯 Visão Geral

O GabaritaENEM utiliza **LangGraph** para orquestrar múltiplos agentes de IA que colaboram para:

- Recuperar e explicar questões do ENEM 
- Gerar simulados personalizados por área de conhecimento
- Encontrar questões semelhantes dado uma questão alvo

### Tecnologias Utilizadas

- **Llama 3.1 8B Instant**: Modelo de linguagem utilizado para raciocínio, geração de respostas e resolução de questões.
- **BAAI/bge-m3 (HuggingFace)**: Modelo de embeddings utilizado para representar semanticamente as questões do ENEM e permitir busca por similaridade.
- **ChromaDB**: Banco vetorial utilizado para armazenar embeddings e realizar recuperação semântica eficiente (RAG).
- **LangGraph** Framework utilizado para orquestrar o fluxo entre agentes, permitindo controle de estados, rotas e colaboração entre diferentes componentes do sistema.
- **LangChain** Utilizado como base para integrações com modelos, retrievers e ferramentas.
- **UV**: Gerenciador moderno de dependências e ambientes Python.
- **PyMuPDF (fitz)**: Utilizado para extração de texto das provas do ENEM em PDF.
---

## 🏗️ Arquitetura dos Agentes

### 1. Supervisor
- **Papel:** Orquestrador do fluxo
- **Função:** Classifica a pergunta em `VÁLIDA` ou `INVÁLIDA` e direciona para o agente correto

### 2. Question Retriever
- **Papel:** Recuperador de questão específica
- **Função:** Busca a questão exata por ano e número via **MCP Tool** (`get_question`), com fallback para busca semântica no ChromaDB

### 3. Similar Retriever
- **Papel:** Recuperador de questões semelhantes
- **Função:** Busca questões semanticamente similares via **MCP Tool** (`get_similar_questions`) para enriquecer o contexto

### 4. Writer
- **Papel:** Professor especialista em ENEM
- **Função:** Gera uma explicação pedagógica estruturada da questão, incluindo análise das alternativas e habilidade avaliada.

### 5. Safety (Self-RAG)
- **Papel:** Verificador de consistência factual
- **Função:** Valida em duas etapas — relevância dos documentos e suporte factual da resposta. Aciona re-busca via MCP em caso de reprovação

### 6. Automation Agent
- **Papel:** Gerador de simulados
- **Função:** Verifica se a resposta está suportada pelos documentos recuperados e aciona nova busca caso necessário.

---

## 🔌 MCP — Model Context Protocol

O sistema implementa um servidor MCP próprio (`mcp-docstore`) que expõe o corpus ENEM como ferramentas padronizadas.

### Ferramentas expostas

| Ferramenta | Descrição | Parâmetros |
|---|---|---|
| `get_question` | Busca questão exata por ano e número | `ano: int`, `numero: int` |
| `get_similar_questions` | Busca questões semanticamente similares | `query: str` |

### Segurança

| Mecanismo | Implementação |
|---|---|
| **Allowlist** | Apenas `get_question` e `get_similar_questions` são expostas |
| **Somente leitura** | Nunca chama `add`, `delete` ou `update` no ChromaDB |
| **Log de auditoria** | Toda chamada registrada em `mcp_calls.log` com timestamp e parâmetros |
| **Limite de resultados** | `k` máximo de 10 para evitar dumps massivos |
| **Sem acesso à rede** | Servidor local via `stdio` sem abrir portas de rede |

---


## 📁 Estrutura do Projeto

```
GabaritaENEM/
├── dataset/
│   ├── gabaritos/          # gabarito_{ano}.pdf
│   ├── provas/             # prova_{ano}.pdf
│   └── processed/          # enem_{ano}.json (dataset chunked)
├── src/
│   ├── agents/
│   │   ├── agent_graph.py      # Grafo LangGraph + nós
│   │   ├── rag_agent.py        # Agentes e prompts
│   │   ├── automation_agent.py # Geração de simulados
│   │   ├── retriever.py        # Conexão com ChromaDB
│   │   ├── embeddings.py       # Instância única do modelo
│   │   └── aux_def_rag.py      # Utilitários RAG
│   ├── mcp_server/
│   │   └── mcp_docstore.py     # Servidor MCP local
│   ├── vectors/                # ChromaDB persistido
│   └── main_agent.py           # Entry point CLI
├── .env
├── pyproject.toml
└── README.md
```

---

## 🚀 Instalação

### Pré-requisitos

- Python >= 3.10 <= 3.15
- `uv` (gerenciador de pacotes)

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/iorranlira/GabaritaENEM

# 2. Navegue até o repositório raiz
cd GabaritaENEM

# 3. Instale o uv
pip install uv

# 4 Criar o ambiente virtual
uv venv

# 5. inicie o uv
source .venv/bin/activate

# 6. Instale as dependências
uv pip install -e .
```

---

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto:

```properties
# LLM
GROQ_API_KEY=sua_chave_groq

# HuggingFace (recomendado para evitar rate limit)
HF_TOKEN=seu_token_hf
```
---

## 🏃 Execução

```bash
# No diretorio raiz, execute:
uv run python -m src.main
```

```
══════════════════════════════════════════
🤖 GabaritaENEM - AI Student Assistant
══════════════════════════════════════════
O que posso fazer:
📚 Buscar e resolver questões do ENEM
📝 Gerar simulados personalizados
🔎 Encontrar questões semelhantes
> Digite sua pergunta:
```

---

## 💬 Exemplos de Uso

**Resolver uma questão específica:**
```
me explique a questao 33 do enem 2023
```

**Gerar simulado:**
```
gere um simulado de matematica e ciencias da natureza com 5 questoes cada
```

---

## 📊 Formato da Resposta

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 QUESTÃO PRINCIPAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENEM {ano} - Questão {número} - {área}
{enunciado completo}
▶ Gabarito: {letra}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EXPLICAÇÃO PEDAGÓGICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 HABILIDADE AVALIADA
✅ POR QUE {gabarito} ESTÁ CORRETA
❌ POR QUE AS OUTRAS ESTÃO ERRADAS
🪜 PASSO A PASSO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 QUESTÕES SEMELHANTES PARA TREINO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
## 🧠 Mecanismo Anti-Alucinação (Self-RAG)

O sistema implementa verificação em duas etapas inspirada no **Self-RAG**:

1. **Relevância dos documentos** — avalia se os chunks recuperados respondem especificamente à pergunta
2. **Suporte factual da resposta** — verifica se todas as afirmações da resposta estão presentes no contexto

Em caso de reprovação:
- **1ª tentativa** → aciona re-busca via MCP com query reformulada
- **2ª tentativa** → recusa formal com mensagem explicativa ao usuário

**Exemplos de input/output esperado (Q&A):**
 
| # | Input | Output esperado |
|---|---|---|
| 1 | `me explique a questão 12 do enem 2019` | Questão 12/2019 com enunciado, gabarito e explicação pedagógica por alternativa |
| 2 | `explique a questão 45 do enem 2021` | Questão 45/2021 com habilidade avaliada, análise das alternativas e passo a passo |
| 3 | `resolva a questão 90 do enem 2022` | Questão 90/2022 com gabarito, justificativa da correta e erros conceituais das demais |
| 4 | `me explique a questão 136 do enem 2020` | Questão 136/2020 de Matemática com resolução detalhada e questões semelhantes |
| 5 | `questão 56 do enem 2018` | Questão 56/2018 com contexto recuperado e citação da fonte (ano, número, área) |
| 6 | `me ajude com a questão 33 do enem 2023` | Questão 33/2023 com explicação estruturada e questões semelhantes para treino |
| 7 | `explique a questão 1 do enem 2015` | Questão 1/2015 de Linguagens com habilidade da matriz ENEM identificada |
| 8 | `me explique o enem 2047` | Recusa: ano fora do banco (2011–2025) |
| 9 | `questão 999 do enem 2020` | Recusa: número de questão fora do intervalo 1–180 |
| 10 | `gabarito` | Recusa: pergunta muito curta ou fora do escopo |
 
---
---

### Automação — Gerar simulados - Tarefas
 
Definição das 5 tarefas de automação avaliadas, com inputs e output esperados.
 
| # | Tarefa | Input | Output esperado | 
|---|---|---|---|
| 1 | Simulado por área única | `"gere um simulado de matematica com 5 questoes"` | 5 questões de Matemática aleatorias formatadas | 
| 2 | Simulado multi-área | `"simulado de humanas e natureza, 3 cada"` | 6 questões distribuídas igualmente | 
| 3 | Simulado todas as áreas | `"quero treinar com questões de todas as áreas"` | 12 questões (3 por área) | 
| 4 | Quantidade customizada | `"me de um simulado com 2 questoes de linguagens"` | Exatamente 2 questões de Linguagens |  
| 5 | Pedido ambíguo | `"quero treinar para o enem"` | Simulado completo com todas as áreas (3 por área)| 
---

## 👥 Autores

- **Iorran Santos de Lira** — [@iorran](https://github.com/iorranlira)
## 📄 Licença

- Este projeto é open source — desenvolvido como Prova de Conceito (PoC) para a disciplina de LLM.
