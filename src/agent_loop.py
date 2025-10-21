# src/agent_loop.py
import os, json, argparse, time
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv()

from anemone_runner import run_anemone    # 既存：exe呼び出し（実機 or モック）
from pointcloud_gen import make_pointcloud  # 既存：点群生成（必要なら使う）

# ==== ChatGPT（Responses API） ====
from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are an optimization orchestrator for a Solid-State Electroaerodynamic Propulsion (SSEP) simulator.
Goal: maximize thrust_density while keeping parameters within safe bounds.
Always propose the next params as a strict JSON with keys: V_kV (number), gap_m (number), phi (number), stages (integer), and an optional note.
Hard bounds:
- 15 <= V_kV <= 40
- 0.0005 <= gap_m <= 0.006
- 0.8 <= phi <= 1.8
- 1 <= stages <= 6
Return ONLY JSON (no explanations) like:
{"V_kV": 35.0, "gap_m": 0.0012, "phi": 1.2, "stages": 3, "note": "reason"}
"""

def propose_next(history):
    """
    history: [{params: {...}, metrics: {...}}, ...]
    returns: dict like {"V_kV": 35.0, "gap_m": 0.0012, "phi": 1.2, "stages": 3, "note": "..."}
    """
    user_content = (
        "We will iterate. Here is the history as JSON.\n"
        "Each item has params (V_kV,gap_m,phi,stages) and metrics (thrust_density,current_density,power).\n"
        f"{json.dumps(history, ensure_ascii=False)}\n"
        "Propose the next parameters within the hard bounds. Output strict JSON only."
    )

    # ★ Chat Completions の JSONモード（SDK 2.xで安定）
    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # 軽くて速い。必要なら gpt-4.1 / gpt-4o に変更OK
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    content = resp.choices[0].message.content
    return json.loads(content)

def clamp_params(p: Dict[str, Any]) -> Dict[str, Any]:
    # 念のため上下限をサニタイズ
    p["V_kV"] = max(15.0, min(40.0, float(p["V_kV"])))
    p["gap_m"] = max(0.0005, min(0.006, float(p["gap_m"])))
    p["phi"] = max(0.8, min(1.8, float(p["phi"])))
    p["stages"] = int(max(1, min(6, int(p["stages"]))))
    return p

def run_loop(pcd_path: str, trials: int = 20, seed_params: Dict[str, Any] = None):
    """
    pcd_path: あなたが指定する点群（そのまま your_sim.exe に渡す）
    trials:   何回まわすか（GPTの試行回数）
    """
    history: List[Dict[str, Any]] = []

    # 初期案（無ければ中央付近）
    if seed_params is None:
        seed_params = {"V_kV": 30.0, "gap_m": 0.002, "phi": 1.2, "stages": 3}

    params = clamp_params(seed_params)

    best = None  # {"params":..., "metrics":...}

    for t in range(trials):
        # 1) シミュレータ実行（実機orモック）
        metrics = run_anemone(
            pcd_path,
            {"V": params["V_kV"]*1000.0, "gap": params["gap_m"], "phi": params["phi"], "stages": params["stages"]},
        )
        record = {"params": params, "metrics": metrics}
        history.append(record)

        # ベスト更新
        if (best is None) or (metrics["thrust_density"] > best["metrics"]["thrust_density"]):
            best = record

        print(f"[{t+1}/{trials}] params={params}  -> thrust_density={metrics['thrust_density']:.3f}")

        # 2) 次案をGPTに提案させる
        try:
            nxt = propose_next(history)
            params = clamp_params(nxt)
        except Exception as e:
            # GPTが失敗したら、ベスト近傍を微調整
            print("GPT propose failed, fallback:", e)
            params = clamp_params({
                "V_kV": best["params"]["V_kV"] * 0.98,
                "gap_m": max(0.0005, best["params"]["gap_m"] * 0.9),
                "phi": min(1.8, best["params"]["phi"] * 1.02),
                "stages": best["params"]["stages"],
            })

    # まとめ
    summary = {
        "best_params": best["params"],
        "best_metrics": best["metrics"],
        "history": history,
    }
    outdir = "runs/latest_gpt"
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\n=== BEST (GPT-loop) ===")
    print(json.dumps(summary["best_params"], ensure_ascii=False, indent=2))
    print(json.dumps(summary["best_metrics"], ensure_ascii=False, indent=2))
    print(f"\nSaved: {outdir}/summary.json")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcd", type=str, required=True, help="点群ファイルのパス（そのままシミュレータに渡す）")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--V_kV", type=float, default=30.0)
    ap.add_argument("--gap_m", type=float, default=0.002)
    ap.add_argument("--phi", type=float, default=1.2)
    ap.add_argument("--stages", type=int, default=3)
    args = ap.parse_args()

    seed = {"V_kV": args.V_kV, "gap_m": args.gap_m, "phi": args.phi, "stages": args.stages}
    run_loop(args.pcd, trials=args.trials, seed_params=seed)