"""Command-line entry point for generating the PSRS synthetic dataset."""
import argparse
from pathlib import Path

from psrs.services.synthetic_data import DEFAULT_SEED, generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate fictional PSRS data for reproducible experiments."
    )
    parser.add_argument("--output", default="data/generated", help="Output directory")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--historical-days", type=int, default=90)
    parser.add_argument("--forecast-days", type=int, default=14)
    args = parser.parse_args()

    manifest = generate_dataset(
        Path(args.output),
        seed=args.seed,
        historical_days=args.historical_days,
        forecast_days=args.forecast_days,
    )
    print(f"Generated synthetic dataset in: {Path(args.output).resolve()}")
    print(f"Seed: {manifest['seed']}")
    print(f"Historical rows: {manifest['row_counts']['demand_history.csv']}")
    print(f"Evaluation-only rows: {manifest['row_counts']['evaluation_ground_truth.csv']}")
    print("Keep evaluation_ground_truth.csv out of algorithm-visible inputs.")


if __name__ == "__main__":
    main()
