# Hierarchical, Multi-Tenant Resource Governance & Scheduling Engine

A production-grade, enterprise-ready scheduling and governance platform built with **Python FastAPI**, **SQLAlchemy 2.0 (Async/Await)**, **Asyncpg**, **Alembic**, and an **Angular 19+ SPA** (Standalone Components & Signals).

---

## Architectural Highlights

### 1. Polymorphic Tree Multi-Tenancy Architecture
- **ROOT**: `Organization` node (the Tenant boundary, e.g. Stanford University, Acme Corp).
- **BRANCH 1**: `Folder` node (Logical groupings, e.g. School of Engineering, Executive Leadership).
- **BRANCH 2**: `Project` node (Specific contexts/initiatives, e.g. PhD Advising, Strategic Intake).
- **LEAF**: `Resource` node (Individual human hosts or physical equipment).
- Materialized dot-path traversal (`organization.folder.project.resource`) and PostgreSQL `JSONB` for dynamic tagging, attributes, and capacity bounds.

### 2. Identity vs. Capacity Separation
- Decouples global System Identity (`User`) from Organizational Operational Capacity (`Resource Node`).
- A single User can hold multiple distinct operational host capacities across different organizations with completely independent availability matrices, visibility tiers, and permissions.

### 3. Enterprise Authentication & JIT Auto-Provisioning Engine
- Intercepts OIDC / SAML SSO JWT token assertions (`email`, `organization_domain`, `department`, `roles`, `enrolled_programs`).
- Automatically provisions or matches the Tenant Root Organization, Folder, and Project nodes down the tree path in an atomic async transaction, locking the User as a Leaf Resource node under the exact computed path.
- **HttpOnly Cookie Security**:
  - **Access Token**: 15-minute expiration (`max_age=900`, `HttpOnly`, `SameSite=Lax`).
  - **Refresh Token**: 7-day expiration (`max_age=604800`, `HttpOnly`, `Path=/api/v1/auth/refresh`, `SameSite=Lax`).

### 4. Advanced Visibility & Intent-Based Routing Guardrails
- **Three Exposure Tiers**:
  - `PUBLIC`: Globally searchable and bookable via the external directory.
  - `RESTRICTED`: Filtered from API query payloads unless the viewer holds an authorized organizational role.
  - `HIDDEN`: Completely stripped from public search; visible only to Super Admins and triage officers to prevent calendar hijacking of corporate executives.
- **Intent-Based Screening Pipeline**:
  - Booking requests against protected/hidden nodes are routed through an intermediate Project Node (e.g. Partnership Intake).
  - Triage officers review intake responses and programmatically escalate appointments upward to the executive node via single-use, cryptographically signed escalation tokens.

### 5. Strict Concurrency & Anti-Race Condition Protection
- All slot reservation layers utilize PostgreSQL row-level transaction locks (`SELECT ... FOR UPDATE`) to strictly eliminate double-booking race conditions under high concurrency.

### 6. Dual-Context Angular SPA Frontend
- Main application shell provides an instant toggle between:
  - **Provider View**: Multi-Calendar Synchronization (Google / Outlook), Node Availability Rules Matrix (Angular Reactive Forms), Interactive Intake Form Builder, and Escrow/Payment Config (Stripe / PayPal).
  - **Booker View**: Semantic Unified Directory Workspace (interactive tree & search), Global Time-Zone Engine (detects browser timezone, queries UTC availability, renders conflict-free calendar booking tiles adjusted for DST deltas), and Status Tracker Pipeline.
  - **Triage Screening View**: Review queue for incoming booking intents and programmatic escalation actions.

---

## Directory Structure

```
appointment-manager/
├── docker-compose.yml                     # Infrastructure only: PostgreSQL + Adminer
├── docker-compose.dev.yml                 # Local dev stack: adds backend + frontend services
├── README.md                              # Enterprise deployment & architecture documentation
│
├── backend/                               # Python FastAPI backend
│   ├── Dockerfile.dev                     # Dev image: Python 3.12-slim + uvicorn --reload
│   ├── .env.example                       # Environment configuration template → copy to .env
│   ├── pyproject.toml                     # Project dependencies & tool configs
│   ├── requirements.txt                   # Exact pinned dependencies
│   ├── alembic.ini                        # Alembic async migration configuration
│   ├── alembic/
│   │   ├── env.py                         # Asyncpg migration runner
│   │   └── versions/
│   │       └── 0001_initial_hierarchical_schema.py
│   │
│   ├── app/
│   │   ├── main.py                        # FastAPI factory, CORS, exception handlers, lifespan
│   │   ├── config.py                      # Pydantic Settings (DB URLs, JWT secrets, cookie lifetimes)
│   │   ├── database.py                    # AsyncEngine, async_sessionmaker, DB dependency
│   │   ├── core/                          # Security, JWT tokens, native bcrypt, exceptions
│   │   ├── models/                        # SQLAlchemy 2.0 Async Models
│   │   ├── schemas/                       # Pydantic v2 strict models
│   │   ├── services/                      # JIT Provisioner, Tree Service, Scheduling Engine, Intent Router
│   │   ├── api/v1/                        # FastAPI Routers (Auth, Nodes, Availability, Booking, Search, Integrations)
│   │   └── tests/                         # Pytest-asyncio automated test suite
│   │
└── frontend/                              # Angular SPA
    ├── Dockerfile.dev                     # Dev image: Node 20-alpine + ng serve
    ├── package.json
    ├── angular.json
    ├── src/
    │   ├── styles.css                     # Obsidian Glassmorphism Enterprise Design System
    │   └── app/
    │       ├── core/                      # Services, Models, Signals-based Auth
    │       └── features/
    │           ├── provider-dashboard/    # Host capacity matrix & integrations
    │           ├── booker-dashboard/      # Unified directory & global timezone slot engine
    │           └── triage-portal/         # Intent review queue & escalation
```

---

## Getting Started

### Option A — Docker (recommended)

Spins up the full stack (PostgreSQL, Adminer, FastAPI backend, Angular frontend) with a single command. Source code is bind-mounted so hot-reload works for both services.

```bash
# From the project root
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:4200        |
| Backend  | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |
| Adminer  | http://localhost:8080        |

> **Note:** On first run, copy the environment template before starting:
> ```bash
> cp backend/.env.example backend/.env
> # Windows: Copy-Item backend/.env.example backend/.env
> ```

---

### Option B — Manual (run processes locally)

#### 1. Infrastructure (PostgreSQL + Adminer)
```bash
docker compose up -d
```

#### 2. Backend
From the `backend/` directory:
```bash
# First-time setup
cp .env.example .env   # Windows: Copy-Item .env.example .env
python -m pip install -r requirements.txt

# Run the test suite (JIT provisioning, visibility guardrails, concurrency locks, token rotation)
python -m pytest app/tests -v

# Start the dev server
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation will be available at: `http://localhost:8000/docs`.

#### 3. Frontend
From the `frontend/` directory:
```bash
npm install
npm start
```
The Angular SPA will launch on `http://localhost:4200`.

---

## Exact Pinned Versions Reference
- `fastapi==0.136.1`
- `uvicorn==0.46.0`
- `asyncpg==0.31.0`
- `sqlalchemy==2.0.49`
- `alembic==1.19.2`
- `pydantic>=2.9.0`
- `Angular 19+`
