#!/bin/bash
set -e

# ==== Настройки ====
IMAGE_NAME="test:postgres1"
CONTAINER_NAME="my_proj1"
POSTGRES_USER="myuser"
POSTGRES_PASSWORD="mypassword"
POSTGRES_DB="mydatabase"
APP_PATH="/app/scripts"  # путь к скриптам внутри контейнера

# ==== 1. Сборка образа ====
echo "Сборка Docker-образа..."
sudo docker build -t $IMAGE_NAME .

# ==== 2. Запуск контейнера ====
echo "Запуск контейнера $CONTAINER_NAME..."
sudo docker run -d \
    --name $CONTAINER_NAME \
    -e POSTGRES_USER=$POSTGRES_USER \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e POSTGRES_DB=$POSTGRES_DB \
    -p 5432:5432 \
    $IMAGE_NAME

# ==== 3. Ждём готовности PostgreSQL ====
echo "3. Ждём PostgreSQL..."
until sudo docker exec $CONTAINER_NAME pg_isready -U $POSTGRES_USER > /dev/null 2>&1; do
    echo "Ждём базу..."
    sleep 2
done
echo "PostgreSQL готов"

# ==== 4. Запуск скриптов Python внутри контейнера ====
echo "4. Запуск extract.py и transform.py..."
sudo docker exec -it $CONTAINER_NAME bash -c "python $APP_PATH/extract.py && python $APP_PATH/transform.py"

# ==== 5. Подключение к PostgreSQL через psql ====
echo "5. Подключение к PostgreSQL"
sudo docker exec -it $CONTAINER_NAME psql -U $POSTGRES_USER -d $POSTGRES_DB

