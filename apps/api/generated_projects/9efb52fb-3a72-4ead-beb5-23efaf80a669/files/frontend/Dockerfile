FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy application code
COPY . .

# Build the Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]