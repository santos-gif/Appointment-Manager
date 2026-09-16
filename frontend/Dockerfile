FROM node:24-alpine
WORKDIR /app

COPY frontend/package*.json ./
RUN npm install -g @angular/cli
RUN npm install


COPY . .

CMD [ "ng", "serve", "--host", "0.0.0.0", "--poll", "2000" ]
