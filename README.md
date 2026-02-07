# Open-Meteo Weather API (Django + DRF + Pandas)

Proyecto Django/DRF que:
1) Carga datos horarios históricos (temperatura y precipitación) desde Open-Meteo a SQLite mediante un comando.
2) Expone endpoints REST para obtener estadísticas de temperatura, precipitación y un resumen global.
3) Separa responsabilidades: `clients/` (Open-Meteo), `services/` (lógica), `api/` (DRF y modelos).

El proyecto está preparado tanto para **desarrollo** como para **producción**, manteniendo entornos completamente separados.

---

## Stack
- Python
- Django
- Django REST Framework
- Pandas
- Open-Meteo (archive + geocoding)
- SQLite
- Docker / Docker Compose

---

## Estructura del proyecto

- `clients/open_meteo.py`: cliente para Open-Meteo (geocoding + archive).
- `api/`: modelos, serializers, views, urls y comando Django.
- `services/`: lógica de negocio (queries, stats, exceptions).
- `project/settings.py`: configuración base.
- `project/dev.py`: overrides para desarrollo y Docker.
- `project/prod.py`: configuración de producción (sin afectar a dev)
- `Dockerfile`: imagen base.
- `docker-compose.yml`: entorno de desarrollo.
- `docker-compose.prod.yml`: entorno de producción.

Modelos principales:
- `City`: ciudad (`name` + `country_code` únicos).
- `WeatherDataset`: dataset por ciudad y rango (`city + start_date + end_date` únicos).
- `WeatherHour`: fila horaria por dataset (`dataset + timestamp` únicos).

---

## Requisitos

- Docker
- Docker Compose

(No es necesario instalar Python localmente)

---

## Arranque con Docker (recomendado)

### Build y levantar el servidor
```bash
docker compose up --build
```

La API estará disponible en:
```
http://localhost:8000/api/
```

Las migraciones se ejecutan automáticamente al arrancar el contenedor.

---

## Ejecutar comandos Django

### Cargar datos desde Open-Meteo
```bash
docker compose exec web python manage.py loadcitydata Madrid 2024-07-01 2024-07-03 --countryISO ES --replace
```

### Crear superusuario
```bash
docker compose exec web python manage.py createsuperuser
```

---

## Producción (Docker)

El entorno de producción está completamente separado y **no modifica** ningún archivo de desarrollo.

### Archivos específicos de producción
- `requirements.prod.txt`
- `project/prod.py`
- `docker-compose.prod.yml`

### Variables de entorno requeridas
En producción deben definirse, como mínimo:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`

Opcionales:
- `SQLITE_PATH`
- `LOG_DIR`

### Arrancar producción (ejemplo local)
```bash
DJANGO_SECRET_KEY=change-me DJANGO_ALLOWED_HOSTS=localhost \
docker compose -f docker-compose.prod.yml up --build
```

Producción utiliza:
- `gunicorn` como servidor WSGI
- `whitenoise` para servir archivos estáticos
- `collectstatic` automático en el arranque

---

## Endpoints disponibles

### 1) Estadísticas de temperatura
`GET /api/weather/temperature/`

Query params:
- `city` (str)
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `above` (float, opcional, default: 30)
- `below` (float, opcional, default: 0)

Ejemplo:
```bash
curl "http://localhost:8000/api/weather/temperature/?city=Madrid&start_date=2024-07-01&end_date=2024-07-03"
```

---

### 2) Estadísticas de precipitación
`GET /api/weather/precipitation/`

Query params:
- `city`
- `start_date`
- `end_date`

Ejemplo:
```bash
curl "http://localhost:8000/api/weather/precipitation/?city=Madrid&start_date=2024-07-01&end_date=2024-07-03"
```

---

### 3) Resumen global
`GET /api/weather/summary/`

Ejemplo:
```bash
curl "http://localhost:8000/api/weather/summary/"
```

---

## Tests

Los tests están organizados en:
```
api/tests/
```

Ejecutar tests con Docker:
```bash
docker compose run --rm test
```

---

## Admin

Panel de administración:
```
http://localhost:8000/admin/
```

---

## Persistencia de datos

- SQLite se persiste mediante volúmenes Docker.
- Los logs se escriben en un volumen independiente.
- Los archivos estáticos se recopilan en producción en `/staticfiles`.

---

## Decisiones de diseño

- Arquitectura en capas (`clients`, `services`, `api`).
- Serializers DRF como contrato de entrada y salida.
- Lógica de negocio aislada en `services`.
- Entornos dev y prod completamente separados.
- Docker como fuente única de verdad del entorno.
- Tests deterministas sin dependencias de red.
