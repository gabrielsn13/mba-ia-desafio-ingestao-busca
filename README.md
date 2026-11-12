# Ingestão e Busca Semântica com LangChain e Postgres

Aplicação de linha de comando que responde perguntas com base no conteúdo de um PDF. O projeto usa Python, LangChain, OpenAI e PostgreSQL com pgvector.

Na ingestão, o PDF é dividido em trechos de até 1000 caracteres, com overlap de 150, e seus embeddings são armazenados no banco. Para cada pergunta, a aplicação busca os 10 trechos mais relevantes e os envia como contexto à LLM. O prompt instrui o modelo a não usar informações externas; ainda assim, confira as respostas no documento.

## Pré-requisitos

- Python 3.12.
- Docker e Docker Compose; no Windows, abra o Docker Desktop e aguarde sua inicialização.
- Uma chave da [API OpenAI](https://platform.openai.com/) e créditos disponíveis. A assinatura do ChatGPT não inclui créditos da API. Consulte os [modelos disponíveis](https://platform.openai.com/docs/models) e seus preços antes de usar.

Execute os comandos abaixo na **raiz do projeto**, onde ficam `docker-compose.yml` e `requirements.txt`.

## 1. Instalar as dependências

No Windows PowerShell:

```powershell
py -3.12 -m venv venv312
.\venv312\Scripts\python.exe -m pip install -r requirements.txt
```

No Linux ou macOS:

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Configurar o ambiente

Crie o `.env` local a partir do template **apenas se ele ainda não existir**, para não sobrescrever suas configurações.

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

No Linux ou macOS:

```bash
cp .env.example .env
```

Edite o `.env` e preencha as variáveis:

```env
OPENAI_API_KEY=sua-chave-da-openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=nome-do-modelo-de-chat
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/rag
PG_VECTOR_COLLECTION_NAME=pdf_document
PDF_PATH=document.pdf
```

Substitua a chave e escolha um modelo de chat disponível na sua conta. O Compose publica o PostgreSQL na porta **5433** da máquina; o `.env.example` pode conter `5432`, portanto confira e ajuste a `DATABASE_URL` no seu `.env`. Se alterar usuário, senha, porta ou banco no Compose, ajuste a conexão também.

O `.env` é ignorado pelo Git: **não publique nem compartilhe sua chave**. As credenciais do PostgreSQL no exemplo são apenas para desenvolvimento local.

## 3. Iniciar o banco

```bash
docker compose up -d
docker compose ps
```

Aguarde o serviço `postgres` ficar `healthy`. O serviço `bootstrap_vector_ext` inicializa a extensão pgvector e pode aparecer como encerrado; confira sua conclusão com:

```bash
docker compose ps -a
```

O status esperado para ele é `Exited (0)`. O volume do Docker mantém os dados entre reinicializações.

## 4. Ingerir o PDF

No Windows PowerShell:

```powershell
.\venv312\Scripts\python.exe src\ingest.py
```

No Linux ou macOS, com o ambiente virtual ativado:

```bash
python src/ingest.py
```

Ao concluir, o script informa a quantidade de trechos armazenados. Use o mesmo modelo de embeddings para ingestão e busca. Se trocar o modelo ou alterar o PDF, os vetores antigos podem permanecer ou ser incompatíveis; remova os dados antigos apropriados e reingira o documento. Remover o volume do Docker apaga todos os dados nele.

## 5. Iniciar o chat

No Windows PowerShell:

```powershell
.\venv312\Scripts\python.exe src\chat.py
```

No Linux ou macOS, com o ambiente virtual ativado:

```bash
python src/chat.py
```

Digite uma pergunta e pressione Enter. Para encerrar, digite `sair`.

Teste uma pergunta cuja resposta esteja no PDF e outra fora do contexto. Para informações ausentes, o prompt solicita a resposta: **“Não tenho informações necessárias para responder sua pergunta.”** A resposta é gerada por uma LLM e não é garantida em todos os casos.

## Estrutura

```text
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── document.pdf
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
└── README.md
```

Projeto baseado no [desafio de ingestão e busca semântica](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca).
