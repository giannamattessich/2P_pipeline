from __future__ import annotations
from pathlib import Path
import json
import numpy as np

def ensure_dir(p: Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_npy(path: Path, arr: np.ndarray, overwrite: bool = False) -> None:
    path = Path(path)
    if path.exists() and not overwrite:
        return
    np.save(path, arr)

def load_npy(path: Path, mmap_mode: str = "r"):
    return np.load(Path(path), mmap_mode=mmap_mode)

def write_json(path: Path, obj: dict, overwrite: bool = True) -> None:
    path = Path(path)
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
