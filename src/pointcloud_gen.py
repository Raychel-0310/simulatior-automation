import os, hashlib, json, pathlib
from typing import Dict

RUNS_DIR = pathlib.Path("runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def _hash_params(params: Dict) -> str:
    payload = json.dumps(params, sort_keys=True).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]

def make_pointcloud(params: Dict) -> str:
    """
    パラメータから点群(.pcd)を生成してパスを返す（スタブ）。
    実運用では CAD 生成 → サンプリングに置き換えて下さい。
    """
    hid = _hash_params(params)
    pcd_path = RUNS_DIR / f"{hid}.pcd"

    if not pcd_path.exists():
        gap = float(params.get("gap", 0.002))
        stages = int(params.get("stages", 3))
        points = []
        for i in range(100):
            x = i * 1e-3
            y = (i % max(1, stages)) * gap
            points.append((x, y, 0.0))

        with open(pcd_path, "w") as f:
            f.write("# .PCD MOCK (x y z)\n")
            for x, y, z in points:
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")

    return str(pcd_path)