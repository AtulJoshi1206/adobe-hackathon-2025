# Use a slim Python base image for a smaller footprint
FROM python:3.9-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application code
COPY src/main.py .

# The command that will be executed when the container starts
# It runs the Python script to process PDFs.
CMD ["python", "main.py"]