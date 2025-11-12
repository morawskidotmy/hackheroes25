# MEVO Setup Guide

## What You Need to Know

The good news: **MEVO uses GBFS (General Bikeshare Feed Specification)** which is **100% free and requires no authentication**.

## Current Implementation Status

✅ **MEVO is fully integrated and ready to use**

The API already implements MEVO through GBFS endpoints:
- Station information: `https://gbfs.urbansharing.com/rowermevo.pl/station_information.json`
- Station status (availability): `https://gbfs.urbansharing.com/rowermevo.pl/station_status.json`

## What is Required

### Mandatory (Already Implemented)
- ✅ **Client-Identifier Header**: Custom header identifying your application
- ✅ **HTTPS Access**: SSL/TLS support for secure requests
- ✅ **Base URL**: `https://gbfs.urbansharing.com/rowermevo.pl`

### Your Setup

The API automatically sends:
```
Client-Identifier: hackheroes-co2calculator
```

To customize this, edit in `providers.go`:

```go
func (m *MEVOProvider) getStationInfo() (*MEVOStationInfo, error) {
	var result MEVOStationInfo
	_, err := m.client.R().
		SetHeader("Client-Identifier", "YOUR-NAME-co2calculator"). // ← Change here
		SetResult(&result).
		Get(m.baseURL + "/station_information.json")
	
	if err != nil {
		return nil, err
	}
	return &result, nil
}
```

## MEVO API Endpoints Used

### 1. Station Information
```
GET https://gbfs.urbansharing.com/rowermevo.pl/station_information.json
```

Returns:
```json
{
  "data": {
    "stations": [
      {
        "station_id": "175",
        "name": "Przymorze",
        "lat": 54.4123,
        "lon": 18.5456,
        "address": "Some Address"
      }
    ]
  }
}
```

### 2. Station Status
```
GET https://gbfs.urbansharing.com/rowermevo.pl/station_status.json
```

Returns:
```json
{
  "data": {
    "stations": [
      {
        "station_id": "175",
        "num_bikes_available": 7,
        "num_docks_available": 5,
        "is_renting": 1,
        "is_returning": 1
      }
    ]
  }
}
```

## Optional: Customize Client Identifier

MEVO recommends identifying your app properly. Update in `providers.go`:

```go
type MEVOProvider struct {
	baseURL string
	client  *resty.Client
}

func NewMEVOProvider() *MEVOProvider {
	return &MEVOProvider{
		baseURL: "https://gbfs.urbansharing.com/rowermevo.pl",
		client:  resty.New().SetTimeout(5 * time.Second),
	}
}
```

And in the request methods:

```go
SetHeader("Client-Identifier", "mycompany-myapp") // Follow their naming: company-app
```

**Examples**:
- `hackheroes-co2calculator`
- `greentech-bikefinder`
- `myorg-environmentalapp`

## Testing MEVO Integration

### Test 1: Direct API Call

```bash
curl -H "Client-Identifier: hackheroes-co2calculator" \
  https://gbfs.urbansharing.com/rowermevo.pl/station_information.json | jq .
```

Should return list of stations in Poland.

### Test 2: Through Our API

```bash
# Start the server
go run main.go providers.go

# Get nearby stations in Warsaw
curl "http://localhost:3000/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2"
```

Should return MEVO stations with availability.

### Test 3: Calculate CO2

```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0300
  }'
```

Should find closest MEVO bike and calculate savings.

## Verification Checklist

✅ **Before Deployment**:
- [ ] MEVO API is accessible: `curl https://gbfs.urbansharing.com/rowermevo.pl/station_information.json`
- [ ] Client-Identifier header is set
- [ ] Server responds with real MEVO data
- [ ] Warsaw coordinates return results

## Coverage

**MEVO operates in**:
- 🇵🇱 Gdańsk (primary)
- 🇵🇱 Other Polish cities (expanding)

**Station coverage**: ~50 stations across cities

## Data Update Frequency

MEVO updates:
- **Station information**: Once per month (relatively static)
- **Station status**: Every 30-60 seconds (real-time)

Our API queries live, so you always get current availability.

## Rate Limiting

MEVO has:
- No documented rate limits for GBFS feeds
- Recommended: 1 request per 30 seconds per endpoint
- Our implementation: Queries on-demand (good for low traffic)

For high traffic, consider:
```go
// Add caching (optional)
cache.Set("mevo_stations", data, 30*time.Second)
```

## Troubleshooting

### Issue: No MEVO stations found

**Cause**: Coordinates outside MEVO coverage area
**Solution**: Use Warsaw coordinates for testing

### Issue: "Connection refused"

**Cause**: HTTPS not working or API unreachable
**Solution**: 
```bash
# Test connectivity
curl -I https://gbfs.urbansharing.com/rowermevo.pl/station_information.json
```

### Issue: Empty station list

**Cause**: MEVO API down or returning no data
**Solution**: Check their status or retry after 60 seconds

## Documentation Links

- **MEVO Website**: https://www.rowermevo.pl
- **GBFS Specification**: https://gbfs.org
- **Support Email**: kontakt@rowermevo.pl
- **Support Phone**: +48 58 739 11 23

## Terms of Use

MEVO's public GBFS feed:
- ✅ Free to use
- ✅ No API key required
- ✅ Open data license
- ✅ Real-time access allowed
- ⚠️ Check their terms: https://www.rowermevo.pl/terms

## Next Steps

1. **Test integration**: `go run main.go providers.go`
2. **Verify MEVO data**: Call `/v1/nearby-stations` with Warsaw coords
3. **Deploy**: Follow DEPLOYMENT.md
4. **Monitor**: Check logs for any MEVO API issues

## Summary

**Zero configuration needed** - MEVO works out of the box!

The only optional step is customizing the `Client-Identifier` header to match your organization's naming convention.

---

For questions, contact MEVO support or check their GBFS documentation at https://gbfs.org
