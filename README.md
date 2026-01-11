# ParkMonitor

Real-time parking monitoring system with AI-powered forecasting.

## Components

- **ingestor**: Go service that polls parking data APIs and stores in SQLite
- **forecast**: Python FastAPI service for ML forecasting
- **frontend**: Nuxt.js dashboard with real-time data and predictions

## Running

### Production (without local Caddy)
When deploying, your external Caddy will handle routing:

```bash
docker-compose up -d
```

- Frontend: http://localhost:3000
- API: http://localhost:8000

### Development (with local Caddy)
To simulate production with local Caddy proxy:

```bash
docker-compose --profile dev up -d
```

- App: http://localhost:8080 (Caddy proxies both frontend and API)
- API via Caddy: http://localhost:8080/api/*

### Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

- `API_BASE_URL=/api` - Use when behind Caddy (production)
- `API_BASE_URL=http://localhost:8000` - Direct backend access

## Production Caddy Configuration

Add this to your production Caddyfile:

```caddyfile
your-domain.com {
    # API endpoints
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy localhost:8000
    }

    # Frontend
    handle {
        reverse_proxy localhost:3000
    }
}
```

## Development

### Forecast Service
```bash
cd forecast
pixi install
pixi run train  # Train model first
pixi run serve
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
