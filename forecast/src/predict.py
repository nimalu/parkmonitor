"""Prediction script for parking forecasting."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import ParkingDataLoader
from features import FeatureEngineer
from models import ParkingForecaster


def make_predictions(model_path: str = None, lot_id: str = None):
    """
    Make predictions using a trained model.

    Args:
        model_path: Path to saved model file
        lot_id: Specific parking lot ID to predict (if None, predicts all)
    """
    print("=== Parking Availability Prediction ===\n")

    # Determine model path
    if model_path is None:
        model_path = (
            Path(__file__).parent.parent / "models" / "parking_forecaster_xgboost.pkl"
        )

    if not Path(model_path).exists():
        print(f"Error: Model not found at {model_path}")
        print("Please train a model first using: pixi run train")
        return

    # Load model
    print(f"1. Loading model from {model_path}...")
    forecaster = ParkingForecaster()
    forecaster.load(str(model_path))

    # Load latest data
    print("\n2. Loading latest parking data...")
    loader = ParkingDataLoader()

    if lot_id:
        df = loader.load_readings(lot_ids=[lot_id])
        df = df.merge(
            loader.load_parking_lots()[["id", "name", "total"]],
            left_on="lot_id",
            right_on="id",
        )
        df["occupied"] = df["total"] - df["free"]
        df["occupancy_rate"] = (df["occupied"] / df["total"]) * 100
    else:
        df = loader.load_combined_data()

    print(f"   Loaded {len(df)} readings")

    # Engineer features
    print("\n3. Engineering features...")
    engineer = FeatureEngineer()
    df = engineer.create_all_features(df)
    df = df.dropna()

    # Prepare features
    print("\n4. Preparing features for prediction...")
    X = df[forecaster.feature_columns].fillna(0)

    # Make predictions
    print("\n5. Making predictions...")
    predictions = forecaster.predict(X)

    # Add predictions to dataframe
    df["predicted_occupancy"] = predictions
    df["actual_occupancy"] = df[forecaster.target_column]
    df["prediction_error"] = df["actual_occupancy"] - df["predicted_occupancy"]

    # Display results
    print("\n=== Prediction Results ===\n")

    if lot_id:
        # Show detailed results for specific lot
        lot_name = df["name"].iloc[0]
        print(f"Parking Lot: {lot_name} (ID: {lot_id})")
        print(f"Total Capacity: {df['total'].iloc[0]} spaces")
        print("\nLatest Predictions:")

        recent = df[
            ["timestamp", "actual_occupancy", "predicted_occupancy", "prediction_error"]
        ].tail(10)
        print(recent.to_string(index=False))

        print(f"\nMean Absolute Error: {df['prediction_error'].abs().mean():.2f}%")
    else:
        # Show summary for all lots
        print("Summary by Parking Lot:")
        summary = (
            df.groupby("name")
            .agg(
                {
                    "actual_occupancy": "mean",
                    "predicted_occupancy": "mean",
                    "prediction_error": lambda x: x.abs().mean(),
                }
            )
            .round(2)
        )
        summary.columns = ["Avg Actual (%)", "Avg Predicted (%)", "MAE (%)"]
        summary = summary.sort_values("MAE (%)", ascending=False).head(10)
        print(summary)

        print(f"\nOverall MAE: {df['prediction_error'].abs().mean():.2f}%")

    print("\n=== Prediction Complete ===\n")

    return df


def predict_future(model_path: str = None, lot_id: str = None, hours_ahead: int = 24):
    """
    Predict future parking availability (requires time series extension).

    Args:
        model_path: Path to saved model
        lot_id: Parking lot ID
        hours_ahead: Hours to predict into the future
    """
    print(f"Future prediction for {hours_ahead} hours ahead is not yet implemented.")
    print("This requires additional time series forecasting logic.")
    print("Current implementation supports predictions on existing data only.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Make parking availability predictions"
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Path to trained model file"
    )
    parser.add_argument(
        "--lot-id", type=str, default=None, help="Specific parking lot ID to predict"
    )
    parser.add_argument(
        "--future",
        action="store_true",
        help="Predict future availability (not yet implemented)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours ahead to predict (for future predictions)",
    )

    args = parser.parse_args()

    if args.future:
        predict_future(
            model_path=args.model, lot_id=args.lot_id, hours_ahead=args.hours
        )
    else:
        make_predictions(model_path=args.model, lot_id=args.lot_id)
