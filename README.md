# report-api — API de Consulta de Relatórios 

API REST read-only para consulta dos relatórios de análise arquitetural gerados pelo `ia-service`. Integra-se ao API Gateway e ao `streamlit-app` do projeto FIAP Hackathon.

---
 
## Índice
 
1. [Descrição do Problema](#1-descrição-do-problema)
2. [Arquitetura Proposta](#2-arquitetura-proposta)
3. [Fluxo da Solução](#3-fluxo-da-solução)
4. [Instruções de Execução](#4-instruções-de-execução)

---

## 1. Descrição do Problema

Sistemas de análise arquitetural baseados em IA produzem relatórios complexos — riscos identificados, recomendações, métricas de qualidade — que precisam ser consumidos de forma confiável por múltiplos clientes (frontend, gateway, outros serviços). O desafio está em expor esses dados sem acoplar o mecanismo de consulta ao mecanismo de geração, e sem comprometer a integridade dos dados já persistidos.

**Contexto do ecossistema:**

| Serviço | Porta | Papel |
|---|---|---|
| `ia-service` | 8000 | Recebe diagramas, executa análise com IA + RAG, escreve relatórios no banco |
| `report-api` | 8001 | Lê e expõe relatórios (read-only) — este serviço |
| `streamlit-app` | — | Frontend que consome o `report-api` |

**Problema específico:** como estruturar o serviço de consulta de forma que regras de domínio, lógica de aplicação e detalhes de infraestrutura não se misturem, garantindo testabilidade e independência de frameworks?

---

## 2. Arquitetura Proposta

O serviço adota **Clean Architecture**, organizando o código em quatro camadas concêntricas com dependências que apontam sempre para o centro.

```
┌──────────────────────────────────────────────────────────┐
│  INFRA (Frameworks & Drivers)                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ADAPTERS (Interface Adapters)                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  APPLICATION (Use Cases)                     │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │  DOMAIN (Entities & Business Rules)    │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Estrutura de Pastas

```
app/
├── main.py                              # Entry point (shim → infra/main/app.py)
│
├── domain/                              # Camada mais interna — zero dependências externas
│   ├── entities/
│   │   ├── analysis.py                  # Entidade Analysis (id, status, file_name…)
│   │   └── report.py                    # Entidade Report (componentes, riscos, QA…)
│   ├── value_objects/
│   │   ├── analysis_id.py               # UUID imutável com igualdade por valor
│   │   └── analysis_status.py           # Enum dos status válidos do domínio
│   └── exceptions/
│       ├── base.py                      # DomainException (base hierárquica)
│       └── analysis_not_found.py        # AnalysisNotFoundError (nomeado pelo negócio)
│
├── application/                         # Casos de uso — depende só do domínio
│   ├── ports/
│   │   ├── input/
│   │   │   ├── i_get_report_use_case.py    # Interface IGetReportUseCase
│   │   │   └── i_list_reports_use_case.py  # Interface IListReportsUseCase
│   │   └── output/
│   │       ├── i_analysis_repository.py    # Interface IAnalysisRepository
│   │       └── i_report_repository.py      # Interface IReportRepository
│   ├── use_cases/
│   │   ├── get_report_use_case.py       # Busca analysis + report, lança exceção se ausente
│   │   └── list_reports_use_case.py     # Lista paginada com dados de analysis
│   └── dto/
│       ├── get_report_dto.py            # GetReportInputDTO, ReportDTO, GetReportOutputDTO
│       └── list_reports_dto.py          # ListReportsInputDTO, ReportSummaryDTO, ListReportsOutputDTO
│
├── adapters/                            # Implementações das interfaces — depende de application
│   ├── mappers/
│   │   ├── analysis_mapper.py           # dict (SQL row) → Analysis entity
│   │   └── report_mapper.py             # dict (SQL row) → Report entity
│   ├── repositories/
│   │   ├── sqlalchemy_analysis_repository.py   # Implementa IAnalysisRepository
│   │   └── sqlalchemy_report_repository.py     # Implementa IReportRepository
│   ├── controllers/
│   │   └── report_controller.py         # Monta InputDTO, chama use case, trata exceções de domínio → HTTP
│   └── presenters/
│       └── report_presenter.py          # OutputDTO → dict JSON para a resposta HTTP
│
├── infra/                               # Camada mais externa — frameworks e drivers
│   ├── database/
│   │   └── connection.py               # Engine SQLAlchemy, pool, get_db, check_db_connection
│   ├── http/
│   │   ├── server.py                   # Instância FastAPI com lifespan e registro de routers
│   │   └── routes/
│   │       ├── health_routes.py        # GET /health
│   │       └── report_routes.py        # GET /reports e GET /reports/{id} — composition local
│   └── main/
│       └── app.py                      # Composition root: aquece o engine e cria o app
│
└── utils/
    └── logger.py                        # structlog JSON — preocupação transversal
```

### Princípios aplicados

| Princípio | Como se manifesta |
|---|---|
| **Regra de dependência** | Importações sempre apontam para o centro: `infra → adapters → application → domain` |
| **Inversão de dependência** | Use cases dependem de `IAnalysisRepository` (interface), não de `SqlAlchemyAnalysisRepository` (concreta) |
| **Separação de responsabilidade** | Controller extrai parâmetros; use case orquestra; mapper converte; presenter formata |
| **Domínio puro** | `domain/` não importa FastAPI, SQLAlchemy ou qualquer biblioteca externa |
| **Exceções semânticas** | `AnalysisNotFoundError` carrega o `analysis_id`; o controller a converte em HTTP 404 |

---

## 3. Fluxo da Solução

### GET /reports/{analysis_id}

```
HTTP Request
    │
    ▼
report_routes.py          ← extrai analysis_id do path, obtém Session via Depends
    │  monta controller
    ▼
ReportController          ← chama use case via interface IGetReportUseCase
    │  GetReportInputDTO(analysis_id)
    ▼
GetReportUseCase          ← orquestra: busca analysis, busca report
    │
    ├─► IAnalysisRepository.find_by_id()
    │       └─► SqlAlchemyAnalysisRepository
    │               └─► SELECT * FROM analyses WHERE id = :id
    │               └─► AnalysisMapper.to_domain(row) → Analysis entity
    │
    ├─► [AnalysisNotFoundError se analysis é None]
    │
    └─► IReportRepository.find_by_analysis_id()
            └─► SqlAlchemyReportRepository
                    └─► SELECT * FROM reports WHERE analysis_id = :id ORDER BY created_at DESC LIMIT 1
                    └─► ReportMapper.to_domain(row) → Report entity
    │
    ▼
GetReportOutputDTO        ← ReportDTO.from_entity(report) converte entidade → DTO
    │
    ▼
ReportPresenter           ← serializa DTO → dict JSON
    │
    ▼
HTTP Response 200
```

### GET /reports?limit=20&offset=0

```
HTTP Request
    │
    ▼
report_routes.py          ← extrai limit/offset dos query params
    │
    ▼
ReportController          ← chama use case via IListReportsUseCase
    │  ListReportsInputDTO(limit, offset)
    ▼
ListReportsUseCase
    │
    └─► IReportRepository.list_with_analysis(limit, offset)
            └─► SqlAlchemyReportRepository
                    └─► SELECT r.*, a.status, a.file_name, a.created_at
                            FROM reports r JOIN analyses a ON r.analysis_id = a.id
                            ORDER BY r.created_at DESC LIMIT :limit OFFSET :offset
    │
    ▼  [ReportSummaryDTO.from_row(row) para cada linha]
ListReportsOutputDTO
    │
    ▼
ReportPresenter           ← serializa lista de ReportSummaryDTO → dict JSON
    │
    ▼
HTTP Response 200
```

### Tratamento de erro

```
AnalysisNotFoundError (domain)
    └─► capturada em ReportController.handle_get_report()
            └─► raise HTTPException(status_code=404, detail=str(exc))
```

O domínio lança exceções nomeadas pelo negócio, sem conhecer HTTP. O controller faz a tradução na borda do adaptador.

---

## 4. Instruções de Execução

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.12+ (apenas para execução local sem Docker)

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `POSTGRES_USER` | `hackathon` | Usuário do banco |
| `POSTGRES_PASSWORD` | `hackathon123` | Senha do banco |
| `POSTGRES_DB` | `hackathon_db` | Nome do banco |
| `POSTGRES_HOST` | `localhost` | Host do banco |
| `POSTGRES_PORT` | `5432` | Porta do banco |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`) |

### Opção 1 — Standalone com Docker (banco incluso)

Sobe o PostgreSQL com o schema inicializado e o `report-api` em um único comando:

```bash
docker compose -f docker-compose.standalone.yml up --build
```

A API estará disponível em `http://localhost:8001`.

### Opção 2 — Integrado ao ia-service

Se o `ia-service` já estiver rodando com o banco compartilhado:

```bash
docker compose up --build
```

O `report-api` conecta ao banco gerenciado externamente via rede Docker.

### Opção 3 — Desenvolvimento local (sem Docker)

```bash
# 1. Suba apenas o banco
docker compose -f docker-compose.standalone.yml up pgvector -d

# 2. Configure o ambiente Python
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

# 3. Inicie a API com hot-reload
uvicorn app.main:app --reload --port 8001
```

### Verificar saúde

```bash
curl http://localhost:8001/health
# {"status": "healthy", "db": "connected"}
```

### Consultar relatórios

```bash
# Listar (paginado)
curl "http://localhost:8001/reports?limit=10&offset=0"

# Detalhe por ID
curl "http://localhost:8001/reports/550e8400-e29b-41d4-a716-446655440000"
```

### Resposta de exemplo — GET /reports/{analysis_id}

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analisado",
  "file_name": "diagrama.png",
  "created_at": "2026-04-02T21:30:00",
  "report": {
    "id": "7f3e9c00-...",
    "executive_summary": "A arquitetura apresenta baixo acoplamento entre serviços...",
    "components_identified": ["API Gateway", "Auth Service", "User DB"],
    "architectural_risks": [
      {
        "type": "SPOF",
        "description": "User DB sem réplica de leitura",
        "severity": "ALTO",
        "mitigation": "Adicionar réplica read-only com failover automático"
      }
    ],
    "recommendations": ["Configurar DLQ no SQS", "Implementar circuit breaker"],
    "rag_used": true,
    "qa_is_valid": true,
    "qa_completeness_score": 0.92,
    "qa_issues_found": [],
    "qa_quality_notes": "Relatório completo e consistente.",
    "created_at": "2026-04-02T21:30:05",
    "updated_at": "2026-04-02T21:30:05"
  }
}
```

### Documentação interativa

Com a API rodando, acesse:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

---

## 5. Diagramas de Arquitetura

Diagramas Mermaid gerados por análise reversa do código-fonte. Renderizam nativamente no GitHub.

### 5.1 Arquitetura Interna — Camadas Hexagonais

Mostra as camadas Clean Architecture e direção de dependência.

```mermaid
graph TD
    subgraph "Infra Layer"
        MAIN["app.infra.main.app"]
        SERVER["FastAPI Server"]
        ROUTES_R["report_routes"]
        ROUTES_H["health_routes"]
        DB_CONN["DB Connection - SQLAlchemy"]
    end

    subgraph "Adapters Layer"
        CTRL["ReportController"]
        REPO_A["SqlAlchemyAnalysisRepository"]
        REPO_R["SqlAlchemyReportRepository"]
        MAPPER_A["AnalysisMapper"]
        MAPPER_R["ReportMapper"]
        PRESENTER["ReportPresenter"]
    end

    subgraph "Application Layer"
        UC_GET["GetReportUseCase"]
        UC_LIST["ListReportsUseCase"]
        PORT_IN_GET["IGetReportUseCase"]
        PORT_IN_LIST["IListReportsUseCase"]
        PORT_OUT_A["IAnalysisRepository"]
        PORT_OUT_R["IReportRepository"]
        DTO_GET["GetReportDTO"]
        DTO_LIST["ListReportsDTO"]
    end

    subgraph "Domain Layer"
        ENT_A["Analysis Entity"]
        ENT_R["Report Entity"]
        VO_ID["AnalysisId"]
        VO_STATUS["AnalysisStatus"]
        EXC["AnalysisNotFoundError"]
    end

    MAIN --> SERVER
    SERVER --> ROUTES_R
    SERVER --> ROUTES_H
    ROUTES_R --> CTRL
    CTRL --> UC_GET
    CTRL --> UC_LIST
    UC_GET -.->|implements| PORT_IN_GET
    UC_LIST -.->|implements| PORT_IN_LIST
    UC_GET --> PORT_OUT_A
    UC_GET --> PORT_OUT_R
    UC_LIST --> PORT_OUT_R
    REPO_A -.->|implements| PORT_OUT_A
    REPO_R -.->|implements| PORT_OUT_R
    REPO_A --> MAPPER_A
    REPO_R --> MAPPER_R
    MAPPER_A --> ENT_A
    MAPPER_R --> ENT_R
    ENT_A --> VO_ID
    ENT_A --> VO_STATUS
    UC_GET --> EXC
    ROUTES_R --> PRESENTER
    REPO_A --> DB_CONN
    REPO_R --> DB_CONN
```

### 5.2 Fluxo de Request — GET /reports/{analysis_id}

Ciclo completo com caminhos de sucesso e falha.

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI as FastAPI Router
    participant Ctrl as ReportController
    participant UC as GetReportUseCase
    participant ARepo as AnalysisRepository
    participant RRepo as ReportRepository
    participant DB as PostgreSQL pgvector
    participant Presenter as ReportPresenter

    Client->>FastAPI: GET /reports/{analysis_id}
    FastAPI->>Ctrl: handle_get_report(id)
    Ctrl->>UC: execute(GetReportInputDTO)
    UC->>ARepo: find_by_id(analysis_id)
    ARepo->>DB: SELECT * FROM analyses WHERE id = :id
    alt Analysis not found
        DB-->>ARepo: null
        ARepo-->>UC: None
        UC-->>Ctrl: raise AnalysisNotFoundError
        Ctrl-->>FastAPI: HTTPException 404
        FastAPI-->>Client: 404 Not Found
    else Analysis found
        DB-->>ARepo: row
        ARepo-->>UC: Analysis entity
        UC->>RRepo: find_by_analysis_id(id)
        RRepo->>DB: SELECT * FROM reports WHERE analysis_id = :id
        DB-->>RRepo: row or null
        RRepo-->>UC: Report entity or None
        UC-->>Ctrl: GetReportOutputDTO
        Ctrl->>Presenter: to_get_response(output)
        Presenter-->>FastAPI: JSON dict
        FastAPI-->>Client: 200 OK
    end
```

### 5.3 Visão Macro — Contexto no Ecossistema Distribuído

Posição do report-service no sistema ArchAnalyzer (inferido do schema e referências).

```mermaid
graph LR
    subgraph "Client"
        USER["User / API Gateway"]
    end

    subgraph "Upstream Services"
        UPLOAD["Upload Service"]
        EXTRACT["Extraction Agent"]
        REPORT_AGENT["Report Agent"]
        QA["QA Validator"]
    end

    subgraph "Infrastructure"
        S3["AWS S3"]
        SQS["AWS SQS"]
        PG["PostgreSQL + pgvector"]
    end

    subgraph "Report Service"
        API["FastAPI :8001"]
    end

    USER -->|upload diagram| UPLOAD
    UPLOAD -->|store file| S3
    UPLOAD -->|enqueue| SQS
    SQS -->|consume| EXTRACT
    EXTRACT -->|write extraction_results| PG
    EXTRACT -->|trigger| REPORT_AGENT
    REPORT_AGENT -->|write reports| PG
    REPORT_AGENT -->|trigger| QA
    QA -->|update qa fields| PG
    USER -->|GET /reports| API
    API -->|read| PG
```

### 5.4 Schema do Banco — Diagrama ER

```mermaid
erDiagram
    analyses {
        UUID id PK
        VARCHAR status
        VARCHAR file_name
        VARCHAR file_type
        VARCHAR s3_key
        VARCHAR sqs_message_id
        TEXT error_message
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    extraction_results {
        UUID id PK
        UUID analysis_id FK
        JSONB components
        JSONB relationships
        JSONB patterns
        TEXT raw_description
        TIMESTAMPTZ created_at
    }

    reports {
        UUID id PK
        UUID analysis_id FK
        JSONB components_identified
        JSONB architectural_risks
        JSONB recommendations
        TEXT executive_summary
        BOOLEAN rag_used
        BOOLEAN qa_is_valid
        FLOAT qa_completeness_score
        JSONB qa_issues_found
        TEXT qa_quality_notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    analyses ||--o{ extraction_results : has
    analyses ||--o{ reports : has
```

### 5.5 Máquina de Estados — Analysis

```mermaid
stateDiagram-v2
    [*] --> recebido: Upload received
    recebido --> em_processamento: Agent picks up
    em_processamento --> analisado: Success
    em_processamento --> erro: Failure
    erro --> [*]
    analisado --> [*]
```

### 5.6 Pipeline CI/CD

```mermaid
flowchart TD
    subgraph "Feature Branch"
        F1["Push to feature/*"]
        F2["CI: lint + test"]
    end

    subgraph "Develop Branch"
        D1["Push to develop"]
        D2["Run tests"]
        D3["Calculate semver"]
        D4["Create release branch + PR"]
    end

    subgraph "Release Branch"
        R1["PR merged to release/*"]
        R2["CI: validate"]
    end

    subgraph "Main Branch"
        M1["Push to main"]
        M2["Terraform init"]
        M3["Terraform apply"]
        M4["Deploy to AWS"]
    end

    F1 --> F2
    F2 -->|merge| D1
    D1 --> D2 --> D3 --> D4
    D4 --> R1 --> R2
    R2 -->|merge to main| M1
    M1 --> M2 --> M3 --> M4
```
