# syntax=docker/dockerfile:1.7
FROM node:20-bookworm-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev

FROM node:20-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8004
RUN apt-get update \
  && apt-get install -y --no-install-recommends wget \
  && rm -rf /var/lib/apt/lists/*
RUN addgroup --system --gid 1001 nodeapp && adduser --system --uid 1001 --ingroup nodeapp nodeapp
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src
USER nodeapp
EXPOSE 8004
CMD ["node", "src/index.js"]
