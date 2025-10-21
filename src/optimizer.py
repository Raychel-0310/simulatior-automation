import csv, pathlib
from typing import Dict, Any
import optuna

from pointcloud_gen import make_pointcloud
from anemone_runner import run_anemone

RUNS_DIR = pathlib.Path("runs")
LATEST_DIR = RUNS_DIR / "latest"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def constraint_ok(p: Dict[str, Any]) -> bool:
    return p.get("gap", 0.002) >= 0.0005

def objective_factory(search_space: Dict[str, Any]):
    def objective(trial: optuna.trial.Trial):
        gap = trial.suggest_float("gap", float(search_space["gap_mm"][0]) / 1000.0,
                                        float(search_space["gap_mm"][1]) / 1000.0)
        V_kV = trial.suggest_float("V_kV", float(search_space["V_kV"][0]), float(search_space["V_kV"][1]))
        phi_low, phi_high = search_space.get("phi", [1.0, 1.0])
        stages_low, stages_high = search_space.get("stages", [3, 3])
        phi = trial.suggest_float("phi", float(phi_low), float(phi_high))
        stages = trial.suggest_int("stages", int(stages_low), int(stages_high))

        params = {"gap": gap, "phi": phi, "stages": stages}
        if not constraint_ok(params):
            raise optuna.TrialPruned()

        pcd_path = make_pointcloud(params)
        metrics = run_anemone(pcd_path, {"V": V_kV * 1000.0, "phi": phi, "stages": stages, "gap": gap})

        LATEST_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = LATEST_DIR / "history.csv"
        header = ["trial", "gap", "phi", "stages", "V_kV", "thrust_density", "current_density", "power", "pcd_path"]
        write_header = not csv_path.exists()
        with open(csv_path, "a", newline="") as f:
            w = csv.writer(f)
            if write_header: w.writerow(header)
            w.writerow([trial.number, gap, phi, stages, V_kV, metrics["thrust_density"], metrics["current_density"], metrics["power"], pcd_path])

        return metrics["thrust_density"]
    return objective

def optimize(search_space: Dict[str, Any], trials: int = 30) -> Dict[str, Any]:
    study = optuna.create_study(direction="maximize")
    study.optimize(objective_factory(search_space), n_trials=trials)
    best = study.best_params
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    (LATEST_DIR / "best_params.json").write_text(str(best), encoding="utf-8")
    return best