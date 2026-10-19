"""Poll Results Visualizer - pipeline entry point.

    python main.py          # generate data (if missing) -> load -> clean -> analyse
    python main.py --app    # same, then launch the Streamlit dashboard
"""
import argparse
import subprocess
import sys
from pathlib import Path

from src.analytics import analyze_data
from src.data_processor import clean_data, load_data

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "poll_responses.csv"


def run_pipeline() -> None:
    print("=" * 55)
    print(" POLL RESULTS VISUALIZER")
    print("=" * 55)

    # 1. data (generate a synthetic poll dataset if none exists)
    if not DATA_FILE.exists():
        print("[1/4] No dataset found - generating synthetic poll data...")
        from src.data_generator import main as generate_data
        generate_data()
    else:
        print(f"[1/4] Using existing dataset: {DATA_FILE.name}")

    # 2. load
    df = load_data(DATA_FILE)
    print(f"[2/4] Loaded {len(df):,} rows and {df.shape[1]} columns")

    # 3. clean
    df, report = clean_data(df)
    print(f"[3/4] Cleaning done. Rows after cleaning: {len(df):,}")
    for key, value in report.items():
        print(f"      - {key}: {value}")

    # 4. analyse
    results = analyze_data(df)
    print(f"[4/4] Analysis complete. Sections: {', '.join(map(str, results.keys()))}")
    for key, value in results.items():
        if isinstance(value, (int, float, str)):
            print(f"      - {key}: {value}")

    print("\nDone. Launch the dashboard with:  streamlit run app.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll Results Visualizer")
    parser.add_argument("--app", action="store_true", help="launch the Streamlit dashboard afterwards")
    args = parser.parse_args()

    run_pipeline()
    if args.app:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")], cwd=ROOT)


if __name__ == "__main__":
    main()