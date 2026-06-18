# vbgc_android_assets

Flask service that serves static asset folders (videos, images) over HTTP for the VBGC Android app.

## Layout

```
app.py              # Flask app — all routes live here
requirements.txt    # Flask + gunicorn
assets/
  video-bg/         # video backgrounds (mp4/webm)
  image-assets/     # image assets
  image-and-video/  # mixed media
```

The three asset folders are the only content served. They're created automatically on startup if missing. In prod, drop files directly into these folders — the listing endpoint picks them up without a restart.

## URL conventions

- `GET /` — JSON index with URL templates for each folder
- `GET /healthz` — health check
- `GET /<folder>/` — JSON list. Default: `files` (name, size, url). If the folder contains `manifest.json`, returns `items` from the manifest with `thumbnail_url`, `video_url`, and `pro` populated (other manifest fields are passed through).
- `GET /<folder>/<filename>` — serve the file; supports HTTP Range (videos stream in `<video>` tags). Add `?download=1` to force `Content-Disposition: attachment`

`<folder>` must be one of `video-bg`, `image-assets`, `image-and-video`. Anything else returns 404. Path traversal is blocked in `_safe_resolve` (app.py).

## Run

Dev:
```
pip install -r requirements.txt
python app.py                              # PORT env override, defaults to 5000
```

Prod:
```
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Conventions

- Folder slugs are kebab-case and fixed in the `FOLDERS` dict in app.py — don't rename without updating any clients consuming these URLs.
- `.gitkeep` files preserve the empty asset dirs in git; actual assets are gitignored (see `.gitignore`).
- New asset categories: add a new entry to `FOLDERS` in app.py and a matching `assets/<slug>/.gitkeep`.
