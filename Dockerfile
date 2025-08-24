# Use an official, lightweight Python 3.11.9 image
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Upgrade pip and install dependencies with VERBOSE logging
# This will give us maximum detail on the error.
RUN pip install --upgrade pip && \
    pip install \
    --verbose \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy the rest of your application code
COPY . .

# Tell the container to listen on port 10000
EXPOSE 10000

# The command to run your application
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
