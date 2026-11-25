FROM node:22.23.4-bookworm-slim AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./

RUN npm ci --no-update-notifier

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
# The sources include .env, which CI writes from the GitHub environment's ENV_FILE: it is baked into the image
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM base AS runner
WORKDIR /app

# The storefront's name, the only line that differs between the storefronts' copies of this file
ARG entity=dortak

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder /app/container-entrypoint.sh /app/startup.sh ./
# Fails the build if the base image has no setpriv, which container-entrypoint.sh needs
RUN command -v setpriv

EXPOSE 3000

ENV PORT=3000
ENV STOREFRONT_PROCESS_NAME=${entity}

# The entrypoint drops privileges before startup.sh syncs assets and execs Node.
ENTRYPOINT ["/bin/sh", "/app/container-entrypoint.sh"]
CMD ["/bin/sh", "./startup.sh"]
