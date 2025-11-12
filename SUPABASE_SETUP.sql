-- CO2 Bike Calculator - Supabase Database Setup
-- Run these SQL commands in your Supabase SQL Editor

-- Create co2_calculations table
CREATE TABLE co2_calculations (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  co2_savings_kg DECIMAL(10, 3) NOT NULL,
  distance_km DECIMAL(10, 2) NOT NULL,
  start_lat DECIMAL(10, 6) NOT NULL,
  start_lon DECIMAL(10, 6) NOT NULL,
  end_lat DECIMAL(10, 6) NOT NULL,
  end_lon DECIMAL(10, 6) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create journey_tracking table for per-journey transport choice tracking
CREATE TABLE journey_tracking (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  start_lat DECIMAL(10, 6) NOT NULL,
  start_lon DECIMAL(10, 6) NOT NULL,
  end_lat DECIMAL(10, 6) NOT NULL,
  end_lon DECIMAL(10, 6) NOT NULL,
  distance_km DECIMAL(10, 2) NOT NULL,
  chosen_transport VARCHAR(50) NOT NULL CHECK (chosen_transport IN ('bike', 'car')),
  potential_co2_savings_kg DECIMAL(10, 3),
  nearest_station_name VARCHAR(255),
  nearest_station_lat DECIMAL(10, 6),
  nearest_station_lon DECIMAL(10, 6),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_stats table for tracking overall stats
CREATE TABLE user_stats (
  user_id VARCHAR(255) PRIMARY KEY,
  total_co2_saved_kg DECIMAL(10, 3) DEFAULT 0,
  total_bike_journeys INT DEFAULT 0,
  total_car_journeys INT DEFAULT 0,
  net_neutral BOOLEAN DEFAULT FALSE,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_co2_calculations_user_id ON co2_calculations(user_id);
CREATE INDEX idx_co2_calculations_created_at ON co2_calculations(created_at);
CREATE INDEX idx_journey_tracking_user_id ON journey_tracking(user_id);
CREATE INDEX idx_journey_tracking_created_at ON journey_tracking(created_at);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE co2_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE journey_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;

-- Create a policy so users can only see their own calculations
CREATE POLICY "Users can view their own calculations"
  ON co2_calculations
  FOR SELECT
  USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert their own calculations"
  ON co2_calculations
  FOR INSERT
  WITH CHECK (user_id = auth.uid()::text);

-- Journey tracking policies
CREATE POLICY "Users can view their own journeys"
  ON journey_tracking
  FOR SELECT
  USING (user_id = auth.uid()::text);

CREATE POLICY "Users can insert their own journeys"
  ON journey_tracking
  FOR INSERT
  WITH CHECK (user_id = auth.uid()::text);

-- User stats policies
CREATE POLICY "Users can view their own stats"
  ON user_stats
  FOR SELECT
  USING (user_id = auth.uid()::text);

CREATE POLICY "Users can update their own stats"
  ON user_stats
  FOR UPDATE
  USING (user_id = auth.uid()::text);
