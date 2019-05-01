FROM ubuntu:16.04

ARG CUR_PATH

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

RUN pip install flask 

COPY flaskapp/ /app

ENTRYPOINT [ "python" ]

CMD [ "app/flaskapp.py" ]
