# File: backend/Dockerfile (v2 - Corrected Paths)

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- PENTING: Salin file model yang sudah diunduh ---
COPY ./embedding_model_files /app/embedding_model_files

# The trailing slash on 'app/' is important. It copies the *content*
# of the 'app' directory into the working directory ('/app').
COPY . .

# Copy the main entry point
#COPY main.py .

# Expose the port the app runs on
EXPOSE 8080

# --- REAL CMD (Restored) ---
# Now that we've fixed the file structure, we can use the real command.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]