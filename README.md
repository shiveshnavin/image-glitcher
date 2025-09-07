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

