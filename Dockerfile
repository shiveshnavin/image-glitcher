
FROM jrottenberg/ffmpeg:8-ubuntu-edge

# Install Python and dependencies
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		python3 python3-pip python3-venv python3-dev \
		build-essential wget ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Set python/pip aliases
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt ./

# Create virtual environment and install requirements
RUN python3 -m venv /opt/venv \
	&& /opt/venv/bin/pip install --upgrade pip \
	&& /opt/venv/bin/pip install -r requirements.txt

# Copy app code
COPY scripts ./scripts
COPY app.py ./app.py

EXPOSE 7860

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT []
CMD ["python", "app.py"]
