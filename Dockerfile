FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

RUN useradd --uid 1000 --no-create-home app
USER 1000

CMD ["python", "src/process.py"]
