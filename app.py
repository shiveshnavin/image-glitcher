import os
import tempfile
import subprocess
import shlex
from pathlib import Path
from typing import Optional

import gradio as gr
import requests
from PIL import Image

# --- Config ---
GLITCH_SCRIPT = Path("scripts/glitch.py").resolve()
assert GLITCH_SCRIPT.exists(), f"glitch.py not found at {GLITCH_SCRIPT}"

# Verify ffmpeg/ffprobe presence (v7+ preferred)
def _check_binaries():
    def ver(cmd):
        try:
            out = subprocess.check_output([cmd, "-version"], text=True)
            return out.splitlines()[0]
        except Exception:
            return "NOT FOUND"
    return ver("ffmpeg"), ver("ffprobe")

print("FFmpeg:", _check_binaries()[0])
print("FFprobe:", _check_binaries()[1])

# --- Helpers ---
def _download_image(url: str, dst_dir: Path) -> Path:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    # Attempt to infer extension
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


def _ensure_image(path: Path) -> Path:
    # Simple open-validate cycle (also normalizes/transcodes weird formats)
    with Image.open(path) as im:
        im.verify()  # quick integrity check
    return path


def run_glitch(
    image_url: Optional[str],
    image_file: Optional[Path],
    duration: float,
    fps: Optional[int],
    glitch2_secs: Optional[float],
    wobble_main: Optional[float],
    wobble_jitter: Optional[float],
    wobble_f1: Optional[float],
    wobble_f2: Optional[float],
    sigma: Optional[float],
):
    if not duration or duration <= 0:
        raise gr.Error("Duration must be > 0 seconds")

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        # Source image handling
        src_path: Optional[Path] = None
        if image_file is not None:
            src_path = Path(image_file)
        elif image_url and image_url.strip():
            src_path = _download_image(image_url.strip(), tdir)
        else:
            raise gr.Error("Provide either an image URL or upload a file")

        _ensure_image(src_path)

        # Output path
        out_path = tdir / "glitched.mp4"

        # Build CLI
        cmd = [
            "python", str(GLITCH_SCRIPT),
            str(src_path),
            str(duration),
            "--out", str(out_path),
        ]
        if fps is not None:
            cmd += ["--fps", str(fps)]
        if glitch2_secs is not None:
            cmd += ["--glitch2_secs", str(glitch2_secs)]
        if wobble_main is not None:
            cmd += ["--wobble_main", str(wobble_main)]
        if wobble_jitter is not None:
            cmd += ["--wobble_jitter", str(wobble_jitter)]
        if wobble_f1 is not None:
            cmd += ["--wobble_f1", str(wobble_f1)]
        if wobble_f2 is not None:
            cmd += ["--wobble_f2", str(wobble_f2)]
        if sigma is not None:
            cmd += ["--sigma", str(sigma)]

        # Run
        print("Running:", shlex.join(cmd))
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise gr.Error(f"glitch.py failed: {e}")

        if not out_path.exists():
            raise gr.Error("Output file not produced by glitch.py")

        # Return file path; Gradio will host and provide a URL.
        return str(out_path)


# --- Gradio UI ---
def build_ui():
    with gr.Blocks(title="Glitch Video Generator", analytics_enabled=False) as demo:
        gr.Markdown(
            """
            # 🔧 Glitch Video Generator
            Convert an image into a glitched video. Provide a URL **or** upload an image, set the duration, and tweak optional parameters.
            """
        )

        with gr.Row():
            image_url = gr.Textbox(label="Image URL", placeholder="https://example.com/pic.jpg")
            image_file = gr.Image(label="Upload Image", type="filepath")

        duration = gr.Number(label="Duration (seconds)", value=5, precision=2)
        with gr.Accordion("Optional Parameters", open=False):
            fps = gr.Slider(1, 120, value=30, step=1, label="fps (frames per second)")
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

        run_btn.click(
            fn=_wrap,
            inputs=[
                image_url,
                image_file,
                duration,
                fps,
                glitch2_secs,
                wobble_main,
                wobble_jitter,
                wobble_f1,
                wobble_f2,
                sigma,
            ],
            outputs=[output_file, url_box],
        )

        gr.Markdown(
            """
            ### API Usage
            This Space exposes a **predict API** at `/run/predict`.

            **JSON (image URL)**
            ```bash
            curl -X POST \
              -H "Content-Type: application/json" \
              -d '{
                "data": [
                  "https://picsum.photos/seed/abc/800/600",  # image_url
                  null,                                       # image_file (null when using URL)
                  5,                                          # duration
                  30, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0           # optional params
                ]
              }' \
              https://<your-username>-glitch-video.hf.space/run/predict
            ```

            **Multipart (file upload)**
            ```bash
            curl -X POST \
              -F "data=@-;type=application/json" \
              -F "files[]=@/path/to/local_image.jpg" \
              https://<your-username>-glitch-video.hf.space/run/predict <<'JSON'
            {"data": [null, "file", 5, 30, 0, 0, 0, 0, 0, 0]}
            JSON
            ```
            """
        )

    return demo


demo = build_ui()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
