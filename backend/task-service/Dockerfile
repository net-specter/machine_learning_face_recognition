# Dockerfile (express-app)
FROM node:20-alpine

WORKDIR /

RUN apk update && apk add --no-cache mysql-client

COPY ./package*.json ./
RUN npm install --omit=dev

COPY ./src ./src
COPY ./scripts ./scripts
COPY ./src/config ./config
COPY ./src/migrations ./migrations
# COPY ./src/seeders ./seeders
COPY ./src/models ./models

# Add the entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"] 

ENV NODE_ENV=production

EXPOSE 8003

CMD ["node", "./src/app.js"]