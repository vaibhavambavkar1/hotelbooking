# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the docker
WORKDIR /app

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the docker
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the docker
COPY . /app/

# Expose the port on which the Django app will run
EXPOSE 8000

# Command to run migrations and then start the server
# Note: You might want to use a separate script or just run gunicorn in production
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
