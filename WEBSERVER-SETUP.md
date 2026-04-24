# Power Supply Front Panel - Webserver Setup Guide

## Overview

The PowerSupplyFrontPanel module now includes a complete web-based control panel with a professional UI for controlling VISA Power Supply devices through a web browser.

## Starting the Application

```bash
cd c:\Repositories\VISA-Power-Supply
set PYTHONPATH=src
python src/main.py
```

## Accessing the Control Panel

Once the application starts, open your web browser and navigate to:

```
http://localhost:5000
```

You should see a beautiful power supply control panel with all controls ready to use.

## Features Available in Web UI

### 1. **Connection Management**
- **Connect** - Establish connection to the power supply
- **Disconnect** - Close the connection
- **Identify Device** - Query device information (model, serial number)

### 2. **Voltage Control**
- Slider for smooth voltage adjustment (0-30V)
- Numeric input for precise voltage entry
- Real-time display of set voltage

### 3. **Current Control**
- Slider for current limit adjustment (0-5A)
- Numeric input for precise current entry
- Real-time display of set current limit

### 4. **Output Management**
- **Output ON** - Enable power supply output
- **Output OFF** - Disable power supply output
- Status indicator showing current output state

### 5. **Protection Settings**
- Over-Voltage Protection (OVP) threshold setting
- Over-Current Protection (OCP) threshold setting
- Default values: OVP=15V, OCP=5A

### 6. **Real-Time Measurements**
- Voltage reading (updates automatically every 2 seconds)
- Current reading (updates automatically every 2 seconds)
- Power reading (calculated from V × I)
- Manual refresh available with "Measure Now" button

### 7. **System Control**
- **View Logs** - Open system activity log with color-coded entries
- **Shutdown Application** - Safely shutdown the entire application

## Technical Details

### Architecture
```
Browser (HTML/CSS/JS)
    ↓ (HTTP Requests)
Webserver (http.server)
    ↓ (API Routes)
PowerSupplyFrontPanel Module
    ↓ (Protocol Messages)
VISAPowerSupply Module (Simulated)
```

### API Endpoints

All API calls use POST to `http://localhost:5000/api/`

#### Power Supply Commands
- `power-supply/connect` - Connect device
- `power-supply/disconnect` - Disconnect device
- `power-supply/identify` - Get device info
- `power-supply/set_voltage` - Set voltage
- `power-supply/set_current` - Set current limit
- `power-supply/toggle_output` - Toggle output on/off
- `power-supply/set_ovp` - Set OVP threshold
- `power-supply/set_ocp` - Set OCP threshold
- `power-supply/measure` - Get measurements

#### System Commands
- `shutdown` - Broadcast shutdown signal

### Response Format

All responses are JSON:

```json
{
  "status": "ok",
  "voltage": 12.5,
  "current": 2.3,
  "power": 28.75,
  "output_enabled": true,
  "connected": true
}
```

## File Structure

```
src/paf/modules/power_supply_front_panel/
├── module.py                 # Main module with webserver
├── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_module.py
├── scripts/
│   └── run-tests.bat
└── assets/                   # Web assets (served by webserver)
    ├── index.html            # Main UI page
    ├── style.css             # Styling
    └── app.js                # Client-side logic
```

## Webserver Details

- **Server Type**: Python http.server.HTTPServer
- **Port**: 5000 (default, configurable)
- **Address**: localhost
- **Assets Directory**: `assets/` subfolder
- **Request Handler**: Custom PowerSupplyRequestHandler
  - Serves static files on GET requests
  - Routes API calls on POST requests
  - Handles CORS headers

## Performance Notes

- **Measurement Updates**: Every 2 seconds (automatic)
- **Server Timeout**: 0.5 seconds (non-blocking)
- **Thread**: Runs in separate module thread
- **Responsiveness**: UI remains responsive during operations

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, you can modify the port in `src/main.py`:

```python
PowerSupplyFrontPanel("power_supply_front_panel", self.protocol, 
                     debug=self.debug, 
                     power_supply_address="visa_power_supply", 
                     main_module_address=self.address,
                     port=8000)  # Use different port
```

### CORS Issues
CORS headers are automatically included in all responses. If you still experience issues, check:
- Browser console for error messages
- Application debug output
- Firewall/proxy settings

### Connection Fails
If "Connect" button fails:
1. Check that visa_power_supply module started correctly
2. Review application debug output
3. Check system logs for error messages

### Measurements Not Updating
If measurements don't auto-update:
1. Ensure device is connected
2. Check browser console for JavaScript errors
3. Verify webserver is running (check terminal output)

## Testing

To run tests for the PowerSupplyFrontPanel module:

```bash
cd c:\Repositories\VISA-Power-Supply
set PYTHONPATH=src
python -m unittest discover -s src/paf/modules/power_supply_front_panel/tests -p "test_*.py" -v
```

All tests should pass without errors.

## Development Notes

The webserver uses Python's built-in `http.server` module to avoid external dependencies. The implementation is fully thread-safe and integrates seamlessly with the PAF protocol bus.

Each UI action sends a message through the PAF protocol to the VISAPowerSupply module, which processes the command and returns a response that the browser UI displays.

For more information about the PAF architecture, see the main project documentation.
