# Stage 1: Build Environment - Use a Python image with development tools
# We use Python 3.11 as recommended, and a slim version to keep the image smaller.
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for complex Python packages (like openblas/scipy, and QML libraries)
# We install crucial build dependencies first.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libblas3 \
    liblapack3 \
    gfortran \
    libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
# We install dependencies here to leverage Docker's layer caching.
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir speeds up build time
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Image - A clean, minimal image for running the application
# We use a smaller, production-ready base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code (backend/ content)
# Ensure this matches your directory structure (main.py, api/, core/, data/)
COPY . /app

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the Uvicorn server
# Using the standard host and port. We run without --reload for production stability.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]