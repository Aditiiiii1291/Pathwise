# =============================================================================
# PATHWISE FRONTEND — MULTI-STAGE PRODUCTION DOCKERFILE
# =============================================================================

# --- Stage 1: Build production bundle ---
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using clean install
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build argument for backend API URL (baked into Vite production bundle)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# --- Stage 2: Serve static bundle via Nginx ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
