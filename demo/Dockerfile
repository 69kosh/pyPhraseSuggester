FROM python:slim

# for github library
RUN apt update
RUN apt-get install -y git 




# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./api.py .
COPY ./*.csv .

# for github library
RUN git clone https://github.com/69kosh/pyPhraseSuggesting /mySrc/pyPhraseSuggesting
ENV PYTHONPATH "${PYTHONPATH}:/mySrc/pyPhraseSuggesting/src"