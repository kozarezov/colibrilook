"""Preserve downloaded media quality; never upscale or recompress video.
Usage: python content/tools/prepare_media.py --source .qa/media
Only refreshes assets already selected in static/images/editorial and static/video.
Raw downloads are kept outside the repository; content/media.json records provenance.
"""
import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image


def prepare(source: Path, root: Path):
    photos = root / 'static/images/editorial'
    videos = root / 'static/video'
    for raw in source.glob('*-photo.jpg'):
        target = photos / (raw.name.split('-')[0] + '.webp')
        if target.exists():
            with Image.open(raw) as image:
                image.save(target, lossless=True)
    with TemporaryDirectory() as tmp:
        for raw in source.glob('*.mp4'):
            target = videos / raw.name
            if not target.exists():
                continue
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-map', '0', '-c', 'copy', '-movflags', '+faststart', str(target)], check=True)
            # PNG extraction keeps the actual decoded video frame without JPEG recompression.
            poster = Path(tmp) / (raw.stem + '.png')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '0.5', '-i', str(raw), '-frames:v', '1', str(poster)], check=True)
            with Image.open(poster) as image:
                image.save(photos / (raw.stem + '-poster.webp'), lossless=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source, Path(__file__).resolve().parents[2])
