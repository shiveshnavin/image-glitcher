# Glitch Video Generator — Hugging Face Space

This Space wraps your existing `scripts/glitch.py` CLI so users can upload an image **or** pass an image URL, choose a duration and optional parameters, and receive a downloadable video URL (served by Gradio). Built for **FFmpeg/ffprobe v7**.

---

## ✅ Features

* Accept **image URL** or **direct image upload** (PNG/JPG/GIF).
* Required: `duration` (seconds). Optional: all your CLI params `--fps, --base, --glitch2_secs, --wobble_main, --wobble_jitter, --wobble_f1, --wobble_f2, --sigma`.
* Outputs a hosted **file URL** to the generated video.
* Accessible via **web UI** and **programmatic API**.

---

## 📂 Repository Layout

```
.
├─ app.py                 # Gradio UI + API wrapper around scripts/glitch.py
├─ scripts/
│  └─ glitch.py           # Your existing script (copied as-is)
├─ requirements.txt       # Python deps (Gradio, Pillow, glitch-this, requests)
├─ Dockerfile             # Ensures FFmpeg/ffprobe v7 is present
└─ README.md              # (optional) reuse this document
```

> **Note:** Replace `scripts/glitch.py` contents with your real script; this Space just calls it.

---

## 🐳 Dockerfile (FFmpeg/ffprobe v7)

```dockerfile
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
```

---

## 📦 requirements.txt

```txt
gradio>=4.44.0
pillow>=9.5.0
glitch-this>=1.0.3
requests>=2.31.0
```

---

## 🐍 app.py (Gradio UI + API)

````python
import os
import tempfile
import subprocess
import shlex
from pathlib import Path
from typing import Optional

import gradio as gr
import requests
from PIL import Image

GLITCH_SCRIPT = Path("scripts/glitch.py").resolve()
assert GLITCH_SCRIPT.exists(), f"glitch.py not found at {GLITCH_SCRIPT}"

def _download_image(url: str, dst_dir: Path) -> Path:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "").lower()
    ext = ".jpg"
    if "png" in ctype:
        ext = ".png"
    elif "jpeg" in ctype:
        ext = ".jpg"
    elif "gif" in ctype:
        ext = ".gif"
    img_path = dst_dir / f"input{ext}"
    with open(img_path, "wb") as f:
        f.write(r.content)
    return img_path


def run_glitch(image_url: Optional[str], image_file: Optional[Path], duration: float, fps: Optional[int], base: Optional[int], glitch2_secs: Optional[float], wobble_main: Optional[float], wobble_jitter: Optional[float], wobble_f1: Optional[float], wobble_f2: Optional[float], sigma: Optional[float]):
    if not duration or duration <= 0:
        raise gr.Error("Duration must be > 0 seconds")

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        src_path: Optional[Path] = None
        if image_file is not None:
            src_path = Path(image_file)
        elif image_url and image_url.strip():
            src_path = _download_image(image_url.strip(), tdir)
        else:
            raise gr.Error("Provide either an image URL or upload a file")

        out_path = tdir / "glitched.mp4"

        cmd = ["python", str(GLITCH_SCRIPT), str(src_path), str(duration), "--out", str(out_path)]
        if fps is not None: cmd += ["--fps", str(fps)]
        if base is not None: cmd += ["--base", str(base)]
        if glitch2_secs is not None: cmd += ["--glitch2_secs", str(glitch2_secs)]
        if wobble_main is not None: cmd += ["--wobble_main", str(wobble_main)]
        if wobble_jitter is not None: cmd += ["--wobble_jitter", str(wobble_jitter)]
        if wobble_f1 is not None: cmd += ["--wobble_f1", str(wobble_f1)]
        if wobble_f2 is not None: cmd += ["--wobble_f2", str(wobble_f2)]
        if sigma is not None: cmd += ["--sigma", str(sigma)]

        subprocess.run(cmd, check=True)
        if not out_path.exists():
            raise gr.Error("Output file not produced")
        return str(out_path)


def build_ui():
    with gr.Blocks(title="Glitch Video Generator") as demo:
        with gr.Row():
            image_url = gr.Textbox(label="Image URL")
            image_file = gr.Image(label="Upload Image", type="filepath")
        duration = gr.Number(label="Duration (seconds)", value=5, precision=2)
        with gr.Accordion("Optional Parameters", open=False):
            fps = gr.Slider(1, 120, value=30, step=1, label="fps")
            base = gr.Slider(1, 100, value=20, step=1, label="base")
            glitch2_secs = gr.Number(value=0.0, precision=2, label="glitch2_secs")
            wobble_main = gr.Number(value=0.0, precision=2, label="wobble_main")
            wobble_jitter = gr.Number(value=0.0, precision=2, label="wobble_jitter")
            wobble_f1 = gr.Number(value=0.0, precision=2, label="wobble_f1")
            wobble_f2 = gr.Number(value=0.0, precision=2, label="wobble_f2")
            sigma = gr.Number(value=0.0, precision=2, label="sigma")

        run_btn = gr.Button("Generate")
        output_file = gr.File(label="Output video")
        url_box = gr.Textbox(label="Output URL", interactive=False)

        def _wrap(*args):
            path = run_glitch(*args)
            return path, path

        run_btn.click(fn=_wrap, inputs=[image_url, image_file, duration, fps, base, glitch2_secs, wobble_main, wobble_jitter, wobble_f1, wobble_f2, sigma], outputs=[output_file, url_box])

        gr.Markdown("""
        ## API Usage
        Programmatic access:
        ```bash
        curl -X POST -H "Content-Type: application/json" \\
          -d '{"data": ["https://picsum.photos/seed/abc/800/600", null, 5, 30, 20, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}' \\
          https://<your-space>.hf.space/run/predict
        ```
        The response includes the hosted file URL.
        """)

    return demo

demo = build_ui()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
````

---

## 📝 README.md

````md
# Glitch Video Generator (Hugging Face Space)

Accessible both via **UI** and **API**. Wraps `scripts/glitch.py` to convert an image (URL or upload) into a glitched video.

### Local run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
````

### Deploy to Spaces

Choose **Docker** SDK, push repo. The app provides UI and API endpoints automatically.

```


---

## 🔌 API Access (UI + Programmatic)

This Space is accessible via the Gradio UI **and** a JSON/multipart API. The model function is exposed at `/run/predict` and the payload order matches the UI inputs:

```

\[ image\_url\:str | null,
image\_file\:path | "file" | null,
duration\:number,
fps\:number,
base\:number,
glitch2\_secs\:number,
wobble\_main\:number,
wobble\_jitter\:number,
wobble\_f1\:number,
wobble\_f2\:number,
sigma\:number ]

````

### JSON request (using image URL)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      "https://picsum.photos/seed/abc/800/600",  # image_url
      null,                                       # image_file (null when using URL)
      5,                                          # duration
      30, 20, 0, 0, 0, 0, 0, 0                    # fps, base, glitch2_secs, wobble_main, wobble_jitter, wobble_f1, wobble_f2, sigma
    ]
  }' \
  https://<your-username>-glitch-video.hf.space/run/predict
````

Response:

```json
{"data": ["https://<space-hosted-file-url>/file=glitched.mp4"]}
```

### Multipart request (file upload)

```bash
curl -X POST \
  -F "data=@-;type=application/json" \
  -F "files[]=@/path/to/local_image.jpg" \
  https://<your-username>-glitch-video.hf.space/run/predict <<'JSON'
{"data": [null, "file", 5, 30, 20, 0, 0, 0, 0, 0, 0]}
JSON
```

Notes:

* Set **second** element to the literal string `"file"` when uploading via `files[]`.
* The endpoint returns a hosted URL (same one shown in the UI) which you can store or forward.
* CORS is allowed by default on Spaces; if needed you can proxy requests via your backend.

If you want a custom path like `/api/glitch`, we can swap Gradio for a **FastAPI** app serving the same UI and an OpenAPI schema—say the word and I’ll provide that variant.
