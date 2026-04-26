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
        self.measurement_counter = 0
        self.interaction_counter = 0
        self.error_queue = []

    def _push_error(self, error_text: str) -> None:
        """Store instrument errors for later retrieval via error_query."""
        self.error_queue.append(error_text)
        # Keep queue bounded so repeated bad calls do not grow unbounded.
        if len(self.error_queue) > 50:
            self.error_queue.pop(0)

    def _next_measurement_profile(self) -> tuple[float, float]:
        """Return deterministic simulation factors for load and voltage drop."""
        self.measurement_counter += 1
        profile_index = (self.measurement_counter + self.interaction_counter) % 8

        # Load factor cycles 35% -> 98% to emulate changing DUT demand.
        load_factor = 0.35 + (profile_index * 0.09)
        if load_factor > 0.98:
            load_factor = 0.98

        # Slight voltage sag under heavier load.
        voltage_factor = 1.0 - (load_factor * 0.01)
        return load_factor, voltage_factor

    def _respond(self, message: Message, payload: dict) -> None:
        """Send a response when the message is a request."""
        if message.source:
            self.protocol.send_response(message, payload)

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
        self.interaction_counter += 1
        self._respond(message, {"status": "connected", "model": self.model_id})
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
        self.interaction_counter += 1
        self._respond(message, {"status": "disconnected"})
        return False

    def message_identify(self, message: Message) -> bool:
        """Handle the "identify" command - identify the simulated power supply.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling identify command: {message}")
        self._respond(message, {
            "model": self.model_id,
            "connected": self.connected,
            "voltage_range": [0.0, 30.0],
            "current_range": [0.0, 5.0],
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
        if not self.connected:
            self._push_error("-100,Power supply is not connected")
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            voltage = message.payload.get("voltage", 0.0)
            self.voltage = max(0.0, min(30.0, float(voltage)))
            self.interaction_counter += 1
            self._respond(message, {"voltage": self.voltage, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            self._push_error("-222,Invalid voltage value")
            self._respond(message, {"error": "Invalid voltage value"})
        return False

    def message_set_current(self, message: Message) -> bool:
        """Handle the "set_current" command - set output current limit.

        Args:
            message (Message): Incoming message with current value in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_current command: {message}")
        if not self.connected:
            self._push_error("-100,Power supply is not connected")
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            current = message.payload.get("current", 0.0)
            self.current = max(0.0, min(5.0, float(current)))
            self.interaction_counter += 1
            self._respond(message, {"current": self.current, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            self._push_error("-223,Invalid current value")
            self._respond(message, {"error": "Invalid current value"})
        return False

    def message_toggle_output(self, message: Message) -> bool:
        """Handle the "toggle_output" command - enable or disable power supply output.

        Args:
            message (Message): Incoming message with output state in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling toggle_output command: {message}")
        if not self.connected:
            self._push_error("-100,Power supply is not connected")
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            if "enable" in message.payload:
                self.output_enabled = bool(message.payload.get("enable"))
            else:
                self.output_enabled = not self.output_enabled
            self.interaction_counter += 1
            self._respond(message, {"output_enabled": self.output_enabled, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            self._push_error("-224,Invalid output command")
            self._respond(message, {"error": "Invalid output command"})
        return False

    def message_set_ovp(self, message: Message) -> bool:
        """Handle the "set_ovp" command - set over-voltage protection threshold.

        Args:
            message (Message): Incoming message with OVP threshold in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_ovp command: {message}")
        if not self.connected:
            self._push_error("-100,Power supply is not connected")
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            ovp = float(message.payload.get("threshold", 15.0))
            if ovp < 0.0 or ovp > 30.0:
                self._push_error(f"-225,OVP value out of range: {ovp}")
                self._respond(message, {"error": f"OVP value out of range: {ovp}"})
                return False
            self.ovp_threshold = ovp
            self.interaction_counter += 1
            self._respond(message, {"ovp_threshold": self.ovp_threshold, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            self._push_error("-225,Invalid OVP value")
            self._respond(message, {"error": "Invalid OVP value"})
        return False

    def message_set_ocp(self, message: Message) -> bool:
        """Handle the "set_ocp" command - set over-current protection threshold.

        Args:
            message (Message): Incoming message with OCP threshold in payload.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling set_ocp command: {message}")
        if not self.connected:
            self._push_error("-100,Power supply is not connected")
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            ocp = float(message.payload.get("threshold", 5.0))
            if ocp < 0.0 or ocp > 5.0:
                self._push_error(f"-226,OCP value out of range: {ocp}")
                self._respond(message, {"error": f"OCP value out of range: {ocp}"})
                return False
            self.ocp_threshold = ocp
            self.interaction_counter += 1
            self._respond(message, {"ocp_threshold": self.ocp_threshold, "status": "ok"})
        except (TypeError, ValueError, AttributeError):
            self._push_error("-226,Invalid OCP value")
            self._respond(message, {"error": "Invalid OCP value"})
        return False

    def message_measure(self, message: Message) -> bool:
        """Handle the "measure" command - measure voltage, current, and power.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling measure command: {message}")
        if not self.connected:
            self._respond(message, {
                "status": "not_connected",
                "connected": False,
                "output_enabled": False,
                "voltage": 0.0,
                "current": 0.0,
                "power": 0.0,
                "set_voltage": self.voltage,
                "set_current": self.current,
            })
            return False

        if not self.output_enabled:
            self._respond(message, {
                "status": "output_off",
                "connected": True,
                "output_enabled": False,
                "voltage": 0.0,
                "current": 0.0,
                "power": 0.0,
                "set_voltage": self.voltage,
                "set_current": self.current,
            })
            return False

        load_factor, voltage_factor = self._next_measurement_profile()
        measured_voltage = round(self.voltage * voltage_factor, 4)
        measured_current = round(self.current * load_factor, 4)
        measured_power = round(measured_voltage * measured_current, 4)

        # Simulate protection trip behavior.
        if measured_voltage > self.ovp_threshold or measured_current > self.ocp_threshold:
            self.output_enabled = False
            self._push_error("-350,Protection tripped")
            self._respond(message, {
                "status": "protection_tripped",
                "connected": True,
                "output_enabled": False,
                "voltage": 0.0,
                "current": 0.0,
                "power": 0.0,
                "set_voltage": self.voltage,
                "set_current": self.current,
                "ovp_threshold": self.ovp_threshold,
                "ocp_threshold": self.ocp_threshold,
            })
            return False

        self._respond(message, {
            "status": "ok",
            "connected": True,
            "output_enabled": True,
            "voltage": measured_voltage,
            "current": measured_current,
            "power": measured_power,
            "set_voltage": self.voltage,
            "set_current": self.current,
            "ovp_threshold": self.ovp_threshold,
            "ocp_threshold": self.ocp_threshold,
            "load_factor": round(load_factor, 4),
        })
        return False

    def message_reset(self, message: Message) -> bool:
        """Handle the "reset" command - reset operating state to defaults."""
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling reset command: {message}")

        self.voltage = 0.0
        self.current = 0.0
        self.output_enabled = False
        self.ovp_threshold = 15.0
        self.ocp_threshold = 5.0
        self.measurement_counter = 0
        self.interaction_counter += 1
        self.error_queue.clear()

        self._respond(message, {
            "status": "ok",
            "message": "instrument reset",
            "connected": self.connected,
            "output_enabled": self.output_enabled,
        })
        return False

    def message_error_query(self, message: Message) -> bool:
        """Handle the "error_query" command - return and clear oldest error."""
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling error_query command: {message}")

        if self.error_queue:
            error_text = self.error_queue.pop(0)
            self._respond(message, {
                "status": "error",
                "error": error_text,
                "queue_depth": len(self.error_queue),
            })
            return False

        self._respond(message, {
            "status": "ok",
            "error": "0,No error",
            "queue_depth": 0,
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
