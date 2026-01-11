package config

import (
	"flag"
	"time"
)

// Config holds the application configuration from CLI flags
type Config struct {
	DBPath   string
	Interval time.Duration
	Cities   []string
}

// ParseFlags parses command-line flags and returns the configuration
func ParseFlags() *Config {
	dbPath := flag.String("db", "parking.db", "Path to SQLite database file")
	interval := flag.Duration("interval", 5*time.Minute, "Polling interval")
	cities := flag.String("cities", "", "Comma-separated list of cities to monitor")
	flag.Parse()

	return &Config{
		DBPath:   *dbPath,
		Interval: *interval,
		Cities:   parseCities(*cities),
	}
}

// parseCities splits a comma-separated string into a slice of city names
func parseCities(cities string) []string {
	result := []string{}
	current := ""
	for _, c := range cities {
		if c == ',' {
			if current != "" {
				result = append(result, current)
				current = ""
			}
		} else {
			current += string(c)
		}
	}
	if current != "" {
		result = append(result, current)
	}
	return result
}
