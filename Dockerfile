FROM python:3.12-slim

WORKDIR /app

# Install the package and its dependencies
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -e . && \
    rm -rf /root/.cache/pip

# Default entrypoint — runs the GitHub Action adapter
ENTRYPOINT ["python", "-m", "decisiondrift.github.action_entrypoint"]
