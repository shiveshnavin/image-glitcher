---
title: Glitch Image
emoji: 🔥
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
---


# 🔧 Glitch Video Generator

This Space wraps `scripts/glitch.py` and converts an image into a glitched video using **FFmpeg/ffprobe v8** (via Docker).  
You can use it from the **web UI** or programmatically via the **API**.

## � Docker-based Deployment (Hugging Face Spaces)

This Space is configured to use a custom Docker image for deployment. The Dockerfile installs all dependencies, including FFmpeg, Python, and required Python packages, and overrides the default ffmpeg entrypoint so the Gradio app runs as expected.

**You do not need to install anything manually on Hugging Face Spaces.**

If you want to run locally:

```bash
docker build -t image-glitcher .
docker run -p 7860:7860 image-glitcher
```

The app will be available at http://localhost:7860

## �🚀 Usage (UI)
1. Open the Space.
2. Paste an **image URL** or upload an image.
3. Set the **duration (seconds)** and optional parameters.
4. Click **Generate** → Download the video or copy the hosted URL.

## 🔌 API Access
The Space exposes `/run/predict` for programmatic access.  
The input order matches the UI fields:

```
[ image_url:str | null,
image_file:path | "file" | null,
duration:number,
fps:number,
base:number,
glitch2_secs:number,
wobble_main:number,
wobble_jitter:number,
wobble_f1:number,
wobble_f2:number,
sigma:number ]
```


### Example (JSON + URL)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      "https://picsum.photos/seed/abc/800/600",
      null,
      5,
      30, 20, 0, 0, 0, 0, 0, 0
    ]
  }' \
  https://<your-username>-glitch-video.hf.space/run/predict
```

```
curl -X POST \
  -F "data=@-;type=application/json" \
  -F "files[]=@/path/to/local_image.jpg" \
  https://<your-username>-glitch-video.hf.space/run/predict <<'JSON'
{"data": [null, "file", 5, 30, 20, 0, 0, 0, 0, 0, 0]}
JSON
```



🛠️ Requirements (for local non-Docker use)

- FFmpeg/ffprobe v8 (or higher)
- Python 3.10+
- gradio, pillow, glitch-this, requests

For Hugging Face Spaces, all requirements are handled by the Dockerfile.



