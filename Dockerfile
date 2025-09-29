FROM postgres:16

# Устанавливаем Python, venv, pip, cron, supervisor и библиотеки для psycopg2
RUN apt-get update && \
    apt-get install -y python3 python3-venv python3-pip cron supervisor libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаём виртуальное окружение
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем скрипты
COPY scripts/ ./scripts/
RUN chmod +x scripts/extract.py

# Копируем requirements.txt и ставим зависимости в venv
COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Настраиваем cron (каждую минуту) с явным вызовом Python из venv
RUN echo "* * * * * root /opt/venv/bin/python /app/scripts/extract.py >> /var/log/cron.log 2>&1" > /etc/cron.d/mycron && \
    echo "* * * * * root /opt/venv/bin/python /app/scripts/transform.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/mycron && \
    chmod 0644 /etc/cron.d/mycron && \
    touch /var/log/cron.log

# Копируем supervisord.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Переменные окружения PostgreSQL
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=mydatabase
ENV POSTGRES_HOST=127.0.0.1
ENV POSTGRES_PORT=5432

EXPOSE 5432

# Запуск supervisor с указанием абсолютного пути к конфигу
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]

