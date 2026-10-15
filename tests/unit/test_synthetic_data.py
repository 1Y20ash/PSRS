import csv
import hashlib
import json

import pytest

from psrs.services.synthetic_data import generate_dataset


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generation_is_reproducible_for_same_seed(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    manifest_a = generate_dataset(first, seed=123, historical_days=10, forecast_days=3)
    manifest_b = generate_dataset(second, seed=123, historical_days=10, forecast_days=3)

    expected_files = [
        "items.csv",
        "locations.csv",
        "inventory_events.csv",
        "demand_history.csv",
        "evaluation_ground_truth.csv",
        "dataset_manifest.json",
    ]
    for filename in expected_files:
        assert file_hash(first / filename) == file_hash(second / filename)
    assert manifest_a == manifest_b


def test_ground_truth_is_separate_and_dates_do_not_overlap(tmp_path):
    output = tmp_path / "dataset"
    manifest = generate_dataset(output, seed=99, historical_days=5, forecast_days=2)

    with (output / "demand_history.csv").open(newline="", encoding="utf-8") as handle:
        history = list(csv.DictReader(handle))
    with (output / "evaluation_ground_truth.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        truth = list(csv.DictReader(handle))

    history_dates = {row["date"] for row in history}
    truth_dates = {row["date"] for row in truth}
    assert history_dates.isdisjoint(truth_dates)
    assert max(history_dates) < min(truth_dates)
    assert "actual_demand_units" not in history[0]
    assert "demand_units" not in truth[0]
    assert manifest["evaluation_only_files"] == ["evaluation_ground_truth.csv"]


def test_generated_rows_have_expected_cardinality_and_nonnegative_values(tmp_path):
    output = tmp_path / "dataset"
    manifest = generate_dataset(output, seed=7, historical_days=4, forecast_days=2)

    assert manifest["row_counts"]["items.csv"] == 8
    assert manifest["row_counts"]["locations.csv"] == 6
    assert manifest["row_counts"]["demand_history.csv"] == 8 * 6 * 4
    assert manifest["row_counts"]["evaluation_ground_truth.csv"] == 8 * 6 * 2

    for filename, value_column in [
        ("demand_history.csv", "demand_units"),
        ("evaluation_ground_truth.csv", "actual_demand_units"),
        ("inventory_events.csv", "quantity"),
    ]:
        with (output / filename).open(newline="", encoding="utf-8") as handle:
            assert all(int(row[value_column]) >= 0 for row in csv.DictReader(handle))


@pytest.mark.parametrize("kwargs", [
    {"historical_days": 0},
    {"forecast_days": 0},
])
def test_generation_rejects_empty_time_windows(tmp_path, kwargs):
    with pytest.raises(ValueError):
        generate_dataset(tmp_path / "bad", **kwargs)


def test_manifest_marks_data_as_synthetic_and_separates_inputs(tmp_path):
    output = tmp_path / "dataset"
    generate_dataset(output, seed=42, historical_days=2, forecast_days=1)
    manifest = json.loads((output / "dataset_manifest.json").read_text(encoding="utf-8"))

    assert manifest["synthetic_data_only"] is True
    assert manifest["fictional_locations_only"] is True
    assert "evaluation_ground_truth.csv" not in manifest["algorithm_visible_files"]
