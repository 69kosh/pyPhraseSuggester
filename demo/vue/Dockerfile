FROM node:lts-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

ARG VUE_APP_API_HOST

COPY . .
RUN npm run build 


FROM nginx:stable-alpine-slim as production-build
COPY ./nginx.conf /etc/nginx/nginx.conf

## Remove default nginx index page
RUN rm -rf /usr/share/nginx/html/*

# Copy from the stahg 1
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8081
ENTRYPOINT ["nginx", "-g", "daemon off;"]