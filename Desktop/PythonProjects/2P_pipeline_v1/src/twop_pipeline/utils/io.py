from __future__ import annotations
from pathlib import Path
import json, traceback, joblib
import numpy as np, pandas as pd

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

def read_parquet(parquet_path: Path) -> None:
    path = Path(parquet_path)
    if not path.exists():
        raise ValueError(f'Could not read parquet {parquet_path} because the path does not exist.')
    try:
        dataframe = pd.read_parquet(path)
    except:
        print(f'Could not read parquet')
        traceback.print_exc()    
    return dataframe

def save_parquet(dataframe: pd.DataFrame, out_parquet_path: Path, overwrite: bool = True) -> None:
    if not overwrite:
        return
    if not out_parquet_path.endswith('.parquet'):
        out_parquet_path += '.parquet'
    path = Path(out_parquet_path)
    try:
        dataframe.to_parquet(path)
        print(f'Saved state parquet at {out_parquet_path}!')
    except:
        print(f'Could not read parquet')
        traceback.print_exc()    
    return dataframe

def read_joblib(outpath):
    path = Path(outpath)
    if not path.exists():
        raise ValueError(f'Provided path for compressed joblib object does not exist')
    obj = joblib.load(path)
    return obj 

def save_obj_joblib(obj, outpath) -> None:
    if not outpath.endswith('.joblib'):
        outpath += '.joblib'
    path = Path(outpath)
    joblib.dump(obj, path, compress=("lz4", 3))