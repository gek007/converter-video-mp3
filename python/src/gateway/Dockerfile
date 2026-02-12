FROM python:3.12-slim

WORKDIR /app

# Copy application files
COPY server.py .
COPY auth/ ./auth/
COPY storage/ ./storage/

# Copy and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the Flask app runs on
EXPOSE 8080

# Run the application
CMD ["python", "server.py"]
