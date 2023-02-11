# Inspired by: https://nodejs.org/en/docs/guides/nodejs-docker-webapp/
FROM node:16

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 8080
CMD [ "node", "app.js" ]
