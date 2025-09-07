import os


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
