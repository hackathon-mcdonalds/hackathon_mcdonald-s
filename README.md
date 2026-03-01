# CibusChain

Infraestructura tecnológica para el rescate de alimentos preparados en el sector de comida rápida.

**Hackathon:** Feed the Future — Genius Arena 2026 (McDonald's Track)

---

## Requisitos

Antes de empezar, necesitas tener instalado en tu máquina:

| Herramienta | Versión mínima | Para qué sirve |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 4.x | Corre la base de datos y la API en contenedores |
| [Node.js](https://nodejs.org/) | 20.x | Necesario para el dashboard |
| [pnpm](https://pnpm.io/installation) | 8.x | Gestor de paquetes del monorepo |
| [Python](https://www.python.org/downloads/) | 3.12 | Para la API y Sentinel |
| [Git](https://git-scm.com/) | cualquiera | Control de versiones |

---

## Setup inicial (una sola vez)

### 1. Clona el repositorio

```bash
git clone https://github.com/TU_USUARIO/cibuschain.git
cd cibuschain
```

### 2. Instala dependencias de Node

```bash
pnpm install
```

### 3. Configura variables de entorno de la API

```bash
cp apps/api/.env.example apps/api/.env
# Edita apps/api/.env si necesitas cambiar algo (en dev los valores por defecto funcionan)
```

### 4. Instala dependencias de Python

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
cd ../..
```

### 5. Levanta la base de datos y la API

```bash
docker compose up
# Espera a ver: "database system is ready to accept connections"
```

### 6. Aplica las migraciones (crea las tablas)

En una segunda terminal:

```bash
cd apps/api
source .venv/bin/activate
alembic upgrade head
```

Si ves `INFO [alembic.runtime.migration] Running upgrade ...` sin errores, todo está bien.

### 7. Verifica que todo funciona

Abre en tu navegador:
- **http://localhost:8000/health** → debe devolver `{"status": "ok"}`
- **http://localhost:8000/docs** → documentación interactiva de la API

---

## Flujo de trabajo diario

```bash
# Levanta el entorno (cada vez que vayas a trabajar)
docker compose up

# En otra terminal, trabaja en tu feature
git checkout -b feature/nombre-de-tu-feature

# Cuando termines
git add .
git commit -m "feat(missions): implementar endpoint de aceptar misión"
git push origin feature/nombre-de-tu-feature
# → Crea un Pull Request en GitHub
```

---

## Estructura del proyecto

```
cibuschain/
├── apps/
│   ├── api/                    ← Backend FastAPI (Python)
│   │   ├── app/
│   │   │   ├── main.py         ← Punto de entrada de la API
│   │   │   ├── core/
│   │   │   │   ├── config.py   ← Variables de entorno y configuración
│   │   │   │   └── database.py ← Conexión a PostgreSQL
│   │   │   ├── models/
│   │   │   │   └── models.py   ← Definición de todas las tablas (10 modelos)
│   │   │   ├── routers/        ← Endpoints agrupados por recurso
│   │   │   │   ├── missions.py
│   │   │   │   ├── branches.py
│   │   │   │   ├── volunteers.py
│   │   │   │   ├── receivers.py
│   │   │   │   ├── sentinel.py
│   │   │   │   └── fiscal.py
│   │   │   ├── schemas/        ← Validación de datos de entrada/salida (Pydantic)
│   │   │   └── services/       ← Lógica de negocio (Sentinel ML, FiscalFlow, etc.)
│   │   ├── migrations/         ← Migraciones de Alembic (versiones del schema)
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   ├── dashboard/              ← Frontend Next.js (TypeScript)
│   └── mobile/                 ← App móvil Expo (React Native)
│
├── packages/
│   └── shared/                 ← Tipos y utilidades compartidos
│
├── docker-compose.yml          ← Entorno local completo con un comando
├── scripts/
│   └── db_init.sql             ← Extensiones de PostgreSQL (corre automático)
└── README.md
```

---

## Convenciones de Git

### Formato de commits

```
tipo(scope): descripción corta en presente

Ejemplos:
feat(sentinel): implementar cálculo de Pis con GaussianNB
fix(missions): corregir race condition en aceptar misión
docs(readme): agregar instrucciones de setup para Windows
test(fiscal): agregar tests para generación de reporte mensual
refactor(db): extraer lógica de conexión a módulo separado
```

**Tipos:**
- `feat` — nueva funcionalidad
- `fix` — corrección de bug
- `docs` — solo documentación
- `test` — tests
- `refactor` — reorganización de código sin cambiar comportamiento
- `chore` — cambios de configuración, dependencias

### Ramas

```
main          ← producción / demos (siempre debe funcionar)
develop       ← integración de features en desarrollo
feature/xxx   ← tu trabajo nuevo
fix/xxx       ← corrección de bug
```

**Regla:** nunca trabajas directamente en `main`. Todo entra por Pull Request.

---

## Comandos útiles

```bash
# Base de datos
docker compose up postgres          # solo la BD
docker compose down -v              # borra todos los datos (reset total)
alembic revision --autogenerate -m "descripción"  # crea nueva migración
alembic upgrade head                # aplica migraciones
alembic downgrade -1               # revierte última migración

# API
uvicorn app.main:app --reload       # corre la API en modo desarrollo
pytest                              # corre todos los tests
pytest tests/test_missions.py       # tests de un archivo específico

# Docker
docker compose logs api             # logs de la API
docker compose logs postgres        # logs de la BD
docker compose ps                   # estado de los contenedores
```

---

## Arquitectura del sistema

```
┌─────────────────┐    REST    ┌──────────────────────────────────┐
│   POS Oracle    │──────────▶│                                  │
│   Symphony      │           │         FastAPI                  │
└─────────────────┘           │         (apps/api)               │
                              │                                  │
┌─────────────────┐  WebSocket│  ┌──────────┐  ┌─────────────┐  │
│  App Móvil      │◀─────────▶│  │ Sentinel │  │ FiscalFlow  │  │
│  Voluntarios    │           │  │  (ML)    │  │  (Reportes) │  │
└─────────────────┘           │  └──────────┘  └─────────────┘  │
                              └──────────┬───────────────────────┘
┌─────────────────┐                      │
│  Dashboard      │◀────────────────────▶│ PostgreSQL + Redis
│  Next.js        │                      │
└─────────────────┘                      │
```

---

## Preguntas frecuentes

**¿Por qué Docker?** Para que el entorno sea idéntico en todas las máquinas del equipo. "En mi máquina funciona" desaparece como problema.

**¿Por qué pnpm?** Más rápido que npm, comparte librerías entre las tres apps del monorepo en lugar de descargar copias duplicadas.

**¿Qué es Alembic?** El sistema de control de versiones de la base de datos. Como Git, pero para el schema. Cada cambio al schema se registra como una migración que puede aplicarse o revertirse.

**¿Cómo agrego un endpoint nuevo?** Edita el router correspondiente en `apps/api/app/routers/`, define el schema Pydantic en `schemas/`, implementa la lógica en `services/`.

---

*CibusChain — Feed the Future · Genius Arena 2026*
