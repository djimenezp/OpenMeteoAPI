# Open-Meteo Weather API (Django + DRF + Pandas)

Proyecto Django/DRF que:
1) Carga datos horarios históricos (temperatura y precipitación) desde Open-Meteo a SQLite mediante un comando.
2) Expone endpoints REST para obtener estadísticas de temperatura, precipitación y un resumen global.
3) Separa responsabilidades: `clients/` (Open-Meteo), `services/` (lógica), `api/` (DRF y modelos).

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
- `Dockerfile`, `docker-compose.yml`: entorno containerizado.

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

- SQLite se almacena en un volumen Docker (`sqlite_data`).
- Los logs se escriben en el volumen `logs`.

Esto evita problemas de entorno y permite reiniciar contenedores sin perder datos.

---

## Decisiones de diseño

- Arquitectura en capas (`clients`, `services`, `api`).
- Serializers DRF como contrato de entrada y salida.
- Lógica de negocio aislada en `services`.
- Docker como fuente única de verdad del entorno.
- Tests deterministas sin dependencias de red.
