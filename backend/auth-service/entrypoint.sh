#!/bin/sh

# Determine which database we need to wait for based on the service name
# Use environment variables passed via docker-compose
DB_HOST=$DB_HOST
DB_PORT="3306"

echo "Waiting for $DB_HOST:$DB_PORT to be ready..."
until nc -z $DB_HOST $DB_PORT; do
  echo "Database connection failed. Retrying in 2 seconds..."
  sleep 2
done
echo "Database is ready. Starting application."

# Execute the main application command
exec npm start