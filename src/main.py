import argparse, json
from optimizer import optimize
from orchestrator_chatgpt import to_spec

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--use-mock", action="store_true")
    parser.add_argument("--ask", type=str, default="gapは0.8〜6mm、Vは15〜40kVで推力密度最大化")
    args = parser.parse_args()

    spec = to_spec(args.ask)
    print("[Spec]", json.dumps(spec, ensure_ascii=False, indent=2))
    best = optimize(spec["search_space"], trials=args.trials)

    print("\n=== Best Params ===")
    for k, v in best.items():
        print(f"{k}: {v}")
    print("\n結果は runs/latest/ に保存されています。")

if __name__ == "__main__":
    main()