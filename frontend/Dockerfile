# Node.js
FROM node:18-alpine

# Çalışma dizini
WORKDIR /app

# Bağımlılık dosyaları
COPY package*.json ./

# Bağımlılıkları yükle
RUN npm install

# Uygulama kodları
COPY . .

# Build
RUN npm run build

# Port
EXPOSE 3000

# Başlatma komutu
CMD ["npm", "start"]
