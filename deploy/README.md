# Single-port (proxy)

## Desarrollo (puerto 3000)

En desarrollo, el frontend (Next) actúa como proxy del backend mediante `rewrites()`:

- Navegador → `http://localhost:3000`
- `/api/*` → `http://127.0.0.1:8000/*`

Esto elimina CORS y permite que toda la app funcione “desde el puerto 3000”.

## Producción (un solo puerto público)

Usa un reverse proxy (ej. Caddy/Nginx) para enrutar:

- `/api/*` → backend FastAPI
- `/*` → frontend Next

Este repo incluye un ejemplo en `deploy/Caddyfile`.

> Nota: el `Caddyfile` es un ejemplo. Ajusta el puerto público (`:80` / `:443`) y los upstreams según tu despliegue.
