# Arbitrage Engine Dockerfile
FROM node:20-alpine as builder

# Install Rust and build dependencies
RUN apk add --no-cache curl build-base

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install Node dependencies
RUN yarn install

# Copy source files
COPY index.ts ./
COPY native ./native

# Build Rust and TypeScript
RUN yarn build:all

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/native/math_engine.node ./native/math_engine.node
COPY --from=builder /app/package.json ./

# Install only production dependencies
RUN yarn install --production

CMD ["node", "dist/index.js"]
