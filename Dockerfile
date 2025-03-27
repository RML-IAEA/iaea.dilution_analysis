FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose FastAPI's default port
EXPOSE 8000

# Ensure CMD points to the correct module
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
