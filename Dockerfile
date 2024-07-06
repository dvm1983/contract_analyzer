FROM python:3.10

RUN mkdir /project
COPY ./* /project/
WORKDIR /project

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements

EXPOSE 5000

ENTRYPOINT ["python3", "main.py"]