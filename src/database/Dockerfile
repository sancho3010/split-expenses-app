FROM postgres:16-alpine

# Actualizar paquetes del sistema para corregir CVEs
RUN apk update && apk upgrade --no-cache

# Scripts de inicialización se ejecutan al crear el volumen por primera vez
COPY init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
