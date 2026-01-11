"""Machine learning models for parking availability forecasting."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import joblib
from pathlib import Path


class ParkingForecaster:
    """Forecasting model for parking availability."""

    def __init__(self, model_type: str = "xgboost"):
        """
        Initialize forecaster.

        Args:
            model_type: Type of model ('random_forest', 'xgboost', 'lightgbm')
        """
        self.model_type = model_type
        self.model = None
        self.feature_columns = None
        self.target_column = None

        self._init_model()

    def _init_model(self):
        """Initialize the ML model based on type."""
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif self.model_type == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
            )
        elif self.model_type == "lightgbm":
            self.model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = "occupancy_rate",
        exclude_cols: List[str] = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for training.

        Args:
            df: DataFrame with features and target
            target_col: Target column name
            exclude_cols: Columns to exclude from features

        Returns:
            X (features) and y (target)
        """
        if exclude_cols is None:
            exclude_cols = [
                "id",
                "lot_id",
                "city",
                "timestamp",
                "name",
                "address",
                "region",
                "created_at",
                "updated_at",
                "state",
                "free",
                "occupied",
                "lot_type",
                "id_lot",
                "latitude",
                "longitude",
                target_col,
            ]

        # Select feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Remove rows with missing target
        df_clean = df[df[target_col].notna()].copy()

        # Fill missing feature values
        X = df_clean[feature_cols].fillna(0)
        y = df_clean[target_col]
        
        # Ensure all columns are numeric
        for col in X.columns:
            if X[col].dtype == 'object':
                # Try to convert to numeric, drop if it fails
                try:
                    X[col] = pd.to_numeric(X[col])
                except (ValueError, TypeError):
                    X = X.drop(columns=[col])

        self.feature_columns = feature_cols
        self.target_column = target_col

        return X, y

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None,
    ) -> Dict[str, float]:
        """
        Train the forecasting model.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)

        Returns:
            Dictionary of training metrics
        """
        print(f"Training {self.model_type} model...")

        if X_val is not None and y_val is not None:
            if self.model_type in ["xgboost", "lightgbm"]:
                self.model.fit(
                    X_train, y_train, eval_set=[(X_val, y_val)], verbose=False
                )
            else:
                self.model.fit(X_train, y_train)
        else:
            self.model.fit(X_train, y_train)

        # Calculate training metrics
        y_pred_train = self.model.predict(X_train)
        metrics = {
            "train_mae": mean_absolute_error(y_train, y_pred_train),
            "train_rmse": np.sqrt(mean_squared_error(y_train, y_pred_train)),
            "train_r2": r2_score(y_train, y_pred_train),
        }

        if X_val is not None and y_val is not None:
            y_pred_val = self.model.predict(X_val)
            metrics.update(
                {
                    "val_mae": mean_absolute_error(y_val, y_pred_val),
                    "val_rmse": np.sqrt(mean_squared_error(y_val, y_pred_val)),
                    "val_r2": r2_score(y_val, y_pred_val),
                }
            )

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features for prediction

        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        return self.model.predict(X)

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        Evaluate model on test set.

        Args:
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary of evaluation metrics
        """
        y_pred = self.predict(X_test)

        return {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
            "mape": np.mean(np.abs((y_test - y_pred) / y_test)) * 100,
        }

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance from trained model.

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        else:
            raise ValueError(
                f"Model {self.model_type} does not support feature importance"
            )

        feature_imp = (
            pd.DataFrame({"feature": self.feature_columns, "importance": importances})
            .sort_values("importance", ascending=False)
            .head(top_n)
        )

        return feature_imp

    def save(self, filepath: str):
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("Model not trained yet")

        model_data = {
            "model": self.model,
            "model_type": self.model_type,
            "feature_columns": self.feature_columns,
            "target_column": self.target_column,
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")

    def load(self, filepath: str):
        """Load trained model from disk."""
        model_data = joblib.load(filepath)
        self.model = model_data["model"]
        self.model_type = model_data["model_type"]
        self.feature_columns = model_data["feature_columns"]
        self.target_column = model_data["target_column"]
        print(f"Model loaded from {filepath}")
