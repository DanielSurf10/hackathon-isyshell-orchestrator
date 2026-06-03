# IsyShell — Orquestrador Automático de Infraestrutura

O **IsyShell** é um microsserviço seguro, auditável e conteinerizado projetado para eliminar gargalos operacionais e a necessidade de acessos manuais via SSH. A plataforma permite que equipes de suporte gerenciem, consultem e executem scripts de manutenção de forma isolada diretamente dentro do ecossistema de microserviços, utilizando uma arquitetura baseada em **Zero Trust** e **Event-Driven Alerts**.

---

## 🛠️ Stack Tecnológica

* **Backend Framework:** FastAPI (Python 3.11+)
* **Servidor ASGI:** Uvicorn
* **Banco de Dados:** SQLite
* **ORM:** SQLAlchemy 2.0 & Pydantic v2
* **Orquestração de Containers:** Docker SDK for Python
* **Autenticação:** PyJWT (JSON Web Tokens)
* **Comunicação e Alertas:** HTTPX (Chamadas assíncronas)

---

## 🏗️ Diferenciais de Arquitetura & Engenharia

### 1. Segurança Avançada (Handshake JWT)
Em vez de trafegar um token estático de longa vida em operações críticas, o IsyShell adota um modelo de **redução de superfície de ataque**. Um token permanente corporativo (`X-Isy-Token`) é utilizado estritamente como credencial de serviço na rota de autenticação para emitir um **JWT (JSON Web Token) de curta duração**. Todas as rotas administrativas e operacionais exigem esse JWT.

### 2. Isolamento Real via Docker SDK
Para evitar a fragilidade e os riscos de segurança (como *Command Injection*) de abrir terminais locais no host via `subprocess`, o IsyShell consome o **Docker SDK nativo via Unix Socket** (`/var/run/docker.sock`). O microsserviço localiza o container alvo programaticamente e injeta a execução do script no exato *namespace* e *workdir* desejado, mantendo a imutabilidade das imagens originais.

### 3. Execução Concorrente e Assíncrona (Fire-and-Forget)
Processos de manutenção longos (como limpezas profundas de banco de dados) rodam de forma assíncrona em segundo plano utilizando `BackgroundTasks`. A API valida o script instantaneamente (*Pre-flight Check*) e responde com status `202 Accepted`, liberando o cliente enquanto o motor conclui a tarefa.

### 4. Roteamento de Alertas com Padrão Mediator
O sistema implementa o padrão de projeto **Mediator** (combinado com *Strategy*) para o gerenciamento de notificações. Quando uma rotina falha, o executor central propaga o erro para o `AlertDispatcher`. Este mediador distribui o payload do erro de forma assíncrona para todos os canais de comunicação configurados (ex: Telegram Bots, Discord Webhooks, E-mail) sem que a lógica de infraestrutura precise conhecer os destinos finais.

---

## 🗄️ Modelagem do Banco de Dados

* **`users`**: Registra os operadores e analistas de suporte.
* **`api_tokens`**: Armazena de forma individual as chaves permanentes de acesso vinculadas a cada usuário, permitindo revogação seletiva.
* **`scripts`**: Catálogo e metadados das rotinas Bash disponíveis (`path`, parâmetros permitidos e status lógico).
* **`execution_logs`**: Trilha forense e de auditoria completa, registrando `horário`, `script_id`, `target_container`, `user_id` (quem executou), `exit_code` e os logs de saída (`stdout`/`stderr`).

---

## 🔌 Contrato da API (Endpoints Principais)

### Autenticação (Pública)
* `POST /api/v1/auth/token` -> Troca o token permanente individual por um Token Bearer JWT.

### Administração (Protegidas por JWT)
* `GET /api/v1/admin/scripts` -> Lista o catálogo de scripts ativos.
* `POST /api/v1/admin/scripts/create` -> Registra uma nova rotina de manutenção.
* `PUT /api/v1/admin/scripts/{script_id}/status` -> Ativa/Desativa scripts logicamente (Soft Delete).
* `GET /api/v1/admin/execution-logs` -> Trilha completa de auditoria.
* `GET /api/v1/admin/execution-logs/container/{name}/errors` -> Histórico filtrado de falhas por container.

### Operação (Protegidas por JWT)
* `POST /api/v1/ops/execute` -> Dispara a execução de um script em um container específico (suporta flag `run_in_background`).
* `POST /api/v1/ops/execute-many` -> Orquestra e dispara manutenções em lote para múltiplos alvos simultaneamente.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Docker e Docker Compose instalados na máquina host.

### Inicialização rápida
1. Clone o repositório e navegue até a pasta do projeto.
2. Certifique-se de que o Docker Socket possui permissões de leitura no seu ambiente de desenvolvimento.
3. Suba o ecossistema com o comando:
   ```bash
   docker compose up -d
