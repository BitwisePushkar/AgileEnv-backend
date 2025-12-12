FROM python:3.11

ADD requirements.txt .

RUN pip install --trusted-host pypi.python.org -r requirements.txt 

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
