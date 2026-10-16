"""Baseline and leakage-safe lag-based demand forecasting."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Mapping
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

@dataclass(frozen=True)
class ForecastResult:
    location_id: str
    item_id: str
    model: str
    horizon: int
    predictions: list[float]
    baseline_mae: float | None
    ml_mae: float | None
    baseline_wape: float | None = None
    ml_wape: float | None = None
    def to_dict(self) -> dict:
        return asdict(self)

def _series(rows: Iterable[Mapping[str, object]], location_id: str, item_id: str) -> pd.Series:
    selected = [{"date": row["date"], "demand": float(row["demand_units"])}
                for row in rows if str(row["location_id"]) == location_id and str(row["item_id"]) == item_id]
    if not selected:
        raise ValueError("No demand history exists for the requested series")
    frame = pd.DataFrame(selected)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.groupby("date", as_index=True)["demand"].sum().sort_index()
    full = frame.asfreq("D")
    if full.isna().any():
        raise ValueError("Demand history contains missing daily periods")
    if not np.isfinite(full.to_numpy()).all() or (full < 0).any():
        raise ValueError("Demand history must contain finite, non-negative values")
    return full

def _wape(actual, predicted) -> float | None:
    denominator = float(np.abs(actual).sum())
    if denominator == 0:
        return None
    return float(np.abs(np.asarray(actual) - np.asarray(predicted)).sum() / denominator * 100.0)

def forecast_demand(rows: Iterable[Mapping[str, object]], location_id: str, item_id: str,
                    horizon: int = 7, model: str = "auto") -> ForecastResult:
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1 or horizon > 90:
        raise ValueError("horizon must be an integer between 1 and 90")
    if model not in {"auto", "baseline", "ml"}:
        raise ValueError("model must be one of: auto, baseline, ml")
    values = _series(rows, location_id, item_id)
    baseline = float(values.iloc[-min(7, len(values)):].mean())
    if len(values) < 10 or model == "baseline":
        return ForecastResult(location_id, item_id, "moving_average", horizon,
                              [round(max(0.0, baseline), 2)] * horizon, None, None, None, None)
    data = pd.DataFrame({"y": values})
    for lag in (1, 2, 3, 7):
        data[f"lag_{lag}"] = data["y"].shift(lag)
    data["weekday"] = data.index.dayofweek
    data = data.dropna()
    if len(data) < 5:
        return ForecastResult(location_id, item_id, "moving_average", horizon,
                              [round(max(0.0, baseline), 2)] * horizon, None, None, None, None)
    split = max(1, min(len(data) - 1, int(len(data) * 0.8)))
    train, validation = data.iloc[:split], data.iloc[split:]
    features = ["lag_1", "lag_2", "lag_3", "lag_7", "weekday"]
    estimator = RandomForestRegressor(n_estimators=100, random_state=26251, min_samples_leaf=2)
    estimator.fit(train[features], train["y"])
    ml_validation = np.maximum(0.0, estimator.predict(validation[features]))
    # Rolling one-step baseline: only history preceding each validation date is used.
    prior = list(train["y"].astype(float))
    baseline_validation = []
    for timestamp in validation.index:
        baseline_validation.append(float(np.mean(prior[-min(7, len(prior)):])) if prior else 0.0)
        prior.append(float(data.loc[timestamp, "y"]))
    baseline_mae = float(mean_absolute_error(validation["y"], baseline_validation))
    ml_mae = float(mean_absolute_error(validation["y"], ml_validation))
    baseline_wape = _wape(validation["y"], baseline_validation)
    ml_wape = _wape(validation["y"], ml_validation)
    use_ml = model == "ml" or (model == "auto" and ml_mae <= baseline_mae)
    if use_ml:
        estimator.fit(data[features], data["y"])
        history = list(values.astype(float))
        predictions = []
        for offset in range(horizon):
            row = [[history[-1], history[-2], history[-3], history[-7],
                    (values.index[-1].dayofweek + offset + 1) % 7]]
            prediction = max(0.0, float(estimator.predict(row)[0]))
            predictions.append(round(prediction, 2))
            history.append(prediction)
        selected_model = "random_forest_lag"
    else:
        predictions = [round(max(0.0, baseline), 2)] * horizon
        selected_model = "moving_average"
    return ForecastResult(location_id, item_id, selected_model, horizon, predictions,
                          round(baseline_mae, 4), round(ml_mae, 4),
                          round(baseline_wape, 4) if baseline_wape is not None else None,
                          round(ml_wape, 4) if ml_wape is not None else None)
