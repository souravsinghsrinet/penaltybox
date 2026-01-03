FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory
RUN mkdir -p uploads/proofs

# Make start script executable
RUN chmod +x start.sh

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

CMD ["./start.sh"]
