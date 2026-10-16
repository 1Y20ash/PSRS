"""Baseline and simple lag-based demand forecasting."""
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

    def to_dict(self) -> dict:
        return asdict(self)


def _series(rows: Iterable[Mapping[str, object]], location_id: str, item_id: str) -> pd.Series:
    selected = [
        {"date": row["date"], "demand": float(row["demand_units"])}
        for row in rows
        if str(row["location_id"]) == location_id and str(row["item_id"]) == item_id
    ]
    if not selected:
        raise ValueError("No demand history exists for the requested series")
    frame = pd.DataFrame(selected)
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.groupby("date", as_index=True)["demand"].sum().sort_index()
    full = frame.asfreq("D")
    if full.isna().any():
        raise ValueError("Demand history contains missing daily periods")
    if (full < 0).any():
        raise ValueError("Demand history contains negative values")
    return full


def forecast_demand(
    rows: Iterable[Mapping[str, object]],
    location_id: str,
    item_id: str,
    horizon: int = 7,
    model: str = "auto",
) -> ForecastResult:
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    values = _series(rows, location_id, item_id)
    window = min(7, len(values))
    baseline = float(values.iloc[-window:].mean())
    if len(values) < 10 or model == "baseline":
        return ForecastResult(location_id, item_id, "moving_average", horizon,
                              [round(max(0.0, baseline), 2)] * horizon, None, None)

    data = pd.DataFrame({"y": values})
    for lag in (1, 2, 3, 7):
        data[f"lag_{lag}"] = data["y"].shift(lag)
    data["weekday"] = data.index.dayofweek
    data = data.dropna()
    split = max(1, int(len(data) * 0.8))
    train, validation = data.iloc[:split], data.iloc[split:]
    features = ["lag_1", "lag_2", "lag_3", "lag_7", "weekday"]
    estimator = RandomForestRegressor(n_estimators=80, random_state=26251, min_samples_leaf=2)
    estimator.fit(train[features], train["y"])
    ml_mae = mean_absolute_error(validation["y"], estimator.predict(validation[features])) if len(validation) else None
    baseline_predictions = np.full(len(validation), baseline)
    baseline_mae = mean_absolute_error(validation["y"], baseline_predictions) if len(validation) else None
    use_ml = model == "ml" or (model == "auto" and ml_mae is not None and baseline_mae is not None and ml_mae <= baseline_mae)
    if not use_ml:
        predictions = [round(max(0.0, baseline), 2)] * horizon
        selected_model = "moving_average"
    else:
        history = list(values.astype(float))
        predictions = []
        for offset in range(horizon):
            features_row = [[history[-1], history[-2], history[-3], history[-7], (values.index[-1].dayofweek + offset + 1) % 7]]
            prediction = max(0.0, float(estimator.predict(features_row)[0]))
            predictions.append(round(prediction, 2))
            history.append(prediction)
        selected_model = "random_forest_lag"
    return ForecastResult(location_id, item_id, selected_model, horizon, predictions,
                          round(float(baseline_mae), 4) if baseline_mae is not None else None,
                          round(float(ml_mae), 4) if ml_mae is not None else None)
