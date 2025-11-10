FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib (with ARM64/aarch64 support)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    # Update config.guess and config.sub for ARM64 support
    wget -O config.guess 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' && \
    wget -O config.sub 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel hatchling

# Copy build files (needed for pip install)
COPY pyproject.toml .
COPY README.md .

# Copy source code (needed for hatchling build)
COPY src/ ./src/

# Install Python dependencies (standard install, not editable)
RUN pip install --no-cache-dir .

# Copy configuration files
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "roma_trading.main"]

