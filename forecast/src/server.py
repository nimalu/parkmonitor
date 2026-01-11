"""FastAPI server for parking occupancy forecasting."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import ParkingDataLoader
from features import FeatureEngineer
from models import ParkingForecaster


# Pydantic models
class ParkingLot(BaseModel):
    """Parking lot information."""
    id: str
    name: str
    total: int
    lot_type: str
    latitude: float
    longitude: float


class CurrentStatus(BaseModel):
    """Current parking status."""
    lot_id: str
    name: str
    total: int
    free: int
    occupied: int
    occupancy_rate: float
    timestamp: str


class Forecast(BaseModel):
    """Forecast for parking occupancy."""
    lot_id: str
    name: str
    predicted_occupancy_rate: float
    confidence_low: Optional[float] = None
    confidence_high: Optional[float] = None
    forecast_time: str


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    model_loaded: bool
    model_type: Optional[str] = None
    total_lots: int


# Initialize FastAPI app
app = FastAPI(
    title="Parking Forecast API",
    description="API for forecasting parking lot occupancy",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

# Global variables for model and data
forecaster: Optional[ParkingForecaster] = None
data_loader: Optional[ParkingDataLoader] = None
model_path: Optional[Path] = None
model_last_modified: Optional[float] = None


def load_model():
    """Load the trained forecasting model."""
    global forecaster, model_path, model_last_modified
    
    model_path = Path(__file__).parent.parent / "models" / "parking_forecaster_xgboost.pkl"
    
    if not model_path.exists():
        raise RuntimeError(f"Model not found at {model_path}. Please train a model first.")
    
    forecaster = ParkingForecaster()
    forecaster.load(str(model_path))
    model_last_modified = model_path.stat().st_mtime
    print(f"Loaded model from {model_path} (modified: {datetime.fromtimestamp(model_last_modified)})")


def check_and_reload_model():
    """Check if model file has changed and reload if necessary."""
    global forecaster, model_path, model_last_modified
    
    if model_path is None or not model_path.exists():
        return
    
    current_mtime = model_path.stat().st_mtime
    
    if model_last_modified is None or current_mtime > model_last_modified:
        print("Model file changed, reloading...")
        try:
            load_model()
            print("Model reloaded successfully")
        except Exception as e:
            print(f"Failed to reload model: {e}")


def initialize_data_loader():
    """Initialize the data loader."""
    global data_loader
    
    db_path = Path(__file__).parent.parent.parent / "data" / "parking.db"
    
    if not db_path.exists():
        raise RuntimeError(f"Database not found at {db_path}")
    
    data_loader = ParkingDataLoader(db_path)
    print(f"Initialized data loader with database at {db_path}")


@app.on_event("startup")
async def startup_event():
    """Load model and initialize data on startup."""
    initialize_data_loader()
    load_model()
    print("API server started successfully")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Parking Forecast API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "lots": "/lots",
            "current": "/current",
            "forecast": "/forecast/{lot_id}",
            "forecast_all": "/forecast",
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if data_loader is None:
        raise HTTPException(status_code=503, detail="Data loader not initialized")
    
    lots = data_loader.load_parking_lots()
    
    return HealthResponse(
        status="healthy",
        model_loaded=forecaster is not None,
        model_type=forecaster.model_type if forecaster else None,
        total_lots=len(lots)
    )


@app.get("/lots", response_model=List[ParkingLot])
async def get_parking_lots():
    """Get all parking lots."""
    if data_loader is None:
        raise HTTPException(status_code=503, detail="Data loader not initialized")
    
    lots_df = data_loader.load_parking_lots()
    
    return [
        ParkingLot(
            id=row['id'],
            name=row['name'],
            total=int(row['total']),
            lot_type=row['lot_type'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude'])
        )
        for _, row in lots_df.iterrows()
    ]


@app.get("/current", response_model=List[CurrentStatus])
async def get_current_status(lot_id: Optional[str] = Query(None, description="Filter by lot ID")):
    """Get current parking status for all lots or a specific lot."""
    if data_loader is None:
        raise HTTPException(status_code=503, detail="Data loader not initialized")
    
    try:
        # Get the latest reading for each lot
        if lot_id:
            df = data_loader.load_readings(lot_ids=[lot_id])
        else:
            df = data_loader.load_readings()
        
        if df.empty:
            return []
        
        # Get the most recent reading for each lot
        df = df.sort_values('timestamp').groupby('lot_id').tail(1)
        
        # Merge with lot information
        lots_df = data_loader.load_parking_lots()
        merged = df.merge(
            lots_df[['id', 'name', 'total']],
            left_on='lot_id',
            right_on='id'
        )
        
        merged['occupied'] = merged['total'] - merged['free']
        merged['occupancy_rate'] = (merged['occupied'] / merged['total']) * 100
        
        return [
            CurrentStatus(
                lot_id=row['lot_id'],
                name=row['name'],
                total=int(row['total']),
                free=int(row['free']),
                occupied=int(row['occupied']),
                occupancy_rate=float(row['occupancy_rate']),
                timestamp=row['timestamp'].isoformat()
            )
            for _, row in merged.iterrows()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current status: {str(e)}")


@app.get("/forecast/{lot_id}", response_model=Forecast)
async def get_forecast(lot_id: str):
    """Get occupancy forecast for a specific parking lot."""
    check_and_reload_model()
    
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if data_loader is None:
        raise HTTPException(status_code=503, detail="Data loader not initialized")
    
    try:
        # Load recent data for the lot
        df = data_loader.load_readings(lot_ids=[lot_id])
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for lot {lot_id}")
        
        # Get lot info
        lots_df = data_loader.load_parking_lots()
        lot_info = lots_df[lots_df['id'] == lot_id]
        
        if lot_info.empty:
            raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found")
        
        lot_name = lot_info.iloc[0]['name']
        
        # Merge with lot information
        df = df.merge(
            lots_df[['id', 'name', 'total', 'lot_type', 'latitude', 'longitude']],
            left_on='lot_id',
            right_on='id'
        )
        
        df['occupied'] = df['total'] - df['free']
        df['occupancy_rate'] = (df['occupied'] / df['total']) * 100
        
        # Engineer features
        engineer = FeatureEngineer()
        df = engineer.add_temporal_features(df)
        df = engineer.add_lag_features(df, 'occupancy_rate', lags=[1, 2, 3], group_col='lot_id')
        df = engineer.add_rolling_features(df, 'occupancy_rate', windows=[3], group_col='lot_id')
        
        # Get the most recent complete row
        df = df.dropna()
        
        if df.empty:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient historical data for lot {lot_id}. Need at least 3 recent readings."
            )
        
        latest = df.iloc[-1:]
        
        # Prepare features
        X = latest[forecaster.feature_columns].fillna(0)
        
        # Make prediction
        prediction = forecaster.predict(X)[0]
        
        # Simple confidence interval (±10%)
        confidence_low = max(0, prediction - 10)
        confidence_high = min(100, prediction + 10)
        
        return Forecast(
            lot_id=lot_id,
            name=lot_name,
            predicted_occupancy_rate=float(prediction),
            confidence_low=float(confidence_low),
            confidence_high=float(confidence_high),
            forecast_time=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


@app.get("/forecast", response_model=List[Forecast])
async def get_all_forecasts():
    """Get occupancy forecasts for all parking lots."""
    # Check if model needs reloading
    check_and_reload_model()
    
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if data_loader is None:
        raise HTTPException(status_code=503, detail="Data loader not initialized")
    
    try:
        # Load all data
        df = data_loader.load_combined_data()
        
        if df.empty:
            return []
        
        # Engineer features
        engineer = FeatureEngineer()
        df = engineer.add_temporal_features(df)
        df = engineer.add_lag_features(df, 'occupancy_rate', lags=[1, 2, 3], group_col='lot_id')
        df = engineer.add_rolling_features(df, 'occupancy_rate', windows=[3], group_col='lot_id')
        
        # Drop rows with NaN
        df = df.dropna()
        
        if df.empty:
            return []
        
        # Get the most recent reading for each lot
        latest_per_lot = df.sort_values('timestamp').groupby('lot_id').tail(1)
        
        # Prepare features
        X = latest_per_lot[forecaster.feature_columns].fillna(0)
        
        # Make predictions
        predictions = forecaster.predict(X)
        
        # Build response
        forecasts = []
        for idx, (_, row) in enumerate(latest_per_lot.iterrows()):
            prediction = predictions[idx]
            forecasts.append(
                Forecast(
                    lot_id=row['lot_id'],
                    name=row['name'],
                    predicted_occupancy_rate=float(prediction),
                    confidence_low=float(max(0, prediction - 10)),
                    confidence_high=float(min(100, prediction + 10)),
                    forecast_time=datetime.now().isoformat()
                )
            )
        
        return forecasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecasts: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
