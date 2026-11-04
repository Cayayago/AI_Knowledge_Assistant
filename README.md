# AI Knowledge Assistant — API con integración LLM (Módulo 1)

API **asíncrona, validada, probada y versionada** construida con FastAPI, Pydantic,
AsyncIO y HTTPX, que responde preguntas usando un **LLM real a través de
[OpenRouter](https://openrouter.ai)**.

- **Módulo 0 (v0.1.0):** base de la API con un servicio local de bootstrap, sin LLM.
- **Módulo 1 (v0.2.0):** el servicio de bootstrap se reemplaza por un proveedor LLM
  (OpenRouter). Los contratos HTTP, la validación y la estructura se mantienen.

---

## 1. Requisitos

- Python **3.12 o superior** (`python --version`)
- Git
- Una API key de OpenRouter: <https://openrouter.ai/keys>

## 2. Estructura del proyecto

```
AI_knowledge_assist_CY/
├── app/
│   ├── main.py                  # Crea la app FastAPI y registra los routers
│   ├── core/config.py           # Configuración: lee .env (API key, modelo, entorno)
│   ├── api/
│   │   ├── chat.py              # POST /api/v1/chat (usa el servicio + proveedor LLM)
│   │   └── routes/
│   │       ├── health.py        # GET  /health
│   │       └── info.py          # GET  /api/v1/info
│   ├── schemas/                 # Modelos Pydantic (contratos de entrada/salida)
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── info.py
│   ├── services/
│   │   └── assistant_service.py # Arma el prompt (system + user) y llama al proveedor
│   └── providers/
│       ├── base.py              # Contrato LLMProvider (Protocol) + LLMProviderError
│       └── openrouter.py        # Implementación con httpx.AsyncClient contra OpenRouter
├── scripts/
│   ├── asyncio_demo.py          # Secuencial vs. concurrente con asyncio.gather
│   └── httpx_demo.py            # Cliente HTTPX asíncrono contra la API
├── tests/
│   ├── conftest.py              # FakeProvider + cliente HTTPX en memoria
│   ├── unit/                    # Servicio, proveedor OpenRouter (simulado) y schemas
│   └── integration/             # Endpoints completos (sin llamar a internet)
├── .env.example                 # Plantilla de variables de entorno (sin secretos)
├── .gitignore
├── pyproject.toml
└── README.md
```

## 3. Instalación

### Windows (PowerShell)

```powershell
cd "ruta\a\AI_knowledge_assist_CY"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

> Si PowerShell bloquea la activación, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Dependencias (en `pyproject.toml`):

- Producción: `fastapi[standard]`, `pydantic`, `httpx`, `python-dotenv`
- Desarrollo (`[dev]`): `pytest`, `pytest-asyncio`

## 4. Configurar OpenRouter

1. Copia la plantilla: `copy .env.example .env` (Windows) o `cp .env.example .env`.
2. Abre `.env` y pega tu API key:

   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_MODEL=openrouter/free
   ```

| Variable | Obligatoria | Valor por defecto | Para qué sirve |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Sí | (vacía) | Autenticación con OpenRouter |
| `OPENROUTER_MODEL` | No | `openrouter/free` | Modelo a usar (`openrouter/free` elige uno gratuito) |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | URL de la API |
| `APP_ENV` | No | `development` | Entorno que muestra `/api/v1/info` |

> **Seguridad:** `.env` está en `.gitignore` y **nunca** se sube a GitHub. Solo se
> versiona `.env.example`, que no contiene secretos.

Sin API key la API arranca igual, pero `POST /api/v1/chat` responde **502** y
`/api/v1/info` muestra `"llm_enabled": false`.

## 5. Ejecutar la API

```powershell
python -m fastapi dev app/main.py
# o bien
python -m uvicorn app.main:app --reload
```

> Se usa `python -m ...` porque en algunos equipos Windows (Smart App Control)
> bloquea `fastapi.exe` con el mensaje *"Una directiva de Control de aplicaciones
> bloqueó este archivo"*.

- API: <http://127.0.0.1:8000>
- Documentación Swagger: <http://127.0.0.1:8000/docs>

## 6. Endpoints

| Método | Ruta           | Descripción                                   |
|--------|----------------|-----------------------------------------------|
| GET    | `/health`      | Estado del servicio                           |
| POST   | `/api/v1/chat` | Envía una pregunta al LLM y devuelve la respuesta |
| GET    | `/api/v1/info` | Información del proyecto y del LLM configurado |

### POST /api/v1/chat

Request (solo `question` es obligatorio):

```json
{
  "question": "¿Qué es FastAPI?",
  "temperature": 0.3,
  "top_p": 1.0,
  "max_tokens": 300
}
```

| Campo | Regla | Por defecto | Qué controla |
|---|---|---|---|
| `question` | 3 a 2000 caracteres | — | La pregunta |
| `temperature` | 0 a 1.5 | 0.3 | Creatividad: bajo = más preciso, alto = más variado |
| `top_p` | mayor que 0 y hasta 1 | 1.0 | Fracción de tokens candidatos que el modelo considera |
| `max_tokens` | 1 a 2000 | 300 | Longitud máxima de la respuesta |

Response (200):

```json
{
  "answer": "FastAPI es un framework de Python para construir APIs...",
  "provider": "openrouter",
  "model": "openrouter/free"
}
```

Códigos de respuesta:

| Código | Cuándo |
|---|---|
| **200** | El LLM respondió correctamente |
| **422** | El body no cumple las reglas de Pydantic (el LLM no se llama) |
| **502** | Falló el proveedor LLM: sin API key, timeout, error HTTP de OpenRouter o respuesta inválida |

### GET /api/v1/info

```json
{
  "name": "AI Knowledge Assistant",
  "version": "0.2.0",
  "environment": "development",
  "llm_enabled": true,
  "llm_provider": "openrouter",
  "llm_model": "openrouter/free"
}
```

## 7. Ejecutar las pruebas

```powershell
python -m pytest -q
```

Resultado esperado: `37 passed`.

Las pruebas **no llaman a internet ni gastan créditos**:

- `tests/conftest.py` define un `FakeProvider` y, con `app.dependency_overrides`,
  reemplaza el servicio real en las pruebas de integración.
- `tests/unit/test_openrouter_provider.py` prueba el código real de
  `OpenRouterProvider` usando `httpx.MockTransport`, que simula las respuestas
  de OpenRouter (éxito, 401, timeout, formato inválido).
- Las pruebas ignoran la API key de tu `.env`.

| Archivo | Qué prueba |
|---|---|
| `tests/unit/test_assistant_service.py` | El servicio arma el prompt (system + user) y pasa los parámetros |
| `tests/unit/test_openrouter_provider.py` | Petición correcta a OpenRouter y manejo de errores |
| `tests/unit/test_schemas.py` | Validaciones de `ChatRequest` |
| `tests/integration/test_api.py` | `/health`, `/api/v1/chat` (200, 422, 502), `/api/v1/info`, `/docs` |

## 8. Flujo de una petición

```
Cliente → FastAPI (router) → Pydantic (ChatRequest) → AssistantService → OpenRouterProvider → OpenRouter (LLM)
                                                                                    ↓
Cliente ← ChatResponse (answer, provider, model) ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← respuesta
```

1. El cliente envía `POST /api/v1/chat`.
2. Pydantic valida el body. Si falla → **422** y nada más se ejecuta.
3. FastAPI inyecta el servicio con `Depends(get_assistant_service)`, que crea el
   `OpenRouterProvider` con la configuración del `.env`.
4. `AssistantService` arma los mensajes (`system` con las instrucciones del
   asistente + `user` con la pregunta) y llama a `provider.generate(...)`.
5. `OpenRouterProvider` hace `await client.post(".../chat/completions")` con
   `httpx.AsyncClient` y extrae `choices[0].message.content`.
6. Si el proveedor falla lanza `LLMProviderError`, y el router responde **502**.

El servicio depende del **contrato** `LLMProvider` (un `Protocol`), no de
OpenRouter. Por eso en las pruebas se usa un proveedor falso, y en el futuro se
podría cambiar de proveedor sin tocar el servicio ni el router.

## 9. Demostraciones de AsyncIO y HTTPX

```bash
python scripts/asyncio_demo.py      # no requiere la API
python scripts/httpx_demo.py        # requiere la API corriendo en otra terminal
```

## 10. Flujo Git utilizado

- `main`: rama principal.
- `feat/bootstrap-api`: Módulo 0 (API base sin LLM).
- `feature/module-1-llm-integration`: Módulo 1 (integración con OpenRouter).

Commits con Conventional Commits: `chore:`, `feat:`, `test:`, `docs:`.

## 11. Seguridad

- La API key solo vive en `.env`, que está en `.gitignore`.
- No hay secretos, tokens ni credenciales en el repositorio.
