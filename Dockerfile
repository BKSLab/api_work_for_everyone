FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# The WORKDIR is changed to the application's root directory.
WORKDIR /app

# Install tzdata and set timezone to Moscow
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

# Optimize layer caching for dependencies
# Paths are adjusted relative to the new WORKDIR's parent.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# The source code is copied into the parent directory of WORKDIR.
COPY . .

# The command will be executed from /app/app, so paths must be relative.
EXPOSE 8000
