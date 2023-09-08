# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.11

# Встановимо змінну середовища
ENV APP_HOME /app/simple_web

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Скопіюємо інші файли в робочу директорію контейнера
COPY simple_web .

# RUN pip install .

EXPOSE 3000

EXPOSE 5000

# Запустимо наш застосунок всередині контейнера
ENTRYPOINT ["python", "main.py"]