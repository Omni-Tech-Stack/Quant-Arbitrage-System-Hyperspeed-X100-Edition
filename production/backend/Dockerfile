# Backend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy backend files
COPY . .

# Expose port
EXPOSE 3001

# Environment variables
ENV DEMO_MODE=true
ENV PORT=3001

# Start the server
CMD ["npm", "start"]
