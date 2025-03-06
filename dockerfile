# Use an official lightweight Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get update && apt-get install -y curl

# Expose port 8000 (default Django runserver port)
EXPOSE 8000

# Start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lifeline.wsgi:application"]
