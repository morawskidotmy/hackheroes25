package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"

	"github.com/gin-gonic/gin"
)

const (
	CO2_PER_KM_CAR    = 0.12  // kg of CO2 per km for a car
	BIKE_SPEED_KPH    = 15.0  // Average bike speed
	SCOOTER_SPEED_KPH = 20.0  // Average scooter speed
	CAR_SPEED_KPH     = 40.0  // Average car speed in city
)

// Vehicle represents a bike or scooter
type Vehicle struct {
	ID              string  `json:"id"`
	Type            string  `json:"type"` // bike, scooter
	Provider        string  `json:"provider"`
	Name            string  `json:"name,omitempty"`
	Location        Location `json:"location"`
	DistanceKM      float64 `json:"distance_km"`
	BatteryLevel    *int    `json:"battery_level,omitempty"`
	BikesAvailable  *int    `json:"bikes_available,omitempty"`
	DocksAvailable  *int    `json:"docks_available,omitempty"`
	IsAvailable     bool    `json:"is_available"`
}

// Location represents GPS coordinates
type Location struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
}

// CO2Result contains the calculation result
type CO2Result struct {
	Success              bool                   `json:"success"`
	ClosestVehicle       Vehicle                `json:"closest_vehicle"`
	DistanceKM           float64                `json:"distance_km"`
	CO2SavingsKG         float64                `json:"co2_savings_kg"`
	TravelTimes          TravelTimes            `json:"travel_times"`
	EnvironmentalImpact  EnvironmentalImpact    `json:"environmental_impact"`
	Message              string                 `json:"message"`
	ProvidersQueried     []string               `json:"providers_queried"`
}

// TravelTimes contains estimated travel times
type TravelTimes struct {
	BikeMinutes string `json:"bike_minutes"`
	CarMinutes  string `json:"car_minutes"`
}

// EnvironmentalImpact contains environmental metrics
type EnvironmentalImpact struct {
	CO2PerKMCarGrams int     `json:"co2_per_km_car_grams"`
	CO2SavedGrams    int     `json:"co2_saved_grams"`
	EquivalentTrees  float64 `json:"equivalent_trees"`
}

// CalculateRequest contains the request payload
type CalculateRequest struct {
	Latitude            float64 `json:"latitude" binding:"required"`
	Longitude           float64 `json:"longitude" binding:"required"`
	DestinationLatitude float64 `json:"destination_latitude" binding:"required"`
	DestinationLongitude float64 `json:"destination_longitude" binding:"required"`
	Radius              float64 `json:"radius"`
}

// NearbyStationsRequest for nearby stations query
type NearbyStationsRequest struct {
	Latitude  float64 `form:"latitude" binding:"required"`
	Longitude float64 `form:"longitude" binding:"required"`
	Radius    float64 `form:"radius"`
}

// Provider interface for different bike/scooter providers
type Provider interface {
	Name() string
	GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error)
}

// GlobalProviders holds all available providers
var GlobalProviders []Provider

func init() {
	GlobalProviders = []Provider{
		NewMEVOProvider(),
		NewNextbikeProvider(),
		NewVOIProvider(),
		NewLimeProvider(),
		NewTierProvider(),
		NewHiveProvider(),
	}
}

// HealthHandler returns server status
func HealthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "OK",
		"providers": len(GlobalProviders),
	})
}

// CalculateCO2Handler main endpoint
func CalculateCO2Handler(c *gin.Context) {
	var req CalculateRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	// Validate coordinates
	if req.Latitude < -90 || req.Latitude > 90 || req.Longitude < -180 || req.Longitude > 180 ||
		req.DestinationLatitude < -90 || req.DestinationLatitude > 90 || req.DestinationLongitude < -180 || req.DestinationLongitude > 180 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid coordinates",
		})
		return
	}

	if req.Radius == 0 {
		req.Radius = 2.0 // Default 2km radius
	}

	// Get vehicles from all providers concurrently
	vehicles := getAllVehicles(req.Latitude, req.Longitude, req.Radius)
	providers := getQueriedProviders()

	if len(vehicles) == 0 {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "No bikes or scooters available in your area",
			"message": "Please try again later or expand your search radius",
			"providers_queried": providers,
		})
		return
	}

	// Find closest vehicle
	closest := vehicles[0]

	// Calculate distance to destination
	distance := calculateDistance(req.Latitude, req.Longitude, req.DestinationLatitude, req.DestinationLongitude)

	// Calculate CO2 savings
	co2Savings := calculateCO2Savings(distance)

	// Calculate travel times
	bikeTravelTime := formatTravelTime(distance / BIKE_SPEED_KPH)
	carTravelTime := formatTravelTime(distance / CAR_SPEED_KPH)

	result := CO2Result{
		Success:            true,
		ClosestVehicle:     closest,
		DistanceKM:         roundFloat(distance, 2),
		CO2SavingsKG:       roundFloat(co2Savings, 3),
		TravelTimes: TravelTimes{
			BikeMinutes: bikeTravelTime,
			CarMinutes:  carTravelTime,
		},
		EnvironmentalImpact: EnvironmentalImpact{
			CO2PerKMCarGrams: 120,
			CO2SavedGrams:    int(co2Savings * 1000),
			EquivalentTrees:  roundFloat(co2Savings/0.021, 2),
		},
		Message:          fmt.Sprintf("By choosing a %s instead of a car for this %.2fkm trip, you save approximately %.2fkg of CO2 emissions!", closest.Type, distance, co2Savings),
		ProvidersQueried: providers,
	}

	c.JSON(http.StatusOK, result)
}

// NearbyStationsHandler returns nearby vehicles
func NearbyStationsHandler(c *gin.Context) {
	var req NearbyStationsRequest
	if err := c.BindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid query parameters",
		})
		return
	}

	if req.Radius == 0 {
		req.Radius = 1.0
	}

	vehicles := getAllVehicles(req.Latitude, req.Longitude, req.Radius)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"count": len(vehicles),
		"stations": vehicles,
		"providers_queried": getQueriedProviders(),
	})
}

// ProvidersHandler lists available providers
func ProvidersHandler(c *gin.Context) {
	providers := make([]string, len(GlobalProviders))
	for i, p := range GlobalProviders {
		providers[i] = p.Name()
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"providers": providers,
		"count": len(providers),
	})
}

// getAllVehicles fetches vehicles from all providers concurrently
func getAllVehicles(latitude, longitude, radius float64) []Vehicle {
	var wg sync.WaitGroup
	var mu sync.Mutex
	var allVehicles []Vehicle

	for _, provider := range GlobalProviders {
		wg.Add(1)
		go func(p Provider) {
			defer wg.Done()
			vehicles, err := p.GetVehicles(latitude, longitude, radius)
			if err != nil {
				log.Printf("Error fetching from %s: %v\n", p.Name(), err)
				return
			}
			mu.Lock()
			allVehicles = append(allVehicles, vehicles...)
			mu.Unlock()
		}(provider)
	}

	wg.Wait()

	// Sort by distance
	sortVehiclesByDistance(allVehicles)
	return allVehicles
}

// getQueriedProviders returns list of providers
func getQueriedProviders() []string {
	providers := make([]string, len(GlobalProviders))
	for i, p := range GlobalProviders {
		providers[i] = p.Name()
	}
	return providers
}

// calculateDistance using Haversine formula
func calculateDistance(lat1, lon1, lat2, lon2 float64) float64 {
	const R = 6371.0 // Earth's radius in km
	
	latRad1 := lat1 * (3.14159265359 / 180.0)
	latRad2 := lat2 * (3.14159265359 / 180.0)
	deltaLat := (lat2 - lat1) * (3.14159265359 / 180.0)
	deltaLon := (lon2 - lon1) * (3.14159265359 / 180.0)

	a := sinSquared(deltaLat/2) + cos(latRad1)*cos(latRad2)*sinSquared(deltaLon/2)
	c := 2.0 * asin(sqrt(a))
	
	return R * c
}

// calculateCO2Savings returns CO2 saved in kg
func calculateCO2Savings(distanceKM float64) float64 {
	return distanceKM * CO2_PER_KM_CAR
}

// formatTravelTime converts hours to readable format
func formatTravelTime(hours float64) string {
	minutes := int(hours * 60)
	if minutes < 60 {
		return fmt.Sprintf("%d minutes", minutes)
	}
	h := minutes / 60
	m := minutes % 60
	if m == 0 {
		if h == 1 {
			return "1 hour"
		}
		return fmt.Sprintf("%d hours", h)
	}
	if h == 1 {
		return fmt.Sprintf("1 hour %d minutes", m)
	}
	return fmt.Sprintf("%d hours %d minutes", h, m)
}

// Helper math functions
func sin(x float64) float64 {
	// Taylor series approximation
	result := x
	term := x
	for i := 1; i < 10; i++ {
		term *= -x * x / (float64(2*i) * float64(2*i+1))
		result += term
	}
	return result
}

func cos(x float64) float64 {
	result := 1.0
	term := 1.0
	for i := 1; i < 10; i++ {
		term *= -x * x / (float64(2*i-1) * float64(2*i))
		result += term
	}
	return result
}

func sinSquared(x float64) float64 {
	s := sin(x)
	return s * s
}

func asin(x float64) float64 {
	result := x
	term := x
	for i := 1; i < 10; i++ {
		term *= x * x * float64(2*i-1) / float64(2*i)
		result += term / float64(2*i+1)
	}
	return result
}

func sqrt(x float64) float64 {
	if x == 0 {
		return 0
	}
	z := x
	for i := 0; i < 20; i++ {
		z = (z + x/z) / 2
	}
	return z
}

func roundFloat(val float64, precision int) float64 {
	multiplier := 1.0
	for i := 0; i < precision; i++ {
		multiplier *= 10
	}
	return float64(int(val*multiplier)) / multiplier
}

func sortVehiclesByDistance(vehicles []Vehicle) {
	// Simple bubble sort for small lists
	for i := 0; i < len(vehicles); i++ {
		for j := i + 1; j < len(vehicles); j++ {
			if vehicles[j].DistanceKM < vehicles[i].DistanceKM {
				vehicles[i], vehicles[j] = vehicles[j], vehicles[i]
			}
		}
	}
}

func main() {
	if os.Getenv("GIN_MODE") == "" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.Default()

	// Enable CORS
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Routes
	router.GET("/health", HealthHandler)
	router.GET("/providers", ProvidersHandler)
	router.POST("/v1/calculate-co2-savings", CalculateCO2Handler)
	router.GET("/v1/nearby-stations", NearbyStationsHandler)

	// Serve static files
	router.Static("/static", "./static")
	router.StaticFile("/", "./index.html")

	port := ":3000"
	log.Printf("Starting server on %s", port)
	log.Printf("Available providers: %d", len(GlobalProviders))
	for _, p := range GlobalProviders {
		log.Printf("  - %s", p.Name())
	}

	if err := router.Run(port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
