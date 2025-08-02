# Plataforma RAG - Converse com seus Dados

Este projeto é uma plataforma de Recuperação Aumentada por Geração (RAG) que permite ao usuário fazer upload de documentos (PDF, DOCX, MD) ou inserir textos, processá-los e conversar com seus dados utilizando modelos de linguagem via Ollama.

## Sumário

- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Como rodar com Docker Compose](#como-rodar-com-docker-compose)
- [Serviços](#serviços)
- [Como usar](#como-usar)
- [Desenvolvimento](#desenvolvimento)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Licença](#licença)

---

## Arquitetura

O sistema é composto por três serviços principais, orquestrados via Docker Compose:

- **Ollama**: Servidor de modelos de linguagem e embeddings.
- **API Backend (FastAPI)**: Responsável pelo processamento, vetorização e interface de chat.
- **Frontend (Streamlit)**: Interface web para upload, inserção de texto e chat.

## Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Como rodar com Docker Compose

1. Clone este repositório:
   ```sh
   git clone https://github.com/seu-usuario/guideagent_api.git
   cd guideagent_api
   ```

2. Suba todos os serviços:
   ```sh
   docker-compose up --build
   ```

3. Acesse o frontend em [http://localhost:8501](http://localhost:8501).

## Serviços

### 1. Ollama

- Gerencia e serve os modelos de linguagem e embeddings.
- Modelos são definidos pelas variáveis de ambiente `EMBEDDING_MODEL` e `LLM_MODEL` no `docker-compose.yml`.
- Persistência dos modelos em `ollama_data/`.

### 2. API Backend (FastAPI)

- Processa uploads de arquivos e textos, realiza a vetorização e armazena os embeddings usando ChromaDB.
- Expõe endpoints REST:
  - `POST /upload`: Upload e processamento de arquivos.
  - `POST /add_text`: Processamento de texto livre.
  - `POST /chat`: Chat com os dados processados.
  - `GET /`: Endpoint raiz.
- Persistência dos vetores em `chroma_data/`.

### 3. Frontend (Streamlit)

- Interface web para upload de arquivos, inserção de texto e chat.
- Comunicação com a API via REST.

## Como usar

1. **Adicionar Conhecimento**:
   - Faça upload de arquivos PDF, DOCX ou MD pela barra lateral, ou insira texto manualmente.
   - Clique em "Processar Arquivo" ou "Processar Texto" para vetorização.

2. **Chat**:
   - Digite sua pergunta no campo de chat.
   - O assistente irá responder com base nos documentos/textos processados.

## Desenvolvimento

### Rodando localmente sem Docker

#### Backend (API)

```sh
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend

```sh
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

#### Ollama

Siga as instruções em [https://ollama.com/](https://ollama.com/) para instalar e rodar o servidor localmente.

### Variáveis de Ambiente

- `EMBEDDING_MODEL`: Nome do modelo de embedding (ex: `nomic-embed-text`)
- `LLM_MODEL`: Nome do modelo de linguagem (ex: `llama3.2:1b`)
- `OLLAMA_HOST`: URL do serviço Ollama (ex: `http://localhost:11434`)
- `API_URL`: URL da API backend (usado pelo frontend)

## Estrutura do Projeto

```
guideagent_api/
├── api/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── ollama/
│   ├── Dockerfile
│   └── entrypoint.sh
├── docker-compose.yml
└── readme.md
```

## Licença

Este projeto está sob a licença ......