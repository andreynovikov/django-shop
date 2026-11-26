FROM node:22.23.4-bookworm-slim AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./

RUN npm ci --no-update-notifier

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

# The configuration (the GitHub environment's ENV_FILE) is not in the build context, see .dockerignore. The build gets
# it as a secret, mounted only while it runs, because Next inlines NEXT_PUBLIC_* and pre-renders pages from the API.
# It is mounted as .env.local, which Next loads but doesn't copy into .next/standalone, as it does .env, so no layer
# keeps it. The container gets the same file at runtime as /app/.env.local, see startup.sh.
RUN --mount=type=secret,id=storefront_env,target=/app/.env.local,required=true npm run build

FROM base AS runner
WORKDIR /app

# The storefront's name, the only line that differs between the storefronts' copies of this file
ARG entity=sworld

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
