FROM python:3.7-alpine
WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt --no-cache

ENTRYPOINT ["/usr/local/bin/python", "/usr/src/app/app.py"] 
