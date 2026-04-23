"""
download_snap.py — SNAP Dataset Downloader
===========================================
Downloads Stanford SNAP graph datasets and caches them locally.

Usage:
    python download_snap.py                    # Download all
    python download_snap.py --dataset ego-Facebook   # Download specific
    python download_snap.py --list             # List available

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import argparse
import gzip
import os
import sys
import urllib.request
from pathlib import Path

# Data directories
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"


SNAP_DATASETS = {
    "ego-Facebook": {
        "url": "https://snap.stanford.edu/data/facebook_combined.txt.gz",
        "filename": "facebook_combined.txt.gz",
        "description": "Social network (scale-free), ~4K nodes, ~88K edges",
    },
    "roadNet-CA": {
        "url": "https://snap.stanford.edu/data/roadNet-CA.txt.gz",
        "filename": "roadNet-CA.txt.gz",
        "description": "California road network (grid-like), ~2M nodes, ~2.8M edges",
    },
    "com-LiveJournal": {
        "url": "https://snap.stanford.edu/data/bigdata/communities/com-lj.ungraph.txt.gz",
        "filename": "com-lj.ungraph.txt.gz",
        "description": "LiveJournal social network, ~4M nodes, ~34M edges",
    },
}


def download_dataset(name: str) -> bool:
    """Download a single SNAP dataset."""
    if name not in SNAP_DATASETS:
        print(f"❌ Unknown dataset: {name}")
        print(f"   Available: {list(SNAP_DATASETS.keys())}")
        return False

    meta = SNAP_DATASETS[name]
    filepath = RAW_DIR / meta["filename"]

    if filepath.exists():
        print(f"✓ {name} already downloaded at {filepath}")
        return True

    print(f"📥 Downloading {name}...")
    print(f"   URL: {meta['url']}")
    print(f"   Description: {meta['description']}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        urllib.request.urlretrieve(
            meta["url"],
            str(filepath),
            reporthook=_progress_hook
        )
        print(f"\n✓ Downloaded to {filepath}")

        # Verify file size
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.1f} MB")
        return True

    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        if filepath.exists():
            filepath.unlink()
        return False


def _progress_hook(block_num, block_size, total_size):
    """Progress bar for urllib download."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, downloaded * 100 / total_size)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r   [{percent:5.1f}%] {mb_downloaded:.1f} / {mb_total:.1f} MB")
    else:
        mb_downloaded = downloaded / (1024 * 1024)
        sys.stdout.write(f"\r   {mb_downloaded:.1f} MB downloaded")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Download SNAP graph datasets")
    parser.add_argument("--dataset", type=str, help="Specific dataset to download")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--all", action="store_true", help="Download all datasets")
    args = parser.parse_args()

    if args.list:
        print("\n📊 Available SNAP Datasets:")
        print("=" * 60)
        for name, meta in SNAP_DATASETS.items():
            filepath = RAW_DIR / meta["filename"]
            status = "✓ downloaded" if filepath.exists() else "✗ not downloaded"
            print(f"  {name:20s} — {meta['description']}")
            print(f"  {'':20s}   Status: {status}")
            print()
        return

    if args.dataset:
        download_dataset(args.dataset)
    elif args.all:
        print("📥 Downloading all SNAP datasets...\n")
        for name in SNAP_DATASETS:
            download_dataset(name)
            print()
    else:
        # Default: download ego-Facebook (smallest, good for testing)
        print("📥 Downloading ego-Facebook (default, good for testing)...\n")
        download_dataset("ego-Facebook")


if __name__ == "__main__":
    main()
