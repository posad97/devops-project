# Build on Python image
FROM python:3.8-alpine

# Create the working directory for the application
WORKDIR /app

# Install necessary modules with pip
RUN pip install Flask flask-session mysql-connector-python requests gunicorn

# Copy the application code and files to the working directory
COPY . .

# Information about the port exposed
EXPOSE 5000

# Starting the application using gunicorn server
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
