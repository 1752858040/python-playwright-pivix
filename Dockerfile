FROM python:3.9.7

RUN mkdir /app
WORKDIR /app
 
ADD . .

RUN pip install playwright openpyxl

RUN playwright install

CMD ["python", "./main.py", "5"]