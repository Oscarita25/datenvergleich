ARG python=python:3.9.16-slim-buster
FROM ${python} AS build

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM ${python} AS build

COPY --from=build /venv /venv
ENV PATH=/venv/bin$PATH

COPY . .

ENTRYPOINT ["python"]
CMD ["main.py"]
