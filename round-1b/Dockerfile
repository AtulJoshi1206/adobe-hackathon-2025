# Use a slim Python base image
FROM python:3.9-slim-bullseye

WORKDIR /app

# Install the new, lightweight dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the pre-downloaded GloVe model
COPY ./model /app/model

# Copy your source code
COPY ./src /app/src

# Command to run the application
CMD ["python", "src/main.py"]