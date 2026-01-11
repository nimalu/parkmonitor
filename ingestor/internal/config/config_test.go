package config

import (
	"testing"
	"time"
)

func TestParseCities(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected []string
	}{
		{
			name:     "Single city",
			input:    "Dresden",
			expected: []string{"Dresden"},
		},
		{
			name:     "Multiple cities",
			input:    "Dresden,Basel,Hamburg",
			expected: []string{"Dresden", "Basel", "Hamburg"},
		},
		{
			name:     "Empty string",
			input:    "",
			expected: []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parseCities(tt.input)

			if len(result) != len(tt.expected) {
				t.Errorf("parseCities(%q) returned %d cities, expected %d",
					tt.input, len(result), len(tt.expected))
				return
			}

			for i, city := range result {
				if city != tt.expected[i] {
					t.Errorf("parseCities(%q)[%d] = %q, expected %q",
						tt.input, i, city, tt.expected[i])
				}
			}
		})
	}
}

func TestConfig(t *testing.T) {
	config := &Config{
		DBPath:   "test.db",
		Interval: 5 * time.Minute,
		Cities:   []string{"Dresden", "Hamburg"},
	}

	if config.DBPath != "test.db" {
		t.Errorf("Expected DBPath to be 'test.db', got '%s'", config.DBPath)
	}

	if config.Interval != 5*time.Minute {
		t.Errorf("Expected Interval to be 5m, got %v", config.Interval)
	}

	if len(config.Cities) != 2 {
		t.Errorf("Expected 2 cities, got %d", len(config.Cities))
	}
}
