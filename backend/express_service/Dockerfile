# Dockerfile (express-service)
FROM node:20-alpine

# Set the standard working directory
WORKDIR /usr/src/app

# --- 1. System Dependencies for PostgreSQL (pg driver) ---
RUN apk update && apk add --no-cache \
    python3 \
    g++ \
    make \
    libc6-compat

# --- 2. Copy Dependencies & Install ---
# Copy package files (for caching)
COPY package*.json ./
# RUN npm install --omit=dev
RUN npm install

# --- 3. Copy Application Files ---
# Copy all source code (including controllers, services, app.js, server.js)
COPY ./src ./src

# Copy all configuration files required for starting and migrations
# Note: We include knexfile.js, .env, and the package files already copied.
COPY .env ./
COPY knexfile.js ./
# We don't need to copy migrations separately as they are inside /src/ (based on your structure)
# If your knexfile.js points to /src/migrations, the copy ./src/ will handle it.

# --- 4. Define Execution Environment ---
ENV NODE_ENV=production
ENV PORT=3001 
EXPOSE 3001

# --- 5. Start Command ---
# CRITICAL: Use the file that acts as your entry point. 
# Since you have both app.js and server.js, assume server.js starts the listener.
CMD ["npm", "start"]