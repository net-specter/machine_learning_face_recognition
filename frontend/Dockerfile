# Stage 1: Base setup
FROM node:20-alpine AS base
WORKDIR /frontend
COPY package.json package-lock.json ./
RUN npm install --frozen-lockfile

# Stage 2: Builder stage
FROM base AS builder
WORKDIR /frontend
COPY . .
RUN npm run build

# Stage 3: Runner stage (Production environment)
FROM base AS runner
WORKDIR /frontend
ENV NODE_ENV production

# Copy artifacts from the builder stage
COPY --from=builder /frontend/.next ./.next
COPY --from=builder /frontend/public ./public
COPY --from=builder /frontend/package.json ./package.json

# Next.js standalone output mode (recommended)
# For this to work, ensure 'output: "standalone"' is set in your next.config.js file
COPY --from=builder /frontend/standalone ./

EXPOSE 3000

# Start the frontendlication
CMD ["npm", "start"]
