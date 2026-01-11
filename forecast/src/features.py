"""Feature engineering for parking forecasting models."""

import pandas as pd
import numpy as np
from typing import List, Optional


class FeatureEngineer:
    """Create features for parking availability forecasting."""

    @staticmethod
    def add_temporal_features(
        df: pd.DataFrame, timestamp_col: str = "timestamp"
    ) -> pd.DataFrame:
        """
        Add time-based features from timestamp.

        Args:
            df: DataFrame with timestamp column
            timestamp_col: Name of timestamp column

        Returns:
            DataFrame with additional temporal features
        """
        df = df.copy()

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        # Extract temporal components
        df["hour"] = df[timestamp_col].dt.hour
        df["day_of_week"] = df[timestamp_col].dt.dayofweek
        df["day_of_month"] = df[timestamp_col].dt.day
        df["month"] = df[timestamp_col].dt.month
        df["year"] = df[timestamp_col].dt.year
        df["week_of_year"] = df[timestamp_col].dt.isocalendar().week

        # Cyclical encoding for periodic features
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

        # Boolean features
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["is_business_hours"] = ((df["hour"] >= 8) & (df["hour"] <= 18)).astype(int)
        df["is_rush_hour"] = (
            ((df["hour"] >= 7) & (df["hour"] <= 9))
            | ((df["hour"] >= 16) & (df["hour"] <= 19))
        ).astype(int)

        return df

    @staticmethod
    def add_lag_features(
        df: pd.DataFrame,
        target_col: str,
        lags: List[int] = [1, 2, 3, 6, 12, 24],
        group_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Add lagged values of target variable.

        Args:
            df: DataFrame with target column
            target_col: Column to create lags for
            lags: List of lag periods
            group_col: Optional column to group by (e.g., lot_id)

        Returns:
            DataFrame with lag features
        """
        df = df.copy()

        for lag in lags:
            col_name = f"{target_col}_lag_{lag}"
            if group_col:
                df[col_name] = df.groupby(group_col)[target_col].shift(lag)
            else:
                df[col_name] = df[target_col].shift(lag)

        return df

    @staticmethod
    def add_rolling_features(
        df: pd.DataFrame,
        target_col: str,
        windows: List[int] = [3, 6, 12, 24],
        group_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Add rolling statistics of target variable.

        Args:
            df: DataFrame with target column
            target_col: Column to calculate rolling stats for
            windows: List of window sizes
            group_col: Optional column to group by

        Returns:
            DataFrame with rolling features
        """
        df = df.copy()

        for window in windows:
            if group_col:
                grouped = df.groupby(group_col)[target_col]
                df[f"{target_col}_rolling_mean_{window}"] = grouped.transform(
                    lambda x: x.rolling(window, min_periods=1).mean()
                )
                df[f"{target_col}_rolling_std_{window}"] = grouped.transform(
                    lambda x: x.rolling(window, min_periods=1).std()
                )
                df[f"{target_col}_rolling_max_{window}"] = grouped.transform(
                    lambda x: x.rolling(window, min_periods=1).max()
                )
                df[f"{target_col}_rolling_min_{window}"] = grouped.transform(
                    lambda x: x.rolling(window, min_periods=1).min()
                )
            else:
                df[f"{target_col}_rolling_mean_{window}"] = (
                    df[target_col].rolling(window, min_periods=1).mean()
                )
                df[f"{target_col}_rolling_std_{window}"] = (
                    df[target_col].rolling(window, min_periods=1).std()
                )
                df[f"{target_col}_rolling_max_{window}"] = (
                    df[target_col].rolling(window, min_periods=1).max()
                )
                df[f"{target_col}_rolling_min_{window}"] = (
                    df[target_col].rolling(window, min_periods=1).min()
                )

        return df

    @staticmethod
    def create_all_features(
        df: pd.DataFrame,
        target_col: str = "occupancy_rate",
        timestamp_col: str = "timestamp",
        group_col: Optional[str] = "lot_id",
    ) -> pd.DataFrame:
        """
        Create all features for forecasting.

        Args:
            df: Input DataFrame
            target_col: Target variable column
            timestamp_col: Timestamp column
            group_col: Grouping column

        Returns:
            DataFrame with all features
        """
        df = df.copy()

        # Temporal features
        df = FeatureEngineer.add_temporal_features(df, timestamp_col)

        # Lag features
        df = FeatureEngineer.add_lag_features(df, target_col, group_col=group_col)

        # Rolling features
        df = FeatureEngineer.add_rolling_features(df, target_col, group_col=group_col)

        return df


