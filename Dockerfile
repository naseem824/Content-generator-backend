# Use an official, lightweight Python 3.11.9 image
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# The PORT environment variable will be provided by the hosting platform (e.g., Railway/Render)
# The EXPOSE instruction is good practice but not strictly required by Railway/Render
# EXPOSE $PORT

# The command to run your application, now correctly binding to the PORT variable
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "4", "--timeout", "180", "app:app"]
