FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# (Opcional) si alguna dependencia necesitara compilación.
# Normalmente pandas/requests vienen en wheel y no hace falta.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Selector de requirements (dev/prod)
ARG REQUIREMENTS=dev

# Copiamos ambos ficheros para poder elegir en build-time
COPY requirements.txt /app/requirements.txt
COPY requirements.prod.txt /app/requirements.prod.txt

# Instala según entorno
RUN if [ "$REQUIREMENTS" = "prod" ]; then \
      pip install --no-cache-dir -r /app/requirements.prod.txt ; \
    else \
      pip install --no-cache-dir -r /app/requirements.txt ; \
    fi

# Crear usuario non-root
RUN useradd -m appuser
USER appuser

COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
