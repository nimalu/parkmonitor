package main

import (
	"log"
	"strings"

	"github.com/niklas/parkmonitor/ingestor/internal/api"
	"github.com/niklas/parkmonitor/ingestor/internal/config"
	"github.com/niklas/parkmonitor/ingestor/internal/database"
	"github.com/niklas/parkmonitor/ingestor/internal/ingestor"
)

func main() {
	cfg := config.ParseFlags()

	log.Printf("Starting parking ingestor...")
	log.Printf("Database: %s", cfg.DBPath)
	log.Printf("Polling interval: %v", cfg.Interval)

	// Create API client
	client := api.NewClient()

	// If no cities specified, fetch all available cities
	if len(cfg.Cities) == 0 {
		log.Printf("No cities specified, fetching all available cities...")
		citiesMap, err := client.GetCities()
		if err != nil {
			log.Fatalf("Failed to fetch cities: %v", err)
		}
		for cityID := range citiesMap {
			cfg.Cities = append(cfg.Cities, cityID)
		}
		log.Printf("Found %d cities", len(cfg.Cities))
	}

	log.Printf("Monitoring cities: %s", strings.Join(cfg.Cities, ", "))

	// Initialize database
	db, err := database.InitDB(cfg.DBPath)
	if err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Create ingestor and start
	ing := ingestor.New(db, client, cfg.Cities, cfg.Interval)
	ing.Start()
}
