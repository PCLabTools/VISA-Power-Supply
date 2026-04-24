"""
file: simulated.py
description: Simulated implementation of VISAPowerSupply for development and testing.
author: Your Name (your.email@example.com)
"""

from time import sleep
from paf.communication import Message
from .module import VISAPowerSupply, BaseVISAPowerSupply


class SimulatedVISAPowerSupply(BaseVISAPowerSupply):
    """Simulated implementation of VISAPowerSupply."""

    def __init__(self, address: str, protocol, debug: int = 0):
        """Initialize simulated power supply with state tracking.

        Args:
            address (str): Module address.
            protocol: Protocol instance.
            debug (int): Debug level.
        """
        super().__init__(address, protocol, debug)
        # Simulated state
        self.connected = False
        self.voltage = 0.0
        self.current = 0.0
        self.output_enabled = False
        self.ovp_threshold = 15.0
        self.ocp_threshold = 5.0
        self.model_id = "SimulatedVISAPowerSupply-v1.0"

    def background_task(self):
        """Simulated background task."""
        while self.background_task_running:
            if self.debug: print(f"{self.__class__.__name__} ({self.address}): Performing background task.")
            # TODO: implement simulated background task logic (e.g., telemetry updates)
            sleep(1)

    def message_connect(self, message: Message) -> bool:
        """Handle the "connect" command - establish connection to simulated power supply.

        Args:
            message (Message): Incoming message with connection parameters.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling connect command: {message}")
        self.connected = True
        # Send response if this is a request
        if message.source:
            self.protocol.send_response(message, {"status": "connected", "model": self.model_id})
        return False

    def message_disconnect(self, message: Message) -> bool:
        """Handle the "disconnect" command - disconnect from simulated power supply.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling disconnect command: {message}")
        self.connected = False
        self.output_enabled = False
        # Send response if this is a request
        if message.source:
            self.protocol.send_response(message, {"status": "disconnected"})
        return False

    def message_identify(self, message: Message) -> bool:
        """Handle the "identify" command - identify the simulated power supply.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling identify command: {message}")
        # Send response if this is a request
        if message.source:
            self.protocol.send_response(message, {
                "model": self.model_id,
                "connected": self.connected,
                "voltage_range": [0.0, 30.0],
                "current_range": [0.0, 5.0]
            })
        return False

    def message_set_voltage(self, message: Message) -> bool:
        """Handle the "set_voltage" command - set output voltage.

        Args:
            message (Message): Incoming message with voltage value in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_voltage command: {message}")
        try:
            voltage = message.payload.get("voltage", 0.0)
            self.voltage = float(voltage)
            # Send response if this is a request
            if message.source:
                self.protocol.send_response(message, {"voltage": self.voltage, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            if message.source:
                self.protocol.send_response(message, {"error": "Invalid voltage value"})
        return False

    def message_set_current(self, message: Message) -> bool:
        """Handle the "set_current" command - set output current limit.

        Args:
            message (Message): Incoming message with current value in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_current command: {message}")
        try:
            current = message.payload.get("current", 0.0)
            self.current = float(current)
            # Send response if this is a request
            if message.source:
                self.protocol.send_response(message, {"current": self.current, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            if message.source:
                self.protocol.send_response(message, {"error": "Invalid current value"})
        return False

    def message_toggle_output(self, message: Message) -> bool:
        """Handle the "toggle_output" command - enable or disable power supply output.

        Args:
            message (Message): Incoming message with output state in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling toggle_output command: {message}")
        try:
            if "enable" in message.payload:
                self.output_enabled = bool(message.payload.get("enable"))
            else:
                self.output_enabled = not self.output_enabled
            # Send response if this is a request
            if message.source:
                self.protocol.send_response(message, {"output_enabled": self.output_enabled, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            if message.source:
                self.protocol.send_response(message, {"error": "Invalid output command"})
        return False

    def message_set_ovp(self, message: Message) -> bool:
        """Handle the "set_ovp" command - set over-voltage protection threshold.

        Args:
            message (Message): Incoming message with OVP threshold in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_ovp command: {message}")
        try:
            ovp = message.payload.get("threshold", 15.0)
            self.ovp_threshold = float(ovp)
            # Send response if this is a request
            if message.source:
                self.protocol.send_response(message, {"ovp_threshold": self.ovp_threshold, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            if message.source:
                self.protocol.send_response(message, {"error": "Invalid OVP value"})
        return False

    def message_set_ocp(self, message: Message) -> bool:
        """Handle the "set_ocp" command - set over-current protection threshold.

        Args:
            message (Message): Incoming message with OCP threshold in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_ocp command: {message}")
        try:
            ocp = message.payload.get("threshold", 5.0)
            self.ocp_threshold = float(ocp)
            # Send response if this is a request
            if message.source:
                self.protocol.send_response(message, {"ocp_threshold": self.ocp_threshold, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            if message.source:
                self.protocol.send_response(message, {"error": "Invalid OCP value"})
        return False

    def message_measure(self, message: Message) -> bool:
        """Handle the "measure" command - measure voltage, current, and power.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling measure command: {message}")
        # Calculate simulated power
        power = self.voltage * self.current if self.output_enabled else 0.0
        # Send response if this is a request
        if message.source:
            self.protocol.send_response(message, {
                "voltage": self.voltage,
                "current": self.current,
                "power": power,
                "output_enabled": self.output_enabled
            })
        return False

    def message_custom_action(self, message: Message) -> bool:
        """Handles the "custom_action" message.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling custom action: {message}")
        # TODO: implement simulated custom action logic
        return False


# Register this implementation with the factory
VISAPowerSupply.register("simulated", SimulatedVISAPowerSupply)
