FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache coreutils

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/uploads

EXPOSE 5000

CMD ["python", "app.py"]
