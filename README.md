---
title: Gentle Audio
emoji: 🔥
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
---

# 🔧 Glitch Video Generator

This Space wraps `scripts/glitch.py` and converts an image into a glitched video using **FFmpeg/ffprobe v7**.  
You can use it from the **web UI** or programmatically via the **API**.

## 🚀 Usage (UI)
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


🛠️ Requirements

FFmpeg/ffprobe v7 (installed via Dockerfile).
Python deps: gradio, pillow, glitch-this, requests.



