package database

import (
	"database/sql"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// ParkingLot represents a parking lot/garage
type ParkingLot struct {
	ID        string
	City      string
	Name      string
	Address   sql.NullString
	LotType   sql.NullString
	Total     int
	Latitude  sql.NullFloat64
	Longitude sql.NullFloat64
	Region    sql.NullString
}

// ParkingReading represents a snapshot of parking availability
type ParkingReading struct {
	ID        int64
	LotID     string
	City      string
	Timestamp time.Time
	Free      int
	State     string
}

// InitDB initializes the SQLite database and creates tables if they don't exist
func InitDB(dbPath string) (*sql.DB, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	// Create parking_lots table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS parking_lots (
			id TEXT PRIMARY KEY,
			city TEXT NOT NULL,
			name TEXT NOT NULL,
			address TEXT,
			lot_type TEXT,
			total INTEGER NOT NULL,
			latitude REAL,
			longitude REAL,
			region TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		return nil, err
	}

	// Create parking_readings table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS parking_readings (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			lot_id TEXT NOT NULL,
			city TEXT NOT NULL,
			timestamp TIMESTAMP NOT NULL,
			free INTEGER NOT NULL,
			state TEXT NOT NULL,
			FOREIGN KEY (lot_id) REFERENCES parking_lots(id)
		)
	`)
	if err != nil {
		return nil, err
	}

	// Create index on timestamp for efficient queries
	_, err = db.Exec(`
		CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
		ON parking_readings(timestamp)
	`)
	if err != nil {
		return nil, err
	}

	// Create index on lot_id for efficient queries
	_, err = db.Exec(`
		CREATE INDEX IF NOT EXISTS idx_readings_lot_id 
		ON parking_readings(lot_id)
	`)
	if err != nil {
		return nil, err
	}

	return db, nil
}

// UpsertParkingLot inserts or updates a parking lot
func UpsertParkingLot(db *sql.DB, lot *ParkingLot) error {
	_, err := db.Exec(`
		INSERT INTO parking_lots (
			id, city, name, address, lot_type, total, 
			latitude, longitude, region, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
		ON CONFLICT(id) DO UPDATE SET
			name = excluded.name,
			address = excluded.address,
			lot_type = excluded.lot_type,
			total = excluded.total,
			latitude = excluded.latitude,
			longitude = excluded.longitude,
			region = excluded.region,
			updated_at = CURRENT_TIMESTAMP
	`, lot.ID, lot.City, lot.Name, lot.Address, lot.LotType,
		lot.Total, lot.Latitude, lot.Longitude, lot.Region)

	return err
}

// InsertReading inserts a new parking reading
func InsertReading(db *sql.DB, reading *ParkingReading) error {
	_, err := db.Exec(`
		INSERT INTO parking_readings (lot_id, city, timestamp, free, state)
		VALUES (?, ?, ?, ?, ?)
	`, reading.LotID, reading.City, reading.Timestamp, reading.Free, reading.State)

	return err
}

// UpsertParkingLotTx upserts a parking lot within a transaction
func UpsertParkingLotTx(tx *sql.Tx, lot *ParkingLot) error {
	_, err := tx.Exec(`
		INSERT INTO parking_lots (
			id, city, name, address, lot_type, total, 
			latitude, longitude, region, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
		ON CONFLICT(id) DO UPDATE SET
			name = excluded.name,
			address = excluded.address,
			lot_type = excluded.lot_type,
			total = excluded.total,
			latitude = excluded.latitude,
			longitude = excluded.longitude,
			region = excluded.region,
			updated_at = CURRENT_TIMESTAMP
	`, lot.ID, lot.City, lot.Name, lot.Address, lot.LotType,
		lot.Total, lot.Latitude, lot.Longitude, lot.Region)

	return err
}

// InsertReadingTx inserts a reading within a transaction
func InsertReadingTx(tx *sql.Tx, reading *ParkingReading) error {
	_, err := tx.Exec(`
		INSERT INTO parking_readings (lot_id, city, timestamp, free, state)
		VALUES (?, ?, ?, ?, ?)
	`, reading.LotID, reading.City, reading.Timestamp, reading.Free, reading.State)

	return err
}
