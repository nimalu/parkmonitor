"""Data loading utilities for parking forecasting."""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional


class ParkingDataLoader:
    """Load and preprocess parking data from SQLite database."""

    def __init__(self, db_path):
        """Initialize data loader with database path."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

    def load_parking_lots(self) -> pd.DataFrame:
        """Load parking lot metadata."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM parking_lots", conn)
        conn.close()
        return df

    def load_readings(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        lot_ids: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Load parking readings with optional filtering.

        Args:
            start_date: Filter readings after this date (ISO format)
            end_date: Filter readings before this date (ISO format)
            lot_ids: Filter readings for specific lot IDs

        Returns:
            DataFrame with parking readings
        """
        query = "SELECT * FROM parking_readings WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if lot_ids:
            placeholders = ",".join("?" * len(lot_ids))
            query += f" AND lot_id IN ({placeholders})"
            params.extend(lot_ids)

        query += " ORDER BY timestamp"

        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df

    def load_combined_data(self) -> pd.DataFrame:
        """
        Load readings merged with parking lot metadata.

        Returns:
            DataFrame with readings and lot information
        """
        lots = self.load_parking_lots()
        readings = self.load_readings()

        merged = readings.merge(
            lots[["id", "name", "total", "lot_type", "latitude", "longitude"]],
            left_on="lot_id",
            right_on="id",
            suffixes=("", "_lot"),
        )

        # Calculate derived features
        merged["occupied"] = merged["total"] - merged["free"]
        merged["occupancy_rate"] = (merged["occupied"] / merged["total"]) * 100

        return merged

    def get_time_series(self, lot_id: str) -> pd.DataFrame:
        """
        Get time series data for a specific parking lot.

        Args:
            lot_id: Parking lot identifier

        Returns:
            DataFrame with time series indexed by timestamp
        """
        df = self.load_readings(lot_ids=[lot_id])
        df = df.set_index("timestamp").sort_index()
        return df

