FROM node:22-bookworm-slim AS web
WORKDIR /build
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY apps/engine/ ./engine/
RUN pip install --no-cache-dir './engine[yahoo]'
COPY --from=web /build/dist /app/web-dist
ENV WEB_DIST=/app/web-dist HOST=0.0.0.0
EXPOSE 10000
CMD ["python", "-m", "engine.production"]
