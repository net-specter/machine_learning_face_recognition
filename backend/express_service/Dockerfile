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
COPY ./src/seeders ./seeders
COPY ./src/models ./models

ENV NODE_ENV=production

EXPOSE 5000

CMD ["node", "./src/app.js"]
