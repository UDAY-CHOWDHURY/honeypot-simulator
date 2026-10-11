FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY honeypot/simulation /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create required directories
RUN mkdir -p /app/data/fake_files /app/honeypot/backend/logs

# Expose port used by Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
