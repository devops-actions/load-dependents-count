FROM python:3.14-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1

# Fix Playwright browser path so it doesn't depend on $HOME (GitHub Actions sets HOME=/github/home)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright/Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libxshmfence1 libx11-xcb1 libxcb1 && \
    rm -rf /var/lib/apt/lists/*

# Set a fixed path for Playwright browsers so they are found regardless of $HOME at runtime
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install Python dependencies
COPY requirements.txt /action/requirements.txt
RUN pip install --no-cache-dir -r /action/requirements.txt

# Install Chromium browser
RUN playwright install chromium --with-deps

# Copy action source
COPY src/ /action/src/

ENTRYPOINT ["python3", "/action/src/fetch_dependents.py"]
