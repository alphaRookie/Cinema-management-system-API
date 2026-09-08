FROM python:3.13-slim

# Set environment variables to keep Python "clean"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the folder where the code will live in the container
WORKDIR /app


# Install Pipenv (in-exchange of requirements.txt)
RUN pip install --no-cache-dir pipenv

# Copy my Pipfile and Pipfile.lock first 
COPY Pipfile Pipfile.lock ./

# Install dependencies globally inside the container
# --system: Installs packages directly into the container (no "venv" needed)
# --deploy: Forces the build to fail if Pipfile.lock doesn't match my version
RUN pipenv install --system --deploy

# Copy the rest of my project code
COPY . .

# Start the Django server (Production)
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --workers 3 --bind 0.0.0.0:8000 cinema.wsgi:application"]
