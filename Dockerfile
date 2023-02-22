ARG python=python:3.9.16-slim-buster
FROM ${python}

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python"]
CMD ["main.py"]
