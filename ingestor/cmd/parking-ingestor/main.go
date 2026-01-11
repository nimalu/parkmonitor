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
	log.Printf("Cities: %s", strings.Join(cfg.Cities, ", "))

	// Initialize database
	db, err := database.InitDB(cfg.DBPath)
	if err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Create API client and ingestor
	client := api.NewClient()
	ing := ingestor.New(db, client, cfg.Cities, cfg.Interval)
	ing.Start()
}
