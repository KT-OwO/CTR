# Use an old, potentially vulnerable base image
FROM python:3.8-slim-buster

WORKDIR /app

# Copy application files
COPY requirements.txt requirements.txt
COPY app.py app.py

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
# Running as root user by default, which is a security risk
CMD ["python", "app.py"]
