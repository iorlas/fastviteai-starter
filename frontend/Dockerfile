# ============================================
# Frontend Dockerfile (Multi-Stage Build)
# ============================================
# Stage 1: Development - Vite dev server with HMR
# Stage 2: Builder - Build production assets
# Stage 3: Production - Nginx serving static files
# ============================================

# ============================================
# Stage 1: Development
# ============================================
FROM node:20-slim AS development

# Set working directory
WORKDIR /app

# Enable corepack for pnpm
RUN corepack enable pnpm

# Copy package files first (layer caching optimization)
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with host 0.0.0.0 to allow external access
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

# ============================================
# Stage 2: Builder (for production)
# ============================================
FROM node:20-slim AS builder

WORKDIR /app

# Enable corepack for pnpm
RUN corepack enable pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build production assets
RUN pnpm build

# ============================================
# Stage 3: Production (nginx)
# ============================================
FROM nginx:alpine AS production

# Copy custom nginx configuration (optional - create if needed)
# COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
