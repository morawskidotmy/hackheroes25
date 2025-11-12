package main

import (
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/go-resty/resty/v2"
)

// ============================================================================
// MEVO Provider (Poland - GBFS)
// ============================================================================

type MEVOProvider struct {
	baseURL string
	client  *resty.Client
}

type MEVOStationInfo struct {
	Data struct {
		Stations []struct {
			StationID string  `json:"station_id"`
			Name      string  `json:"name"`
			Lat       float64 `json:"lat"`
			Lon       float64 `json:"lon"`
			Address   string  `json:"address"`
		} `json:"stations"`
	} `json:"data"`
}

type MEVOStationStatus struct {
	Data struct {
		Stations []struct {
			StationID         string `json:"station_id"`
			NumBikesAvailable int    `json:"num_bikes_available"`
			NumDocksAvailable int    `json:"num_docks_available"`
			IsRenting         int    `json:"is_renting"`
		} `json:"stations"`
	} `json:"data"`
}

func NewMEVOProvider() *MEVOProvider {
	return &MEVOProvider{
		baseURL: "https://gbfs.urbansharing.com/rowermevo.pl",
		client:  resty.New().SetTimeout(5 * time.Second),
	}
}

func (m *MEVOProvider) Name() string {
	return "MEVO"
}

func (m *MEVOProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	stationInfo, err := m.getStationInfo()
	if err != nil {
		return nil, err
	}

	stationStatus, err := m.getStationStatus()
	if err != nil {
		return nil, err
	}

	statusMap := make(map[string]struct {
		bikes int
		docks int
		renting bool
	})

	for _, station := range stationStatus.Data.Stations {
		statusMap[station.StationID] = struct {
			bikes int
			docks int
			renting bool
		}{
			bikes: station.NumBikesAvailable,
			docks: station.NumDocksAvailable,
			renting: station.IsRenting == 1,
		}
	}

	var vehicles []Vehicle
	for _, station := range stationInfo.Data.Stations {
		status := statusMap[station.StationID]
		if status.bikes == 0 {
			continue
		}

		distance := calculateDistance(latitude, longitude, station.Lat, station.Lon)
		if distance > radius {
			continue
		}

		bikes := status.bikes
		docks := status.docks
		vehicles = append(vehicles, Vehicle{
			ID:             station.StationID,
			Type:           "bike",
			Provider:       m.Name(),
			Name:           station.Name,
			Location:       Location{Latitude: station.Lat, Longitude: station.Lon},
			DistanceKM:     roundFloat(distance, 2),
			BikesAvailable: &bikes,
			DocksAvailable: &docks,
			IsAvailable:    true,
		})
	}

	return vehicles, nil
}

func (m *MEVOProvider) getStationInfo() (*MEVOStationInfo, error) {
	var result MEVOStationInfo
	_, err := m.client.R().
		SetHeader("Client-Identifier", "hackheroes-co2calculator").
		SetResult(&result).
		Get(m.baseURL + "/station_information.json")
	
	if err != nil {
		return nil, err
	}
	return &result, nil
}

func (m *MEVOProvider) getStationStatus() (*MEVOStationStatus, error) {
	var result MEVOStationStatus
	_, err := m.client.R().
		SetHeader("Client-Identifier", "hackheroes-co2calculator").
		SetResult(&result).
		Get(m.baseURL + "/station_status.json")
	
	if err != nil {
		return nil, err
	}
	return &result, nil
}

// ============================================================================
// Nextbike Provider (Worldwide - JSON API)
// ============================================================================

type NextbikeProvider struct {
	client *resty.Client
}

type NextbikeResponse struct {
	Countries []struct {
		Cities []struct {
			Uid   int    `json:"uid"`
			Name  string `json:"name"`
			Bikes []struct {
				Uid      int     `json:"uid"`
				Lat      float64 `json:"lat"`
				Lng      float64 `json:"lng"`
				BikeName string `json:"bike_name"`
			} `json:"bikes"`
		} `json:"cities"`
	} `json:"countries"`
}

func NewNextbikeProvider() *NextbikeProvider {
	return &NextbikeProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (n *NextbikeProvider) Name() string {
	return "Nextbike"
}

func (n *NextbikeProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	var result NextbikeResponse
	_, err := n.client.R().
		SetResult(&result).
		Get("https://api.nextbike.net/maps/nextbike-live.json?city=362") // Berlin as example
	
	if err != nil {
		return nil, err
	}

	var vehicles []Vehicle
	for _, country := range result.Countries {
		for _, city := range country.Cities {
			for _, bike := range city.Bikes {
				distance := calculateDistance(latitude, longitude, bike.Lat, bike.Lng)
				if distance > radius {
					continue
				}

				vehicles = append(vehicles, Vehicle{
					ID:         fmt.Sprintf("%d", bike.Uid),
					Type:       "bike",
					Provider:   n.Name(),
					Location:   Location{Latitude: bike.Lat, Longitude: bike.Lng},
					DistanceKM: roundFloat(distance, 2),
					IsAvailable: true,
				})
			}
		}
	}

	return vehicles, nil
}

// ============================================================================
// VOI Provider (Scooters - API)
// ============================================================================

type VOIProvider struct {
	client *resty.Client
}

type VOIZonesResponse struct {
	Data []struct {
		ID      string `json:"id"`
		Name    string `json:"name"`
		Lat     float64 `json:"lat"`
		Lon     float64 `json:"lon"`
		Polygon [][]float64 `json:"polygon"`
	} `json:"data"`
}

type VOIVehiclesResponse struct {
	Data []struct {
		ID       string  `json:"id"`
		Lat      float64 `json:"lat"`
		Lon      float64 `json:"lon"`
		Battery  int     `json:"battery"`
		Status   string  `json:"status"`
	} `json:"data"`
}

func NewVOIProvider() *VOIProvider {
	return &VOIProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (v *VOIProvider) Name() string {
	return "VOI"
}

func (v *VOIProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	// VOI requires authentication, but we can try public endpoints
	// For now, return empty to avoid authentication errors
	// In production, you'd need API credentials
	return []Vehicle{}, nil
}

// ============================================================================
// Lime Provider (Bikes & Scooters)
// ============================================================================

type LimeProvider struct {
	client *resty.Client
}

func NewLimeProvider() *LimeProvider {
	return &LimeProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (l *LimeProvider) Name() string {
	return "Lime"
}

func (l *LimeProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	// Lime requires session cookies and authentication
	// For now, return empty - would need proper session handling
	return []Vehicle{}, nil
}

// ============================================================================
// Tier Provider (Scooters)
// ============================================================================

type TierProvider struct {
	client *resty.Client
}

type TierVehiclesResponse struct {
	Data []struct {
		ID       string  `json:"id"`
		Lat      float64 `json:"lat"`
		Lng      float64 `json:"lng"`
		Status   string  `json:"status"`
		BatteryLevel int  `json:"batteryLevel"`
	} `json:"data"`
}

func NewTierProvider() *TierProvider {
	return &TierProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (t *TierProvider) Name() string {
	return "Tier"
}

func (t *TierProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	// Tier requires API key authentication
	// For now, return empty - would need API key
	return []Vehicle{}, nil
}

// ============================================================================
// Hive Provider (Scooters)
// ============================================================================

type HiveProvider struct {
	client *resty.Client
}

func NewHiveProvider() *HiveProvider {
	return &HiveProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (h *HiveProvider) Name() string {
	return "Hive"
}

func (h *HiveProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	// Hive API endpoint
	// https://hive.frontend.fleetbird.eu/api/prod/v1.06/map/cars/
	var result map[string]interface{}
	resp, err := h.client.R().
		SetResult(&result).
		SetQueryParams(map[string]string{
			"lat1": fmt.Sprintf("%.6f", latitude-radius),
			"lat2": fmt.Sprintf("%.6f", latitude+radius),
			"lon1": fmt.Sprintf("%.6f", longitude-radius),
			"lon2": fmt.Sprintf("%.6f", longitude+radius),
		}).
		Get("https://hive.frontend.fleetbird.eu/api/prod/v1.06/map/cars/")
	
	if err != nil {
		log.Printf("Hive API error: %v", err)
		return nil, nil
	}

	if resp.StatusCode() != 200 {
		return nil, nil
	}

	// Parse Hive response (structure may vary)
	var vehicles []Vehicle
	if data, ok := result["data"].([]interface{}); ok {
		for _, item := range data {
			if car, ok := item.(map[string]interface{}); ok {
				lat := car["lat"].(float64)
				lng := car["lng"].(float64)
				
				distance := calculateDistance(latitude, longitude, lat, lng)
				if distance > radius {
					continue
				}

				battery := int(car["battery"].(float64))
				vehicles = append(vehicles, Vehicle{
					ID:           fmt.Sprintf("%v", car["id"]),
					Type:         "scooter",
					Provider:     h.Name(),
					Location:     Location{Latitude: lat, Longitude: lng},
					DistanceKM:   roundFloat(distance, 2),
					BatteryLevel: &battery,
					IsAvailable:  true,
				})
			}
		}
	}

	return vehicles, nil
}

// ============================================================================
// Generic GBFS Provider (for other GBFS-compatible systems)
// ============================================================================

type GBFSProvider struct {
	name    string
	baseURL string
	client  *resty.Client
}

type GBFSStationInfo struct {
	Data struct {
		Stations []struct {
			StationID string  `json:"station_id"`
			Name      string  `json:"name"`
			Lat       float64 `json:"lat"`
			Lon       float64 `json:"lon"`
		} `json:"stations"`
	} `json:"data"`
}

type GBFSStationStatus struct {
	Data struct {
		Stations []struct {
			StationID         string `json:"station_id"`
			NumBikesAvailable int    `json:"num_bikes_available"`
			NumDocksAvailable int    `json:"num_docks_available"`
		} `json:"stations"`
	} `json:"data"`
}

func NewGBFSProvider(name, baseURL string) *GBFSProvider {
	return &GBFSProvider{
		name:    name,
		baseURL: baseURL,
		client:  resty.New().SetTimeout(5 * time.Second),
	}
}

func (g *GBFSProvider) Name() string {
	return g.name
}

func (g *GBFSProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	var stationInfo GBFSStationInfo
	var stationStatus GBFSStationStatus
	var wg sync.WaitGroup
	var mu sync.Mutex
	var errInfo, errStatus error

	wg.Add(2)

	go func() {
		defer wg.Done()
		_, err := g.client.R().
			SetResult(&stationInfo).
			Get(g.baseURL + "/station_information.json")
		mu.Lock()
		errInfo = err
		mu.Unlock()
	}()

	go func() {
		defer wg.Done()
		_, err := g.client.R().
			SetResult(&stationStatus).
			Get(g.baseURL + "/station_status.json")
		mu.Lock()
		errStatus = err
		mu.Unlock()
	}()

	wg.Wait()

	if errInfo != nil || errStatus != nil {
		return nil, fmt.Errorf("GBFS fetch error")
	}

	statusMap := make(map[string]struct {
		bikes int
		docks int
	})

	for _, station := range stationStatus.Data.Stations {
		statusMap[station.StationID] = struct {
			bikes int
			docks int
		}{
			bikes: station.NumBikesAvailable,
			docks: station.NumDocksAvailable,
		}
	}

	var vehicles []Vehicle
	for _, station := range stationInfo.Data.Stations {
		status := statusMap[station.StationID]
		if status.bikes == 0 {
			continue
		}

		distance := calculateDistance(latitude, longitude, station.Lat, station.Lon)
		if distance > radius {
			continue
		}

		bikes := status.bikes
		docks := status.docks
		vehicles = append(vehicles, Vehicle{
			ID:             station.StationID,
			Type:           "bike",
			Provider:       g.Name(),
			Name:           station.Name,
			Location:       Location{Latitude: station.Lat, Longitude: station.Lon},
			DistanceKM:     roundFloat(distance, 2),
			BikesAvailable: &bikes,
			DocksAvailable: &docks,
			IsAvailable:    true,
		})
	}

	return vehicles, nil
}
