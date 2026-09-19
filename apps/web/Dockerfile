# Build context = REPO ROOT (compose: context: ., dockerfile: apps/web/Dockerfile)
FROM node:24-alpine AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
WORKDIR /repo

# --- deps: workspace manifests only, for layer caching ---
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages ./packages
RUN pnpm install --frozen-lockfile --filter web...

# --- build ---
FROM base AS builder
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_FACE_FPS=15
# must equal EMERGENCY_NUMBER in root .env (compose passes both from the same file)
ARG NEXT_PUBLIC_EMERGENCY_NUMBER=103
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_FACE_FPS=$NEXT_PUBLIC_FACE_FPS \
    NEXT_PUBLIC_EMERGENCY_NUMBER=$NEXT_PUBLIC_EMERGENCY_NUMBER
COPY --from=deps /repo ./
COPY apps/web ./apps/web
RUN pnpm --filter web build

# --- runtime (standalone output, monorepo path: apps/web/server.js) ---
FROM node:24-alpine AS runner
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
WORKDIR /app
RUN addgroup -S nextjs && adduser -S nextjs -G nextjs
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nextjs /repo/apps/web/public ./apps/web/public
USER nextjs
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
