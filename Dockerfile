FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if required for cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage/encrypted storage/temporary
# Make sure the app user owns the directories if not running as root

EXPOSE 5000

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

CMD ["python", "run.py"]
