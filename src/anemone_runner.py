import subprocess
import json
import tempfile
from pathlib import Path

ANEMONE_EXE = Path(__file__).resolve().parent.parent / "anemone.exe"

def run_anemone(pcd_path, params):
    """anemone.exeを呼び出して結果(JSON)を受け取る"""

    # agent_loop.py から来るパラメータのキーに合わせる
    cfg = {
        "V": params.get("V", params.get("V_kV", 0) * 1000),  # V or V_kV どちらでも対応
        "gap": params.get("gap", params.get("gap_m", 0)),
        "phi": params.get("phi", 1.0),
        "stages": params.get("stages", 1)
    }

    # 一時cfgファイル作成
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as cfg_file:
        json.dump(cfg, cfg_file)
        cfg_file_path = cfg_file.name

    result_path = Path(tempfile.mktemp(suffix=".json"))

    cmd = [
        str(ANEMONE_EXE),
        "--pcd", str(pcd_path),
        "--cfg", str(cfg_file_path),
        "--out", str(result_path)
    ]

    subprocess.run(cmd, check=True)

    with open(result_path, "r") as f:
        result = json.load(f)

    return result