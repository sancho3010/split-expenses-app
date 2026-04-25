FROM nginx:1.27-alpine

# Actualizar paquetes del sistema para corregir CVEs (openssl, libxml2, libpng, musl, zlib)
RUN apk update && apk upgrade --no-cache

# Reemplazar la config principal de nginx completa
COPY nginx.conf /etc/nginx/nginx.conf

# Eliminar configs default que puedan incluir listen 80
RUN rm -f /etc/nginx/conf.d/*

# Copiar archivos estáticos
COPY index.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# Run nginx as non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid
USER nginx

EXPOSE 8080
