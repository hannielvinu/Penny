FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE requirements-dev.lock ./
COPY src ./src
RUN pip install --no-cache-dir -c requirements-dev.lock . && useradd --create-home penny
USER penny
EXPOSE 8099
CMD ["uvicorn", "penny.chaos.proxy:app", "--host", "0.0.0.0", "--port", "8099", "--no-access-log"]
