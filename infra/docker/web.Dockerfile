FROM node:22-alpine

WORKDIR /app

RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN corepack pnpm install --frozen-lockfile=false

COPY apps/web apps/web
COPY packages packages

WORKDIR /app/apps/web
RUN corepack pnpm build

CMD ["corepack", "pnpm", "start"]
