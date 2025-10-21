import os, json
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

_OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def available() -> bool:
    return bool(_OPENAI_KEY)

def to_spec(user_text: str) -> Dict[str, Any]:
    """
    ChatGPT（Responses API）の Structured Outputs を使って
    自然言語→JSON（探索空間・目的）に変換する想定の関数。
    APIキーが未設定の場合は、デフォルトのスキーマを返す。
    """
    default = {
        "objective": "maximize_thrust_density",
        "search_space": {
            "gap_mm": [0.8, 6.0],
            "V_kV": [15.0, 40.0],
            "phi": [0.8, 1.8],
            "stages": [1, 6]
        },
        "budget": {"trials": 30, "parallel": 1}
    }

    if not available():
        return default

    # 実運用では OpenAI API に接続してスキーマ出力を取得する。
    return default

def summarize(log_text: str) -> str:
    if not available():
        return (log_text[:500] + "...") if len(log_text) > 500 else log_text
    return (log_text[:500] + "...") if len(log_text) > 500 else log_text