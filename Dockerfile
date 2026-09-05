FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app

COPY pyproject.toml README.md ./

RUN pip install --no-cache-dir .

COPY src ./src
COPY docs ./docs

RUN mkdir -p data reports

CMD ["python", "src/main.py"]