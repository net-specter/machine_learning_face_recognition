# =========================
# BUILD STAGE
# =========================
FROM node:20 AS builder

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# Copy dependency files
COPY package.json package-lock.json ./

# ✅ Install ALL deps (including devDependencies)
RUN npm install

# Copy source code
COPY . .

# Build Next.js
RUN npm run build


# =========================
# RUN STAGE
# =========================
FROM node:20 AS runner

WORKDIR /app
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Copy only what is needed to run
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]
