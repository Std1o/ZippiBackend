FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/

RUN pip install -r requirements.txt

COPY ./zippi /code/zippi

# Добавляем src в PYTHONPATH
ENV PYTHONPATH=/code/zippi

# Запускаем как модуль
CMD ["python", "-m", "zippi"]
