package ingestor

import (
	"context"
	"database/sql"
	"log"
	"time"

	"github.com/niklas/smart-city/ingestor/internal/api"
	"github.com/niklas/smart-city/ingestor/internal/database"
)

// Ingestor handles the periodic polling and data storage
type Ingestor struct {
	db       *sql.DB
	client   *api.Client
	cities   []string
	interval time.Duration
}

// New creates a new ingestor instance
func New(db *sql.DB, client *api.Client, cities []string, interval time.Duration) *Ingestor {
	return &Ingestor{
		db:       db,
		client:   client,
		cities:   cities,
		interval: interval,
	}
}

// Start begins the periodic polling process
func (i *Ingestor) Start() {
	// Run immediately on startup
	i.poll()

	// Then run periodically
	ticker := time.NewTicker(i.interval)
	defer ticker.Stop()

	for range ticker.C {
		i.poll()
	}
}

// poll fetches data for all configured cities and stores it
func (i *Ingestor) poll() {
	log.Printf("Starting poll cycle at %s", time.Now().Format(time.RFC3339))

	for _, city := range i.cities {
		if err := i.pollCity(city); err != nil {
			log.Printf("Error polling city %s: %v", city, err)
			continue
		}
		log.Printf("Successfully polled city: %s", city)
	}
}

// pollCity fetches and stores data for a single city
func (i *Ingestor) pollCity(city string) error {
	// Fetch parking data
	data, err := i.client.GetCityParkingData(city)
	if err != nil {
		return err
	}

	// Start transaction
	ctx := context.Background()
	tx, err := i.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	timestamp := time.Now()

	// Store/update parking lots and insert readings
	for idx, lot := range data.Lots {
		// Convert api.ParkingLot to database.ParkingLot
		dbLot := &database.ParkingLot{
			ID:        lot.ID,
			City:      lot.City,
			Name:      lot.Name,
			Address:   lot.Address,
			LotType:   lot.LotType,
			Total:     lot.Total,
			Latitude:  lot.Latitude,
			Longitude: lot.Longitude,
			Region:    lot.Region,
		}

		// Upsert parking lot
		if err := database.UpsertParkingLotTx(tx, dbLot); err != nil {
			return err
		}

		// Insert reading
		reading := &database.ParkingReading{
			LotID:     data.LotReadings[idx].LotID,
			City:      city,
			Timestamp: timestamp,
			Free:      data.LotReadings[idx].Free,
			State:     data.LotReadings[idx].State,
		}
		if err := database.InsertReadingTx(tx, reading); err != nil {
			return err
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return err
	}

	log.Printf("Stored %d parking lots for %s", len(data.Lots), city)
	return nil
}
