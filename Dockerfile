FROM python:3.10-slim


ENV DEBIAN_FRONTEND=noninteractive \
PIP_NO_CACHE_DIR=1 \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y --no-install-recommends \
wget xz-utils ca-certificates && \
rm -rf /var/lib/apt/lists/*


RUN wget -O /tmp/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
mkdir -p /opt/ffmpeg && \
tar -xJf /tmp/ffmpeg.tar.xz -C /opt/ffmpeg --strip-components=1 && \
ln -s /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg && \
ln -s /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe && \
ffmpeg -version && ffprobe -version


WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt


COPY scripts ./scripts
COPY app.py ./app.py


EXPOSE 7860
CMD ["python", "app.py"]
