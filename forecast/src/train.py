"""Training script for parking forecasting models."""

import sys
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import ParkingDataLoader
from features import FeatureEngineer
from models import ParkingForecaster


def train_model(model_type: str = "xgboost", save_model: bool = True):
    """
    Train a parking forecasting model.

    Args:
        model_type: Type of model to train ('xgboost', 'lightgbm', 'random_forest')
        save_model: Whether to save the trained model
    """
    print(f"=== Training {model_type.upper()} Model ===\n")

    # Load data
    print("1. Loading data...")
    db_path = Path(__file__).parent.parent.parent / "data" / "parking.db"
    loader = ParkingDataLoader(db_path)
    df = loader.load_combined_data()
    print(f"   Loaded {len(df)} readings from {df['lot_id'].nunique()} parking lots")

    # Engineer features
    print("\n2. Engineering features...")
    engineer = FeatureEngineer()
    print(f"   Before feature engineering: {len(df)} rows")
    # Use smaller lags for limited data
    df = engineer.add_temporal_features(df)
    print(f"   After temporal features: {len(df)} rows, {df.shape[1]} columns")
    
    # Only use small lags that won't eliminate all data
    df = engineer.add_lag_features(df, 'occupancy_rate', lags=[1, 2, 3], group_col='lot_id')
    print(f"   After lag features: {len(df)} rows, {df.shape[1]} columns")
    
    df = engineer.add_rolling_features(df, 'occupancy_rate', windows=[3], group_col='lot_id')
    print(f"   After rolling features: {len(df)} rows, {df.shape[1]} columns")
    print(f"   NaN counts: {df.isna().sum().sum()} total NaN values")

    # Drop rows with NaN values from lag/rolling features
    df = df.dropna()
    print(f"   After dropping NaN: {len(df)} rows")
    
    if len(df) == 0:
        print("\n   ERROR: No data remaining after dropping NaN values!")
        print("   This suggests the database has insufficient data for time series features.")
        print("   Try collecting more data or reducing lag periods.")
        return None, None

    # Prepare data
    print("\n3. Preparing data for training...")
    forecaster = ParkingForecaster(model_type=model_type)
    X, y = forecaster.prepare_data(df)
    print(f"   Features shape: {X.shape}")
    print(f"   Target shape: {y.shape}")

    # Split data (80/20 train/test split)
    print("\n4. Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False,  # No shuffle for time series
    )
    print(f"   Train size: {len(X_train)} samples")
    print(f"   Test size: {len(X_test)} samples")

    # Train model
    print("\n5. Training model...")
    train_metrics = forecaster.train(X_train, y_train, X_test, y_test)

    print("\n   Training Metrics:")
    for metric, value in train_metrics.items():
        print(f"     {metric}: {value:.4f}")

    # Evaluate on test set
    print("\n6. Evaluating on test set...")
    eval_metrics = forecaster.evaluate(X_test, y_test)

    print("\n   Evaluation Metrics:")
    print(f"     MAE:  {eval_metrics['mae']:.4f}% occupancy")
    print(f"     RMSE: {eval_metrics['rmse']:.4f}% occupancy")
    print(f"     R²:   {eval_metrics['r2']:.4f}")
    print(f"     MAPE: {eval_metrics['mape']:.2f}%")

    # Feature importance
    print("\n7. Top 10 most important features:")
    feature_imp = forecaster.get_feature_importance(top_n=10)
    for idx, row in feature_imp.iterrows():
        print(f"     {row['feature']}: {row['importance']:.4f}")

    # Save model
    if save_model:
        print("\n8. Saving model...")
        model_path = (
            Path(__file__).parent.parent
            / "models"
            / f"parking_forecaster_{model_type}.pkl"
        )
        forecaster.save(str(model_path))

    print("\n=== Training Complete ===\n")

    return forecaster, eval_metrics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train parking forecasting model")
    parser.add_argument(
        "--model",
        type=str,
        default="xgboost",
        choices=["xgboost", "lightgbm", "random_forest"],
        help="Model type to train",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Do not save the trained model"
    )

    args = parser.parse_args()

    train_model(model_type=args.model, save_model=not args.no_save)
