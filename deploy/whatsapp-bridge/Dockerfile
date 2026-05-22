# WhatsApp Web köprüsü — panel konteynerinden ayrı çalışır
FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    WHATSAPP_BRIDGE_PORT=3939

WORKDIR /app

COPY tools/whatsapp_bridge/package.json tools/whatsapp_bridge/package-lock.json ./
RUN npm ci --omit=dev

COPY tools/whatsapp_bridge/server.js ./

EXPOSE 3939

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:'+(process.env.WHATSAPP_BRIDGE_PORT||3939)+'/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "server.js"]
