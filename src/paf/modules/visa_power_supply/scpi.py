"""
file: scpi.py
description: SCPI (Standard Commands for Programmable Instruments) implementation of VISAPowerSupply.
             Uses pyvisa as the communication layer to send/receive IEEE 488.2-compliant SCPI commands
             to a real instrument over any VISA transport (GPIB, USB, TCP/IP, Serial).
author: Your Name (your.email@example.com)
"""

from time import sleep
from typing import Optional
import pyvisa
from paf.communication import Message
from .module import VISAPowerSupply, BaseVISAPowerSupply


class SCPIVISAPowerSupply(BaseVISAPowerSupply):
    """SCPI implementation of VISAPowerSupply.

    Communicates with a real instrument using pyvisa and standard SCPI commands.
    The VISA resource string (e.g. "GPIB0::5::INSTR", "USB0::...::INSTR",
    "TCPIP0::192.168.1.10::inst0::INSTR") must be supplied in the "connect"
    message payload under the key "resource".
    """

    def __init__(self, address: str, protocol, debug: int = 0):
        """Initialise the SCPI implementation.

        Args:
            address (str): Module address.
            protocol: Protocol instance.
            debug (int): Debug level.
        """
        self.debug = debug
        self._resource: Optional[pyvisa.resources.Resource] = None
        self._resource_manager: Optional[pyvisa.ResourceManager] = None
        self._resource_string: Optional[str] = None
        super().__init__(address, protocol, debug)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _respond(self, message: Message, payload: dict) -> None:
        """Send a response only when the message originated from send_request."""
        if message.source:
            self.protocol.send_response(message, payload)

    def _query(self, command: str) -> str:
        """Send a SCPI query and return the stripped response string.

        Args:
            command (str): SCPI query string (e.g. "*IDN?").

        Returns:
            str: Instrument response stripped of whitespace.

        Raises:
            pyvisa.VisaIOError: On communication failure.
        """
        return self._resource.query(command).strip()

    def _write(self, command: str) -> None:
        """Send a SCPI command with no response expected.

        Args:
            command (str): SCPI command string (e.g. "OUTP ON").

        Raises:
            pyvisa.VisaIOError: On communication failure.
        """
        self._resource.write(command)

    def _connected(self) -> bool:
        return self._resource is not None

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def background_task(self):
        """Background task — idle loop; real-time polling can be added here."""
        while self.background_task_running:
            if self.debug:
                print(f"{self.__class__.__name__} ({self.address}): Background task running.")
            sleep(1)

    def message_connect(self, message: Message) -> bool:
        """Connect to the instrument using the VISA resource string in the payload.

        Expected payload keys:
            resource (str): VISA resource string (required).
            timeout (int, optional): Communication timeout in ms. Defaults to 5000.

        SCPI commands issued:
            *CLS  — clear status registers and error queue.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling connect command: {message}")
        resource_string = message.payload.get("resource")
        if not resource_string:
            self._respond(message, {"error": "Missing 'resource' key in payload"})
            return False
        timeout_ms = int(message.payload.get("timeout", 5000))
        try:
            self._resource_manager = pyvisa.ResourceManager()
            self._resource = self._resource_manager.open_resource(resource_string)
            self._resource.timeout = timeout_ms
            self._resource_string = resource_string
            # Clear any pre-existing errors and event registers.
            self._write("*CLS")
            # Identify the instrument to return useful metadata.
            idn = self._query("*IDN?")
            self._respond(message, {
                "status": "connected",
                "model": idn,
                "resource": resource_string,
            })
        except pyvisa.VisaIOError as exc:
            self._resource = None
            self._resource_manager = None
            self._resource_string = None
            self._respond(message, {"error": f"VISA connection failed: {exc}"})
        return False

    def message_disconnect(self, message: Message) -> bool:
        """Disconnect from the instrument.

        SCPI commands issued:
            OUTP OFF  — disable output before closing (best practice).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling disconnect command: {message}")
        if not self._connected():
            self._respond(message, {"status": "disconnected"})
            return False
        try:
            self._write("OUTP OFF")
        except pyvisa.VisaIOError:
            pass  # Best-effort; proceed to close regardless.
        try:
            self._resource.close()
        except pyvisa.VisaIOError:
            pass
        self._resource = None
        self._resource_manager = None
        self._resource_string = None
        self._respond(message, {"status": "disconnected"})
        return False

    def message_identify(self, message: Message) -> bool:
        """Identify the instrument.

        SCPI commands issued:
            *IDN?                      — manufacturer, model, serial, firmware.
            SYST:ERR:COUN? (optional)  — check error count (omitted if unsupported).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling identify command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            idn = self._query("*IDN?")
            parts = [p.strip() for p in idn.split(",")]
            self._respond(message, {
                "model": idn,
                "manufacturer": parts[0] if len(parts) > 0 else "",
                "model_number": parts[1] if len(parts) > 1 else "",
                "serial_number": parts[2] if len(parts) > 2 else "",
                "firmware": parts[3] if len(parts) > 3 else "",
                "connected": True,
            })
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error during identify: {exc}"})
        return False

    def message_set_voltage(self, message: Message) -> bool:
        """Set the output voltage setpoint.

        Expected payload keys:
            voltage (float): Target voltage in Volts.

        SCPI commands issued:
            VOLT <value>  — set voltage setpoint (SOUR:VOLT <value> if source subsystem required).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling set_voltage command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            voltage = float(message.payload.get("voltage", 0.0))
            self._write(f"VOLT {voltage:.4f}")
            # Read back the actual setpoint to confirm.
            actual = float(self._query("VOLT?"))
            self._respond(message, {"voltage": actual, "status": "ok"})
        except (TypeError, ValueError):
            self._respond(message, {"error": "Invalid voltage value"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False

    def message_set_current(self, message: Message) -> bool:
        """Set the output current limit.

        Expected payload keys:
            current (float): Current limit in Amps.

        SCPI commands issued:
            CURR <value>  — set current limit (SOUR:CURR <value> if source subsystem required).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling set_current command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            current = float(message.payload.get("current", 0.0))
            self._write(f"CURR {current:.4f}")
            actual = float(self._query("CURR?"))
            self._respond(message, {"current": actual, "status": "ok"})
        except (TypeError, ValueError):
            self._respond(message, {"error": "Invalid current value"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False

    def message_toggle_output(self, message: Message) -> bool:
        """Enable or disable the power supply output.

        Expected payload keys:
            enable (bool, optional): True to enable, False to disable.
                                     If omitted, the output state is toggled
                                     by querying the current state first.

        SCPI commands issued:
            OUTP?       — query current output state (when toggling).
            OUTP ON|OFF — set output state.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling toggle_output command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            if "enable" in message.payload:
                enable = bool(message.payload["enable"])
            else:
                # Query and flip the current state.
                current_state = self._query("OUTP?")
                enable = current_state.strip() in ("0", "OFF", "0\n")
            self._write(f"OUTP {'ON' if enable else 'OFF'}")
            actual_state = self._query("OUTP?")
            output_enabled = actual_state.strip() in ("1", "ON")
            self._respond(message, {"output_enabled": output_enabled, "status": "ok"})
        except (TypeError, ValueError):
            self._respond(message, {"error": "Invalid output command"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False

    def message_set_ovp(self, message: Message) -> bool:
        """Set the over-voltage protection (OVP) threshold and enable OVP.

        Expected payload keys:
            threshold (float): OVP level in Volts.

        SCPI commands issued:
            VOLT:PROT <value>  — set OVP trip level.
            VOLT:PROT:STAT ON  — enable OVP.
            VOLT:PROT?         — read back actual OVP setpoint.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling set_ovp command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            threshold = float(message.payload.get("threshold", 15.0))
            self._write(f"VOLT:PROT {threshold:.4f}")
            self._write("VOLT:PROT:STAT ON")
            actual = float(self._query("VOLT:PROT?"))
            self._respond(message, {"ovp_threshold": actual, "status": "ok"})
        except (TypeError, ValueError):
            self._respond(message, {"error": "Invalid OVP value"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False

    def message_set_ocp(self, message: Message) -> bool:
        """Set the over-current protection (OCP) threshold and enable OCP.

        Expected payload keys:
            threshold (float): OCP level in Amps.

        SCPI commands issued:
            CURR:PROT <value>  — set OCP trip level.
            CURR:PROT:STAT ON  — enable OCP.
            CURR:PROT?         — read back actual OCP setpoint.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling set_ocp command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            threshold = float(message.payload.get("threshold", 5.0))
            self._write(f"CURR:PROT {threshold:.4f}")
            self._write("CURR:PROT:STAT ON")
            actual = float(self._query("CURR:PROT?"))
            self._respond(message, {"ocp_threshold": actual, "status": "ok"})
        except (TypeError, ValueError):
            self._respond(message, {"error": "Invalid OCP value"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False

    def message_measure(self, message: Message) -> bool:
        """Measure output voltage, current, and power.

        SCPI commands issued:
            MEAS:VOLT?   — measure output voltage.
            MEAS:CURR?   — measure output current.
            VOLT?        — query voltage setpoint.
            CURR?        — query current setpoint.
            OUTP?        — query output state.
            MEAS:POW?    — measure power (used when supported; calculated fallback otherwise).
            STAT:QUES?   — questionable status register (detect protection trip condition).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling measure command: {message}")
        if not self._connected():
            self._respond(message, {
                "status": "not_connected",
                "connected": False,
                "output_enabled": False,
                "voltage": 0.0,
                "current": 0.0,
                "power": 0.0,
            })
            return False
        try:
            output_state_raw = self._query("OUTP?").strip()
            output_enabled = output_state_raw in ("1", "ON")

            set_voltage = float(self._query("VOLT?"))
            set_current = float(self._query("CURR?"))

            if not output_enabled:
                self._respond(message, {
                    "status": "output_off",
                    "connected": True,
                    "output_enabled": False,
                    "voltage": 0.0,
                    "current": 0.0,
                    "power": 0.0,
                    "set_voltage": set_voltage,
                    "set_current": set_current,
                })
                return False

            measured_voltage = float(self._query("MEAS:VOLT?"))
            measured_current = float(self._query("MEAS:CURR?"))

            # Attempt power measurement; fall back to calculated value.
            try:
                measured_power = float(self._query("MEAS:POW?"))
            except (pyvisa.VisaIOError, ValueError):
                measured_power = round(measured_voltage * measured_current, 4)

            # Check questionable status register for protection-tripped condition.
            # Bit 0 = voltage unregulated, Bit 1 = current unregulated (OCP/OVP tripped).
            try:
                ques_status = int(self._query("STAT:QUES?"))
            except (pyvisa.VisaIOError, ValueError):
                ques_status = 0

            if ques_status & 0x03:  # Bits 0 or 1 indicate regulation failure.
                self._respond(message, {
                    "status": "protection_tripped",
                    "connected": True,
                    "output_enabled": output_enabled,
                    "voltage": round(measured_voltage, 4),
                    "current": round(measured_current, 4),
                    "power": round(measured_power, 4),
                    "set_voltage": set_voltage,
                    "set_current": set_current,
                })
                return False

            self._respond(message, {
                "status": "ok",
                "connected": True,
                "output_enabled": True,
                "voltage": round(measured_voltage, 4),
                "current": round(measured_current, 4),
                "power": round(measured_power, 4),
                "set_voltage": set_voltage,
                "set_current": set_current,
            })
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error during measure: {exc}"})
        return False

    def message_reset(self, message: Message) -> bool:
        """Reset the instrument to its power-on defaults.

        SCPI commands issued:
            *RST  — reset to factory defaults.
            *CLS  — clear status registers and error queue.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling reset command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        try:
            self._write("*RST")
            self._write("*CLS")
            self._respond(message, {
                "status": "ok",
                "message": "instrument reset",
                "connected": True,
            })
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error during reset: {exc}"})
        return False

    def message_error_query(self, message: Message) -> bool:
        """Query and dequeue the oldest error from the instrument error queue.

        SCPI commands issued:
            SYST:ERR?  — returns "code,message" (e.g. "-110,Command error").
                         Returns "0,No error" when the queue is empty.
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling error_query command: {message}")
        if not self._connected():
            self._respond(message, {
                "status": "ok",
                "error": "0,No error",
                "queue_depth": 0,
            })
            return False
        try:
            error_string = self._query("SYST:ERR?")
            # SCPI error format: "<signed-integer>,<quoted-string>"
            # e.g. '-110,"Command error"' or '0,"No error"'
            code_part = error_string.split(",", 1)[0].strip()
            try:
                code = int(code_part)
            except ValueError:
                code = 0
            if code == 0:
                self._respond(message, {
                    "status": "ok",
                    "error": "0,No error",
                    "queue_depth": 0,
                })
            else:
                self._respond(message, {
                    "status": "error",
                    "error": error_string,
                    "queue_depth": None,  # SCPI does not expose queue depth natively.
                })
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error during error_query: {exc}"})
        return False

    def message_list_resources(self, message: Message) -> bool:
        """Enumerate VISA resources visible to the local VISA resource manager.

        Uses pyvisa's ResourceManager.list_resources() which returns all
        instruments detected across all installed VISA backends (NI-VISA,
        R&S VISA, Keysight IO Libraries, etc.).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling list_resources command: {message}")
        try:
            rm = pyvisa.ResourceManager()
            resources = list(rm.list_resources())
            self._respond(message, {"resources": resources})
        except Exception as exc:
            self._respond(message, {"error": f"Failed to list VISA resources: {exc}", "resources": []})
        return False

    def message_custom_action(self, message: Message) -> bool:
        """Send a raw SCPI command or query to the instrument.

        Expected payload keys:
            command (str): Raw SCPI string to send (required).
            query (bool, optional): If True, send as a query and return response.
                                    Defaults to False (write only).
        """
        if self.debug:
            print(f"{self.__class__.__name__} ({self.address}): Handling custom_action command: {message}")
        if not self._connected():
            self._respond(message, {"error": "Power supply is not connected"})
            return False
        scpi_command = message.payload.get("command")
        if not scpi_command:
            self._respond(message, {"error": "Missing 'command' key in payload"})
            return False
        is_query = bool(message.payload.get("query", False))
        try:
            if is_query:
                response = self._query(scpi_command)
                self._respond(message, {"response": response, "status": "ok"})
            else:
                self._write(scpi_command)
                self._respond(message, {"status": "ok"})
        except pyvisa.VisaIOError as exc:
            self._respond(message, {"error": f"VISA error: {exc}"})
        return False


VISAPowerSupply.register("scpi", SCPIVISAPowerSupply)
