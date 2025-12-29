FROM node:22.18.0-bookworm-slim AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./

RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

FROM base AS runner
WORKDIR /app

ARG entity=sworld

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder /app/startup.sh ./
RUN mv ./server.js ./${entity}.js

USER node

EXPOSE 3000

ENV PORT 3000
ENV APP_MAIN_FILE ${entity}.js

CMD /bin/sh startup.sh ${APP_MAIN_FILE}
