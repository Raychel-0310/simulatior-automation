# src/anemone_runner.py
import subprocess
import json
import tempfile
from pathlib import Path
import os, sys
USE_DUMMY = os.getenv("USE_DUMMY", "1" if sys.platform != "win32" else "0") == "1"
ANEMONE_EXE = Path(__file__).resolve().parent.parent / "anemone.exe"
TIMEOUT_SEC = 300  # シミュ1本のタイムアウト（適宜調整）

def run_anemone(pcd_path, params):
    """
    anemone.exe を起動し、結果JSONを返す。
    params は {"V": [V単位], "gap": [m], "phi": float, "stages": int} 形式を想定。
    """
    if not ANEMONE_EXE.exists():
        raise FileNotFoundError(f"anemone.exe not found: {ANEMONE_EXE}")

    # 設定ファイルを一時生成（UTF-8 / CRLF気にしないでOK）
    cfg = {
        "V": params.get("V", params.get("V_kV", 0)*1000),
        "gap": params.get("gap", params.get("gap_m", 0.0)),
        "phi": float(params.get("phi", 1.0)),
        "stages": int(params.get("stages", 1)),
    }
    cfg_file = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
    try:
        json.dump(cfg, cfg_file)
        cfg_file.flush()
    finally:
        cfg_file.close()
    cfg_path = Path(cfg_file.name)

    result_path = Path(tempfile.mktemp(suffix=".json"))

    cmd = [
        str(ANEMONE_EXE),
        "--pcd", str(pcd_path),
        "--cfg", str(cfg_path),
        "--out", str(result_path),
    ]

    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ANEMONE timed out after {TIMEOUT_SEC}s")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ANEMONE failed (exit {e.returncode})\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )

    if not result_path.exists():
        # もし標準出力でJSONを返す実装なら、こっちを使う
        if completed.stdout.strip().startswith("{"):
            return json.loads(completed.stdout)
        raise FileNotFoundError(f"Result file not found: {result_path}")

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    # 軽いバリデーション
    for k in ("thrust_density", "current_density", "power"):
        if k not in result:
            raise ValueError(f"Result JSON missing key: {k}")
    return result