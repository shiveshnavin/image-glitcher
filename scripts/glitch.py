#!/usr/bin/env python3
import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from PIL import Image
import shutil

# pip install glitch-this pillow
try:
    from glitch_this import ImageGlitcher
except Exception as e:
    print("Missing dependency: pip install glitch-this pillow", file=sys.stderr)
    raise

def log(msg: str):
    print(msg, flush=True)

def run_cmd(cmd):
    pretty = shlex.join(cmd) if isinstance(cmd, list) else cmd
    log(f"[CMD] {pretty}")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    for line in proc.stdout:
        print(line.rstrip())
    ret = proc.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd)
    return ret

def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def safe_delete(*paths: Path):
    for p in paths:
        try:
            if p and Path(p).exists():
                Path(p).unlink()
                log(f"[CLEAN] removed {p}")
        except Exception as e:
            log(f"[CLEAN][warn] could not remove {p}: {e}")

# ---------------- builders return True if they CREATED the output ----------------

def make_glitch_gif(img_path: Path, out_gif: Path, fps: int, n_frames: int,
                    mode: str = "constant", amt_start: float = 0.7, amt_end: float = 0.7) -> bool:
    """Make GIF. Return True if created (file didn't exist)."""
    if out_gif.exists():
        log(f"[SKIP] {out_gif} already exists (not overwriting)")
        return False
    ensure_parent(out_gif)
    log(f"[GLITCH] source={img_path} -> {out_gif} | fps={fps} frames={n_frames} mode={mode} amt={amt_start}->{amt_end}")
    img = Image.open(img_path).convert("RGBA")
    glitcher = ImageGlitcher()

    frames = []
    if n_frames < 2:
        n_frames = 2
    for i in range(n_frames):
        if mode == "ramp" and n_frames > 1:
            amt = amt_start + (amt_end - amt_start) * (i / (n_frames - 1))
        else:
            amt = amt_start
        try:
            frame = glitcher.glitch_image(img, amt, color_offset=True, scan_lines=False, seed=i)
        except TypeError:
            frame = glitcher.glitch_image(img, amt, color_offset=True, scan_lines=False)
        frames.append(frame.convert("P", palette=Image.ADAPTIVE))
        if n_frames <= 120 or i % max(1, n_frames // 60) == 0:
            log(f"[GLITCH] frame {i+1}/{n_frames} amt={amt:.3f}")

    delay_ms = max(1, round(1000 / fps))
    frames[0].save(
        out_gif,
        save_all=True,
        append_images=frames[1:],
        duration=delay_ms,
        loop=0,
        disposal=2,
        optimize=False,
        transparency=0,
    )
    log(f"[GLITCH] wrote {out_gif}")
    return True

def build_concat_raw(gif1: Path, gif2: Path, out_mp4: Path, fps: int, dur_total: float, dur_g2: float) -> bool:
    """Concat with looped GIF1; return True if created."""
    if out_mp4.exists():
        log(f"[SKIP] {out_mp4} already exists (not overwriting)")
        return False
    ensure_parent(out_mp4)
    F = int(fps)
    D1 = max(0.0, float(dur_total) - float(dur_g2))
    D2 = float(dur_g2)

    filter_complex = (
        f"[0:v]fps={F},setpts=N/({F}*TB),trim=duration={D1}[a];"
        f"[1:v]fps={F},setpts=N/({F}*TB),trim=duration={D2}[b];"
        f"[a][b]concat=n=2:v=1:a=0[v]"
    )

    cmd = [
        "ffmpeg", "-n",
        "-stream_loop", "-1", "-i", str(gif1),
        "-ignore_loop", "1", "-i", str(gif2),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-r", str(F),
        "-t", str(dur_total),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_mp4)
    ]
    run_cmd(cmd)
    return True

def apply_vfx(in_mp4: Path, out_mp4: Path, fps: int, dur_total: float) -> bool:
    """
    Softer VFX: gentler zoom, smaller XY wobble, smaller rotation sway.
    Keeps more of the picture visible.
    """
    if out_mp4.exists():
        log(f"[SKIP] {out_mp4} already exists (not overwriting)")
        return False

    ensure_parent(out_mp4)
    F = int(fps)
    L = float(dur_total)

    # toned-down params
    base_zoom   = 1.01
    zoom_amp    = 0.01
    x_wobble_1  = 10
    x_wobble_2  = 4
    y_wobble_1  = 8
    y_wobble_2  = 3
    rot_main    = 0.006
    rot_jitter  = 0.002

    pre_scale_h = 2400
    overscan_w  = 1152
    overscan_h  = 2048

    filter_complex = (
        f"[0:v]fps={F},setpts=N/({F}*TB),"
        f"scale=-1:{pre_scale_h},"
        f"zoompan="
          f"z='{base_zoom}+{zoom_amp}*sin(2*PI*(on/{F})/{L})':"
          f"x='(iw-iw/zoom)/2 + {x_wobble_1}*sin(2*PI*(on/{F})/{L}*3) + {x_wobble_2}*sin(2*PI*(on/{F})/{L}*7)':"
          f"y='(ih-ih/zoom)/2 + {y_wobble_1}*sin(2*PI*(on/{F})/{L}*2) +  {y_wobble_2}*sin(2*PI*(on/{F})/{L}*5)':"
          f"d=1:s={overscan_w}x{overscan_h}:fps={F},"
        f"rotate='{rot_main}*sin(2*PI*t/{L}) + {rot_jitter}*sin(2*PI*t/{L}*7)':"
          f"ow=rotw(iw):oh=roth(ih),"
        f"crop=1080:1920[v]"
    )

    cmd = [
        "ffmpeg", "-n",
        "-i", str(in_mp4),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-r", str(F),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_mp4)
    ]
    log("[CMD] " + shlex.join(cmd))
    run_cmd(cmd)
    return True

def apply_vfxHigh(in_mp4: Path, out_mp4: Path, fps: int, dur_total: float) -> bool:
    """Original stronger VFX; return True if created."""
    if out_mp4.exists():
        log(f"[SKIP] {out_mp4} already exists (not overwriting)")
        return False
    ensure_parent(out_mp4)
    F = int(fps)
    L = float(dur_total)

    filter_complex = (
        f"[0:v]fps={F},setpts=N/({F}*TB),"
        f"scale=-1:2880,"
        f"zoompan="
            f"z='1.10+0.08*sin(2*PI*(on/{F})/{L})':"
            f"x='(iw-iw/zoom)/2 + 24*sin(2*PI*(on/{F})/{L}*3) + 10*sin(2*PI*(on/{F})/{L}*7)':"
            f"y='(ih-ih/zoom)/2 + 18*sin(2*PI*(on/{F})/{L}*2) +  9*sin(2*PI*(on/{F})/{L}*5)':"
            f"d=1:s=1296x2304:fps={F},"
        f"rotate='0.012*sin(2*PI*t/{L}) + 0.004*sin(2*PI*t/{L}*7)':ow=rotw(iw):oh=roth(ih),"
        f"crop=1080:1920[v]"
    )

    cmd = [
        "ffmpeg", "-n",
        "-i", str(in_mp4),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-r", str(F),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_mp4)
    ]
    run_cmd(cmd)
    return True

def add_transitions(in_mp4: Path, out_mp4: Path, fps: int, dur_total: float,
                    wobble_main: float = 0.028, wobble_jitter: float = 0.012,
                    wobble_f1: float = 5.0, wobble_f2: float = 11.0,
                    blur_sigma: int = 42) -> bool:
    """
    Wobble/sway IN (0–0.5s) and OUT (last 0.5s). Heavy blur only during transitions.
    """
    if out_mp4.exists():
        log(f"[SKIP] {out_mp4} already exists (not overwriting)")
        return False
    ensure_parent(out_mp4)
    F = int(fps)
    L = float(dur_total)
    end_start = max(0.0, L - 0.5)

    angle_expr = (
        f"( if(lte(t,0.5),1,0) + if(gte(t,{end_start}),1,0) ) * "
        f"({wobble_main}*sin(2*PI*t*{wobble_f1}) + {wobble_jitter}*sin(2*PI*t*{wobble_f2}))"
    )
    blur_enable = f"between(t,0,0.5)+between(t,{end_start},{end_start}+0.5)"

    filt = (
        f"[0:v]fps={F},scale=1296:2304,"
        f"rotate='{angle_expr}':ow=rotw(iw):oh=roth(ih),"
        f"gblur=sigma={blur_sigma}:steps=3:enable='{blur_enable}',"
        f"crop=1080:1920[v]"
    )

    cmd = [
        "ffmpeg", "-n",
        "-i", str(in_mp4),
        "-t", f"{L:.3f}",
        "-filter_complex", filt,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-r", str(F), "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out_mp4)
    ]
    run_cmd(cmd)
    return True

# --------------------------------- main ---------------------------------

def main():
    ap = argparse.ArgumentParser(description="Glitch → loop+concat → VFX → wobble-blur transitions (no overwrite, verbose)")
    ap.add_argument("image", type=Path, help="Input image path")
    ap.add_argument("duration", type=float, help="Total output duration in seconds (e.g., 8.0)")
    ap.add_argument("--fps", type=int, default=60, help="Frames per second (default: 60)")
    ap.add_argument("--base", type=Path, default=None, help="Output basename (default: image stem)")
    ap.add_argument("--out", type=Path, default=None, help="Output filename")
    ap.add_argument("--glitch2_secs", type=float, default=2.0, help="Duration of heavy glitch segment (default: 2.0s)")
    # Transition tuning
    ap.add_argument("--wobble_main", type=float, default=0.008, help="Main wobble radians amplitude during transitions")
    ap.add_argument("--wobble_jitter", type=float, default=0.002, help="Jitter wobble radians amplitude during transitions")
    ap.add_argument("--wobble_f1", type=float, default=1.0, help="Wobble frequency 1 (Hz)")
    ap.add_argument("--wobble_f2", type=float, default=1.0, help="Wobble frequency 2 (Hz)")
    ap.add_argument("--blur", type=int, default=6, help="Gaussian blur sigma during transitions")
    args = ap.parse_args()

    img_path = args.image
    duration = float(args.duration)
    fps = int(args.fps)
    base = args.base or img_path.with_suffix("")
    base = Path(str(base))

    glitch2_secs = float(args.glitch2_secs)

    # Durations
    seg1_secs = max(0.0, duration - glitch2_secs)
    seg2_secs = glitch2_secs

    # Frames to generate initially (GIF1 loops later)
    gif1_frames = max(2, int(round(min(seg1_secs if seg1_secs > 0 else 2.0, 2.0) * fps)))
    gif2_frames = max(2, int(round(seg2_secs * fps)))

    gif1 = Path(f"{base}_glitch1.gif")
    gif2 = Path(f"{base}_glitch2.gif")
    concat_raw = Path(f"{base}_raw.mp4")
    vfx_mp4 = Path(f"{base}_vfx.mp4")
    final_mp4 = args.base or Path(f"{base}_final.mp4")

    log(f"[SETUP] image={img_path} duration={duration}s fps={fps} glitch2_secs={glitch2_secs}s")
    log(f"[PLAN] seg1(loop)={seg1_secs:.3f}s seg2(heavy)={seg2_secs:.3f}s")
    log(f"[FRAMES] gif1={gif1_frames} gif2={gif2_frames}")
    log(f"[OUTPUTS] {gif1}, {gif2}, {concat_raw}, {vfx_mp4}, {final_mp4}")

    # 1) GIFs
    created_g1 = make_glitch_gif(img_path, gif1, fps=fps, n_frames=gif1_frames, mode="constant", amt_start=0.7, amt_end=0.7)
    created_g2 = make_glitch_gif(img_path, gif2, fps=fps, n_frames=gif2_frames, mode="ramp", amt_start=3.0, amt_end=5.0)
    # If either GIF was (re)generated, downstream is stale
    if created_g1 or created_g2:
        safe_delete(concat_raw, vfx_mp4, final_mp4)

    # 2) Concat
    created_concat = build_concat_raw(gif1, gif2, concat_raw, fps=fps, dur_total=duration, dur_g2=seg2_secs)
    if created_concat:
        safe_delete(vfx_mp4, final_mp4)

    # 3) VFX
    created_vfx = apply_vfx(concat_raw, vfx_mp4, fps=fps, dur_total=duration)
    if created_vfx:
        safe_delete(final_mp4)

    # 4) Transitions
    add_transitions(vfx_mp4, final_mp4, fps=fps, dur_total=duration,
                    wobble_main=args.wobble_main, wobble_jitter=args.wobble_jitter,
                    wobble_f1=args.wobble_f1, wobble_f2=args.wobble_f2,
                    blur_sigma=args.blur)

    shutil.copy(final_mp4, args.out)
    log("[DONE]")
    log(f" - GIF 1: {gif1}")
    log(f" - GIF 2: {gif2}")
    log(f" - MP4 raw (looped+concat): {concat_raw}")
    log(f" - MP4 with VFX: {vfx_mp4}")
    log(f" - MP4 final with transitions: {final_mp4}")
    log(f" - Out File: {args.out}")

if __name__ == "__main__":
    main()
