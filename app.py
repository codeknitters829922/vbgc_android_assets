import json
import os
import mimetypes
from pathlib import Path
from flask import Flask, send_from_directory, abort, jsonify, request, url_for

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/webm", ".webm")
mimetypes.add_type("image/webp", ".webp")

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

FOLDERS = {
    "video-bg": ASSETS_DIR / "video-bg",
    "image-assets": ASSETS_DIR / "image-assets",
    "image-and-video": ASSETS_DIR / "image-and-video",
}

for folder in FOLDERS.values():
    folder.mkdir(parents=True, exist_ok=True)


def _safe_resolve(root: Path, filename: str) -> Path:
    target = (root / filename).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        abort(404)
    return target


@app.get("/")
def index():
    return jsonify({
        "service": "vbgc_android_assets",
        "folders": {
            key: {
                "list": url_for("list_folder", folder=key, _external=True),
                "file": url_for("get_file", folder=key, filename="<filename>", _external=True),
            }
            for key in FOLDERS
        },
    })


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def _file_url(folder: str, name: str) -> str:
    return url_for("get_file", folder=folder, filename=name, _external=True)


def _load_manifest(root: Path):
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return None
    with manifest_path.open() as f:
        return json.load(f)


@app.get("/<folder>/")
def list_folder(folder: str):
    if folder not in FOLDERS:
        abort(404)
    root = FOLDERS[folder]

    manifest = _load_manifest(root)
    if manifest is not None:
        items = []
        for entry in manifest.get("items", []):
            item = {**entry, "pro": bool(entry.get("pro", False))}
            if entry.get("thumbnail"):
                item["thumbnail_url"] = _file_url(folder, entry["thumbnail"])
            if entry.get("video"):
                item["video_url"] = _file_url(folder, entry["video"])
            items.append(item)
        return jsonify({"folder": folder, "count": len(items), "items": items})

    files = []
    for entry in sorted(root.iterdir()):
        if entry.is_file() and not entry.name.startswith(".") and entry.name != "manifest.json":
            files.append({
                "name": entry.name,
                "size": entry.stat().st_size,
                "url": _file_url(folder, entry.name),
            })
    return jsonify({"folder": folder, "count": len(files), "files": files})


@app.get("/<folder>/<path:filename>")
def get_file(folder: str, filename: str):
    if folder not in FOLDERS:
        abort(404)
    root = FOLDERS[folder]
    target = _safe_resolve(root, filename)
    if not target.is_file():
        abort(404)
    return send_from_directory(
        root,
        filename,
        as_attachment=request.args.get("download") == "1",
        conditional=True,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
