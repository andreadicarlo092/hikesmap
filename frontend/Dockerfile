# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- runtime stage ---
FROM node:20-alpine AS runtime

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json

ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["node", "build"]
