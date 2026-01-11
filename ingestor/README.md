# Parking Ingestor

A Go-based service that periodically fetches parking availability data from the [ParkenDD API](https://api.parkendd.de) and stores it in a SQLite database for historical tracking and analysis.

## Features

- 🚗 Fetches real-time parking availability data from multiple cities
- 💾 Stores data in SQLite for efficient querying and analysis
- ⏰ Configurable polling intervals
- 🏙️ Multi-city support
- 📊 Tracks historical parking availability over time

## Installation

### Prerequisites

**Native:**
- Go 1.22 or higher
- GCC (for SQLite CGO compilation)

**Docker:**
- Docker (for containerized deployment)

### Build

**Using Make:**
```bash
make build
```

**Using Go directly:**
```bash
go build -o build/parking-ingestor ./cmd/parking-ingestor
```

**Using Docker:**
```bash
docker build -t parking-ingestor .
```



## Usage

### Native Execution

Run with custom settings:

```bash
./build/parking-ingestor -db parking.db -cities Karlsruhe -interval 5m
```

### Docker Execution

**Run with custom settings:**
```bash
docker run -d \
  --name parking-ingestor \
  -v $(pwd)/data:/data \
  parking-ingestor \
  -db /data/parking.db \
  -cities Karlsruhe,Freiburg \
  -interval 10m
```

**View logs:**
```bash
docker logs -f parking-ingestor
```

### Command-line Options

- `-db <path>` - Path to SQLite database file (default: `parking.db`)
- `-interval <duration>` - Polling interval (default: `5m`)
  - Examples: `1m`, `30s`, `1h`, `15m`
- `-cities <list>` - Comma-separated list of cities to monitor (required)

### Examples

Monitor Dresden and Hamburg with 10-minute intervals:
```bash
./parking-ingestor -cities Dresden,Hamburg -interval 10m
```

Use a custom database location:
```bash
./parking-ingestor -db /var/data/parking.db
```

Monitor multiple cities with frequent updates:
```bash
./parking-ingestor -cities Dresden,Basel,Hamburg,Freiburg,Karlsruhe -interval 2m
```

## Database Schema

### Tables

#### `parking_lots`
Stores metadata about parking lots/garages:
- `id` (TEXT, PRIMARY KEY) - Unique identifier
- `city` (TEXT) - City name
- `name` (TEXT) - Parking lot name
- `address` (TEXT) - Street address
- `lot_type` (TEXT) - Type (e.g., "Tiefgarage", "Parkhaus", "Parkplatz")
- `total` (INTEGER) - Total parking spaces
- `latitude` (REAL) - Geographic latitude
- `longitude` (REAL) - Geographic longitude
- `region` (TEXT) - City region/district
- `created_at` (TIMESTAMP) - First seen timestamp
- `updated_at` (TIMESTAMP) - Last updated timestamp

#### `parking_readings`
Stores time-series data of parking availability:
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `lot_id` (TEXT, FOREIGN KEY) - Reference to parking_lots.id
- `city` (TEXT) - City name
- `timestamp` (TIMESTAMP) - When the reading was taken
- `free` (INTEGER) - Number of free spaces
- `state` (TEXT) - Status (e.g., "open", "closed", "nodata")

Indexes:
- `idx_readings_timestamp` - Efficient time-range queries
- `idx_readings_lot_id` - Efficient per-lot queries

## Querying the Data

### Using SQLite CLI

```bash
sqlite3 parking.db
```

**Example queries:**

Get current status of all parking lots:
```sql
SELECT 
    l.city, l.name, r.free, l.total, r.state, r.timestamp
FROM parking_lots l
JOIN parking_readings r ON l.id = r.lot_id
WHERE r.timestamp IN (
    SELECT MAX(timestamp) 
    FROM parking_readings 
    GROUP BY lot_id
)
ORDER BY l.city, l.name;
```

Get hourly average availability for a specific lot:
```sql
SELECT 
    strftime('%Y-%m-%d %H:00', timestamp) as hour,
    AVG(free) as avg_free,
    MIN(free) as min_free,
    MAX(free) as max_free
FROM parking_readings
WHERE lot_id = 'dresdenaltmarkt'
  AND timestamp >= datetime('now', '-7 days')
GROUP BY hour
ORDER BY hour;
```

Find the busiest parking lots (lowest average availability):
```sql
SELECT 
    l.city,
    l.name,
    l.total,
    AVG(r.free) as avg_free,
    (1.0 - AVG(r.free * 1.0 / l.total)) * 100 as avg_occupancy_pct
FROM parking_lots l
JOIN parking_readings r ON l.id = r.lot_id
WHERE r.timestamp >= datetime('now', '-1 day')
GROUP BY l.id
ORDER BY avg_occupancy_pct DESC
LIMIT 10;
```



### Running Tests

```bash
make test
# or
go test ./...
```

