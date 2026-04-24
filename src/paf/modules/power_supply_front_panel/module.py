"""
file: module.py
description: This module is designed to run a basic webserver which serves a local webpage that allows for this module to interact with the VISAPowerSupply module through the PAF communication protocol.
author: Your Name (your.email@example.com)
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from time import sleep
from typing import Optional
from paf.communication import Message, Protocol, Module


class PowerSupplyRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the power supply control panel."""
    # Timeout for the accepted socket. StreamRequestHandler.setup() calls
    # socket.settimeout(self.timeout), so rfile.readline() in
    # handle_one_request() raises TimeoutError after 1 s of inactivity.
    # BaseHTTPRequestHandler already handles that by setting close_connection
    # = True, so the keep-alive loop exits and handle_request() returns.
    # Without this, handle_request() blocks indefinitely on the keep-alive
    # connection after the shutdown POST is served, which prevents the
    # background task from ever checking background_task_running = False.
    timeout = 1

    def do_GET(self):
        """Handle GET requests - serve static files."""
        # Serve files from the assets directory
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
        
        try:
            return super().do_GET()
        except Exception as e:
            if self.server.debug:
                print(f"Error serving {self.path}: {e}")
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests - API endpoints."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            # API endpoints for power supply commands
            if self.path.startswith('/api/power-supply/'):
                command = self.path.split('/')[-1]
                response = self.handle_power_supply_command(command, data)
                self.send_json_response(response)
            
            # Shutdown endpoint
            elif self.path == '/api/shutdown':
                try:
                    self.server.protocol.send_action(self.server.main_module_address, "shutdown", {})
                    self.send_json_response({"status": "shutdown initiated"})
                except Exception as e:
                    self.send_json_response({"error": str(e)}, 500)
            
            else:
                self.send_error(404, "Endpoint not found")
        
        except Exception as e:
            if self.server.debug:
                print(f"Error handling POST request: {e}")
            self.send_json_response({"error": str(e)}, 500)

    def handle_power_supply_command(self, command: str, data: dict) -> dict:
        """Route power supply commands through the protocol."""
        try:
            # Map command names to power supply actions
            command_map = {
                'connect': 'connect',
                'disconnect': 'disconnect',
                'identify': 'identify',
                'set_voltage': 'set_voltage',
                'set_current': 'set_current',
                'toggle_output': 'toggle_output',
                'set_ovp': 'set_ovp',
                'set_ocp': 'set_ocp',
                'measure': 'measure',
            }
            
            if command not in command_map:
                return {"error": f"Unknown command: {command}"}, 400
            
            # Send request to power supply module
            try:
                response = self.server.protocol.send_request(
                    self.server.power_supply_address,
                    command_map[command],
                    data,
                    timeout=5
                )
                return response.payload if response else {"status": "ok"}
            except TimeoutError:
                return {"error": "Power supply module timeout"}, 504
        
        except Exception as e:
            return {"error": str(e)}, 500

    def send_json_response(self, data: dict, status_code: int = 200):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging or use debug mode."""
        if self.server.debug:
            super().log_message(format, *args)


class PowerSupplyFrontPanel(Module):
    """
    This module is designed to run a basic webserver which serves a local webpage that allows for this module to interact with the VISAPowerSupply module through the PAF communication protocol.
    """

    def __init__(self, address: str, protocol: Protocol, debug: Optional[int] = 0, power_supply_address: Optional[str] = None, main_module_address: Optional[str] = None, port: int = 5000):
        """Initialises the module and sets up the protocol.

        Args:
            address (str): The address of the module.
            protocol (Protocol): The protocol instance.
            debug (Optional[int]): Debug level (default is 0).
            power_supply_address (Optional[str]): The address of the power supply module.
            main_module_address (Optional[str]): The address of the main module.
            port (int): Port for the webserver (default is 5000).
        """
        self.debug = debug
        self.power_supply_address = power_supply_address
        self.main_module_address = main_module_address
        self.port = port
        self.server = None
        super().__init__(address, protocol)

    def handle_message(self, message: Message) -> bool:
        """Handle incoming messages.

        Args:
            message (Message): The message to handle.

        Returns:
            bool: True if the module should shutdown, False otherwise.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling message: {message}")
        if message.command == "custom_action":
            return self.message_custom_action(message)
        return super().handle_message(message)

    def background_task(self):
        """Background task that runs while the module is active - starts webserver."""
        # Set up the assets directory path
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.chdir(assets_dir)
        
        # Create custom request handler with access to protocol and power_supply_address
        handler = PowerSupplyRequestHandler
        handler.server = None  # Will be set by HTTPServer
        
        # Create HTTP server
        self.server = HTTPServer(('localhost', self.port), handler)
        self.server.protocol = self.protocol
        self.server.power_supply_address = self.power_supply_address
        self.server.main_module_address = self.main_module_address
        self.server.debug = self.debug
        
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Webserver starting on http://localhost:{self.port}")
        
        # Run webserver until background_task_running is False
        while self.background_task_running:
            self.server.timeout = 0.5  # Non-blocking timeout
            try:
                self.server.handle_request()
            except Exception as e:
                if self.debug:
                    print(f"{self.__class__.__name__} ({self.address}): Webserver error: {e}")
        
        # Clean up
        if self.server:
            try:
                self.server.server_close()
            except Exception as e:
                if self.debug:
                    print(f"{self.__class__.__name__} ({self.address}): Error closing server: {e}")

    def message_custom_action(self, message: Message) -> bool:
        """Handles the "custom_action" message.

        Args:
            message (Message): Incoming message to handle.

        Returns:
            bool: False to indicate that the module should continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling custom action: {message}")
        return False
