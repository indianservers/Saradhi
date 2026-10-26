FROM node:24-alpine AS builder
ARG APP_NAME
WORKDIR /workspace
COPY package.json package-lock.json tsconfig.base.json ./
COPY apps ./apps
COPY packages ./packages
RUN npm ci
RUN npm run build --workspace "@quickbuddy/${APP_NAME}"

FROM node:24-alpine AS runtime
ARG APP_NAME
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    APP_NAME=${APP_NAME}
WORKDIR /app
RUN addgroup -S -g 10001 quickbuddy \
    && adduser -S -u 10001 -G quickbuddy quickbuddy
COPY --from=builder --chown=10001:10001 /workspace/apps/${APP_NAME}/.next/standalone/ ./
COPY --from=builder --chown=10001:10001 /workspace/apps/${APP_NAME}/.next/static/ ./apps/${APP_NAME}/.next/static/
USER 10001:10001
EXPOSE 3000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=20s --timeout=3s --start-period=25s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.status<500?0:1)).catch(()=>process.exit(1))"]
CMD ["sh", "-c", "exec node apps/${APP_NAME}/server.js"]
