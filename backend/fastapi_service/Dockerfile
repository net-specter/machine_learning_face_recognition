# Use a Python base image suitable for scientific libraries
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# --- 1. System Dependencies for OpenCV/MediaPipe ---
# Install system packages needed for compiling some Python libs and for CV stability
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*


# --- 2. Copy and Install Python Dependencies ---
# Copy requirements file first for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 3. Copy Application Code ---
COPY . .

# --- 4. Define Execution Environment ---
# Set the port FastAPI will run on (e.g., 5000, as configured in your Express .env)
ENV PORT=5000
ENV ML_SERVICE_HOST=0.0.0.0

# Expose the application port
EXPOSE 5000

# --- 5. Start Command ---
# Use Uvicorn to start the FastAPI application
# Replace 'main:app' with the path to your main FastAPI application instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]