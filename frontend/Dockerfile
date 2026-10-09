FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Zusatzkarten des Aktien-Dashboards (E16); false blendet sie aus.
ARG VITE_SHOW_FINANCE_EXTRAS=true
ENV VITE_SHOW_FINANCE_EXTRAS=$VITE_SHOW_FINANCE_EXTRAS

# Prognose im Zeitverlauf (D2, E28); false blendet sie aus (Evaluationsinstanz).
ARG VITE_SHOW_FORECAST=true
ENV VITE_SHOW_FORECAST=$VITE_SHOW_FORECAST

RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
