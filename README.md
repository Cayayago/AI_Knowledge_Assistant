# AI Knowledge Assistant

Primer incremento funcional de un asistente empresarial de conocimiento: una API
**asíncrona, validada, probada y versionada** construida con FastAPI, Pydantic,
AsyncIO y HTTPX.

---

## 1. Requisitos

- Python **3.12 o superior** (`python --version`)
- Git
- Cuenta de GitHub (para publicar el repositorio y crear el Pull Request)

## 2. Estructura del proyecto

```
AI_knowledge_assist_CY/
├── app/
│   ├── main.py                  # Crea la app FastAPI y registra los routers
│   ├── core/config.py           # Nombre, versión, entorno, llm_enabled
│   ├── api/routes/
│   │   ├── health.py            # GET  /health
│   │   ├── chat.py              # POST /api/v1/chat
│   │   └── info.py              # GET  /api/v1/info
│   ├── schemas/                 # Modelos Pydantic (contratos de entrada/salida)
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── info.py
│   └── services/
│       └── assistant_service.py # Lógica del asistente (independiente del router)
├── scripts/
│   ├── asyncio_demo.py          # Secuencial vs. concurrente con asyncio.gather
│   └── httpx_demo.py            # Cliente HTTPX asíncrono contra la API
├── tests/
│   ├── conftest.py              # Cliente HTTPX + ASGITransport (sin servidor externo)
│   ├── unit/                    # Pruebas del servicio y de los schemas
│   └── integration/             # Pruebas de los endpoints
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
pip install -e ".[dev]"
```

> Si PowerShell bloquea la activación, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`


Las dependencias están declaradas en `pyproject.toml`:

- Producción: `fastapi[standard]`, `pydantic`, `httpx`
- Desarrollo (`[dev]`): `pytest`, `pytest-asyncio`

## 4. Ejecutar la API

Con el entorno virtual activado:

```bash
fastapi dev app/main.py
```

Si Windows muestra *"Una directiva de Control de aplicaciones bloqueó este archivo"*
(Smart App Control bloquea los `.exe` del entorno virtual), ejecuta los mismos
comandos a través de Python:

```bash
python -m fastapi dev app/main.py
# o bien
python -m uvicorn app.main:app --reload
```

- API: <http://127.0.0.1:8000>
- Documentación Swagger: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

## 5. Endpoints

| Método | Ruta           | Descripción                                  |
|--------|----------------|----------------------------------------------|
| GET    | `/health`      | Estado del servicio                          |
| POST   | `/api/v1/chat` | Recibe una pregunta y devuelve una respuesta |
| GET    | `/api/v1/info` | Información básica del proyecto              |

### POST /api/v1/chat

Request:

```json
{ "question": "¿Qué es FastAPI?" }
```

Response (200):

```json
{
  "answer": "FastAPI es un framework de Python para construir APIs basado en type hints y ASGI.",
  "provider": "bootstrap-local"
}
```

Regla de validación: `question` debe tener **entre 3 y 2000 caracteres** (se
eliminan espacios al inicio y al final). Si no se cumple, FastAPI responde
**HTTP 422 Unprocessable Entity** con el detalle del error generado por Pydantic.

### GET /api/v1/info

```json
{
  "name": "AI Knowledge Assistant",
  "version": "0.1.0",
  "environment": "development",
  "llm_enabled": false
}
```

### Pruebas manuales rápidas (PowerShell)

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/info
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/chat `
  -ContentType "application/json" -Body '{"question":"¿Qué es FastAPI?"}'
# Entrada inválida -> 422
curl.exe -i -X POST http://127.0.0.1:8000/api/v1/chat -H "Content-Type: application/json" -d '{\"question\":\"a\"}'
```

También se pueden probar todos desde **/docs** con el botón *Try it out*.

## 6. Demostraciones de AsyncIO y HTTPX

```bash
# No requiere la API: compara ejecución secuencial (~3 s) vs concurrente (~1 s)
python scripts/asyncio_demo.py

# Requiere la API corriendo en otra terminal (fastapi dev app/main.py)
python scripts/httpx_demo.py
```

`httpx_demo.py` usa `httpx.AsyncClient` para llamar `/health`, `/api/v1/info`,
envía tres preguntas **en paralelo** con `asyncio.gather` y muestra el 422 de una
pregunta inválida.

## 7. Ejecutar las pruebas

```bash
python -m pytest -q
```

Resultado esperado: `16 passed`.

| ID   | Prueba                                                         | Archivo |
|------|----------------------------------------------------------------|---------|
| T-01 | El servicio responde correctamente a una pregunta conocida     | `tests/unit/test_assistant_service.py` |
| T-02 | `GET /health` → 200                                             | `tests/integration/test_api.py` |
| T-03 | `POST /api/v1/chat` válido → 200                                | `tests/integration/test_api.py` |
| T-04 | `POST /api/v1/chat` pregunta corta → 422                        | `tests/integration/test_api.py` |
| T-05 | `GET /api/v1/info` → 200 y `llm_enabled = false`                | `tests/integration/test_api.py` |
| extra| Límites 3/2000, pregunta muy larga, campo faltante, `/docs`     | `tests/unit/test_schemas.py`, `tests/integration/test_api.py` |

Las pruebas de integración usan `httpx.AsyncClient` con `ASGITransport`, que
invoca la aplicación FastAPI **en memoria**, sin depender de un servidor externo.

## 8. Flujo de una petición

```
Cliente → FastAPI (router) → Pydantic (ChatRequest) → Servicio → Pydantic (ChatResponse) → Cliente
```

1. El cliente envía `POST /api/v1/chat` con un JSON.
2. FastAPI enruta la petición a la función `chat` de `app/api/routes/chat.py`.
3. Antes de ejecutar la función, **Pydantic** valida el cuerpo contra
   `ChatRequest` (tipo `str`, longitud 3–2000). Si falla → **422** y el router
   nunca se ejecuta.
4. El router recibe el objeto ya validado y **delega** en
   `BootstrapAssistantService.answer()` (inyectado con `Depends`).
5. El servicio busca una palabra clave y retorna un `ChatResponse`.
6. FastAPI serializa la respuesta usando `response_model=ChatResponse`.

Gracias a esta separación, en módulos posteriores se podrá reemplazar el
servicio de bootstrap por uno que use un LLM real sin cambiar el router ni los
contratos HTTP.

## 9. Flujo Git utilizado

- **Git** es el sistema de control de versiones que corre en el equipo local
  (commits, ramas, historial).
- **GitHub** es la plataforma en la nube que aloja el repositorio remoto y
  permite colaborar mediante Pull Requests.

Ramas:

- `main`: rama principal (solo el commit inicial).
- `feat/bootstrap-api`: rama de funcionalidad con el incremento, integrada a
  `main` mediante Pull Request.

Commits (Conventional Commits): `chore:`, `feat:`, `test:`, `docs:`.

## 10. Seguridad

- No hay secretos, tokens ni credenciales en el repositorio.
- `.gitignore` excluye `.venv/`, cachés, `.env` y artefactos locales.
