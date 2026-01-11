package api

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	BaseURL = "https://api.parkendd.de"
)

// Client handles API requests to ParkenDD
type Client struct {
	httpClient *http.Client
}

// NewClient creates a new ParkenDD API client
func NewClient() *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// APIResponse represents the root API response
type APIResponse struct {
	Cities map[string]CityInfo `json:"cities"`
}

// CityInfo represents city metadata
type CityInfo struct {
	Name          string `json:"name"`
	ActiveSupport bool   `json:"active_support"`
	Coords        Coords `json:"coords"`
	Source        string `json:"source"`
	URL           string `json:"url"`
}

// Coords represents geographic coordinates
type Coords struct {
	Lat float64 `json:"lat"`
	Lng float64 `json:"lng"`
}

// CityParkingData represents parking data for a city
type CityParkingData struct {
	LastDownloaded string
	LastUpdated    string
	Lots           []ParkingLot
	LotReadings    []ParkingLotReading
}

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

// ParkingLotReading contains the free/state info for a reading
type ParkingLotReading struct {
	LotID string
	Free  int
	State string
}

// parkingLotAPI represents API parking lot data
type parkingLotAPI struct {
	ID       string  `json:"id"`
	Name     string  `json:"name"`
	Address  string  `json:"address"`
	Coords   *Coords `json:"coords"`
	LotType  string  `json:"lot_type"`
	Free     int     `json:"free"`
	Total    int     `json:"total"`
	State    string  `json:"state"`
	Region   string  `json:"region"`
	Forecast bool    `json:"forecast"`
}

// GetCities fetches the list of available cities
func (c *Client) GetCities() (map[string]CityInfo, error) {
	resp, err := c.httpClient.Get(BaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch cities: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API returned status %d: %s", resp.StatusCode, string(body))
	}

	var apiResp APIResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return apiResp.Cities, nil
}

// GetCityParkingData fetches parking data for a specific city
func (c *Client) GetCityParkingData(city string) (*CityParkingData, error) {
	url := fmt.Sprintf("%s/%s", BaseURL, city)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch parking data for %s: %w", city, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API returned status %d for %s: %s", resp.StatusCode, city, string(body))
	}

	var data struct {
		LastDownloaded string          `json:"last_downloaded"`
		LastUpdated    string          `json:"last_updated"`
		Lots           []parkingLotAPI `json:"lots"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, fmt.Errorf("failed to decode response for %s: %w", city, err)
	}

	result := &CityParkingData{
		LastDownloaded: data.LastDownloaded,
		LastUpdated:    data.LastUpdated,
		Lots:           make([]ParkingLot, len(data.Lots)),
		LotReadings:    make([]ParkingLotReading, len(data.Lots)),
	}

	// Convert API lots to internal format
	for i, lot := range data.Lots {
		dbLot := ParkingLot{
			ID:    lot.ID,
			City:  city,
			Name:  lot.Name,
			Total: lot.Total,
		}

		if lot.Address != "" {
			dbLot.Address.String = lot.Address
			dbLot.Address.Valid = true
		}

		if lot.LotType != "" {
			dbLot.LotType.String = lot.LotType
			dbLot.LotType.Valid = true
		}

		if lot.Coords != nil {
			dbLot.Latitude.Float64 = lot.Coords.Lat
			dbLot.Latitude.Valid = true
			dbLot.Longitude.Float64 = lot.Coords.Lng
			dbLot.Longitude.Valid = true
		}

		if lot.Region != "" {
			dbLot.Region.String = lot.Region
			dbLot.Region.Valid = true
		}

		result.Lots[i] = dbLot
		result.LotReadings[i] = ParkingLotReading{
			LotID: lot.ID,
			Free:  lot.Free,
			State: lot.State,
		}
	}

	return result, nil
}
