// Global configuration
const API_BASE_URL = 'http://localhost:5000/api';
const LOG_LIMIT = 100;

// State management
let appState = {
    connected: false,
    outputEnabled: false,
    logs: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Power Supply Control Panel initialized');
    addLog('System', 'Power Supply Control Panel loaded', 'success');
    startPeriodicMeasurements();
});

// Utility functions
function addLog(source, message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
        timestamp,
        source,
        message,
        type
    };
    
    appState.logs.push(logEntry);
    if (appState.logs.length > LOG_LIMIT) {
        appState.logs.shift();
    }
    
    console.log(`[${timestamp}] ${source}: ${message}`);
}

function updateConnectionStatus(connected) {
    appState.connected = connected;
    const statusEl = document.getElementById('connection-status');
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    const identifyBtn = document.getElementById('identify-btn');
    const outputBtns = document.querySelectorAll('#output-on-btn, #output-off-btn, #measure-btn');
    
    if (connected) {
        statusEl.textContent = 'Connected';
        statusEl.className = 'status-value connected';
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
        identifyBtn.disabled = false;
        outputBtns.forEach(btn => btn.disabled = false);
        addLog('System', 'Power supply connected', 'success');
    } else {
        statusEl.textContent = 'Disconnected';
        statusEl.className = 'status-value disconnected';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        identifyBtn.disabled = true;
        outputBtns.forEach(btn => btn.disabled = true);
        appState.outputEnabled = false;
        updateOutputStatus(false);
        addLog('System', 'Power supply disconnected', 'warning');
    }
}

function updateOutputStatus(enabled) {
    appState.outputEnabled = enabled;
    const statusEl = document.getElementById('output-status');
    
    if (enabled) {
        statusEl.textContent = 'On';
        statusEl.style.color = '#28a745';
    } else {
        statusEl.textContent = 'Off';
        statusEl.style.color = '#dc3545';
    }
}

function updateVoltageDisplay() {
    const slider = document.getElementById('voltage-slider');
    const input = document.getElementById('voltage-input');
    const display = document.getElementById('voltage-display');
    
    input.value = parseFloat(slider.value).toFixed(1);
    display.textContent = parseFloat(slider.value).toFixed(1) + ' V';
}

function updateCurrentDisplay() {
    const slider = document.getElementById('current-slider');
    const input = document.getElementById('current-input');
    const display = document.getElementById('current-display');
    
    input.value = parseFloat(slider.value).toFixed(2);
    display.textContent = parseFloat(slider.value).toFixed(2) + ' A';
}

// API Communication
function sendCommand(command, data = {}) {
    return fetch(`${API_BASE_URL}/power-supply/${command}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        addLog('API Error', `Failed to send ${command}: ${error.message}`, 'error');
        throw error;
    });
}

// Power Supply Commands
function connectPowerSupply() {
    addLog('Command', 'Connecting to power supply...', 'info');
    sendCommand('connect', {})
        .then(response => {
            updateConnectionStatus(true);
            addLog('Command', 'Connected: ' + JSON.stringify(response), 'success');
        })
        .catch(error => {
            addLog('Error', 'Connection failed: ' + error.message, 'error');
        });
}

function disconnectPowerSupply() {
    addLog('Command', 'Disconnecting from power supply...', 'info');
    sendCommand('disconnect', {})
        .then(response => {
            updateConnectionStatus(false);
            addLog('Command', 'Disconnected successfully', 'success');
        })
        .catch(error => {
            addLog('Error', 'Disconnection failed: ' + error.message, 'error');
        });
}

function identifyDevice() {
    addLog('Command', 'Identifying device...', 'info');
    sendCommand('identify', {})
        .then(response => {
            addLog('Device Info', JSON.stringify(response), 'success');
            alert('Device Information:\n' + JSON.stringify(response, null, 2));
        })
        .catch(error => {
            addLog('Error', 'Identification failed: ' + error.message, 'error');
        });
}

function setVoltage() {
    const voltage = parseFloat(document.getElementById('voltage-slider').value);
    addLog('Command', `Setting voltage to ${voltage} V`, 'info');
    
    sendCommand('set_voltage', { voltage })
        .then(response => {
            addLog('Command', `Voltage set to ${voltage} V`, 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to set voltage: ' + error.message, 'error');
        });
}

function setVoltageFromInput() {
    const voltage = parseFloat(document.getElementById('voltage-input').value);
    document.getElementById('voltage-slider').value = voltage;
    updateVoltageDisplay();
    setVoltage();
}

function setCurrent() {
    const current = parseFloat(document.getElementById('current-slider').value);
    addLog('Command', `Setting current limit to ${current} A`, 'info');
    
    sendCommand('set_current', { current })
        .then(response => {
            addLog('Command', `Current limit set to ${current} A`, 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to set current: ' + error.message, 'error');
        });
}

function setCurrentFromInput() {
    const current = parseFloat(document.getElementById('current-input').value);
    document.getElementById('current-slider').value = current;
    updateCurrentDisplay();
    setCurrent();
}

function enableOutput() {
    addLog('Command', 'Enabling output...', 'info');
    
    sendCommand('toggle_output', { enable: true })
        .then(response => {
            updateOutputStatus(true);
            addLog('Command', 'Output enabled', 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to enable output: ' + error.message, 'error');
        });
}

function disableOutput() {
    addLog('Command', 'Disabling output...', 'info');
    
    sendCommand('toggle_output', { enable: false })
        .then(response => {
            updateOutputStatus(false);
            addLog('Command', 'Output disabled', 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to disable output: ' + error.message, 'error');
        });
}

function setOVP() {
    const threshold = parseFloat(document.getElementById('ovp-input').value);
    addLog('Command', `Setting OVP to ${threshold} V`, 'info');
    
    sendCommand('set_ovp', { threshold })
        .then(response => {
            addLog('Command', `OVP set to ${threshold} V`, 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to set OVP: ' + error.message, 'error');
        });
}

function setOCP() {
    const threshold = parseFloat(document.getElementById('ocp-input').value);
    addLog('Command', `Setting OCP to ${threshold} A`, 'info');
    
    sendCommand('set_ocp', { threshold })
        .then(response => {
            addLog('Command', `OCP set to ${threshold} A`, 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to set OCP: ' + error.message, 'error');
        });
}

function measureNow() {
    addLog('Command', 'Measuring...', 'info');
    
    sendCommand('measure', {})
        .then(response => {
            document.getElementById('meas-voltage').textContent = parseFloat(response.voltage || 0).toFixed(2) + ' V';
            document.getElementById('meas-current').textContent = parseFloat(response.current || 0).toFixed(2) + ' A';
            document.getElementById('meas-power').textContent = parseFloat(response.power || 0).toFixed(2) + ' W';
            addLog('Measurement', `V: ${response.voltage}V, I: ${response.current}A, P: ${response.power}W`, 'success');
        })
        .catch(error => {
            addLog('Error', 'Failed to measure: ' + error.message, 'error');
        });
}

function startPeriodicMeasurements() {
    // Measure every 2 seconds if connected
    setInterval(() => {
        if (appState.connected) {
            sendCommand('measure', {})
                .then(response => {
                    document.getElementById('meas-voltage').textContent = parseFloat(response.voltage || 0).toFixed(2) + ' V';
                    document.getElementById('meas-current').textContent = parseFloat(response.current || 0).toFixed(2) + ' A';
                    document.getElementById('meas-power').textContent = parseFloat(response.power || 0).toFixed(2) + ' W';
                })
                .catch(error => {
                    // Silent fail for periodic measurements
                });
        }
    }, 2000);
}

// Logging and System Controls
function showLogs() {
    const logContainer = document.getElementById('log-container');
    logContainer.innerHTML = '';
    
    appState.logs.forEach(entry => {
        const logEl = document.createElement('div');
        logEl.className = 'log-entry ' + entry.type;
        logEl.textContent = `[${entry.timestamp}] ${entry.source}: ${entry.message}`;
        logContainer.appendChild(logEl);
    });
    
    document.getElementById('log-modal').classList.add('show');
}

function closeLogs() {
    document.getElementById('log-modal').classList.remove('show');
}

function shutdownApplication() {
    addLog('System', 'Shutting down application...', 'warning');
    
    fetch(`${API_BASE_URL}/shutdown`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        addLog('System', 'Shutdown signal sent', 'warning');
        // Close the webpage tab after a short delay to allow the message to be sent
        setTimeout(() => {
            window.close();
        }, 500);
    })
    .catch(error => {
        addLog('Error', 'Failed to send shutdown signal: ' + error.message, 'error');
    });
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('log-modal');
    if (event.target === modal) {
        modal.classList.remove('show');
    }
}
