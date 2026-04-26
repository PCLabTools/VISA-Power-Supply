"""Unit tests for VISAPowerSupply and its simulated implementation."""

import os
import sys
import time
import unittest

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Message, Protocol
from paf.modules.visa_power_supply import (
    BaseVISAPowerSupply,
    VISAPowerSupply,
    SimulatedVISAPowerSupply,
)


class DummyVISAPowerSupply(BaseVISAPowerSupply):
    """Concrete test implementation used to validate factory registration."""

    def background_task(self):
        while self.background_task_running:
            time.sleep(0.01)

    def message_connect(self, message: Message) -> bool:
        return False

    def message_disconnect(self, message: Message) -> bool:
        return False

    def message_identify(self, message: Message) -> bool:
        return False

    def message_set_voltage(self, message: Message) -> bool:
        return False

    def message_set_current(self, message: Message) -> bool:
        return False

    def message_toggle_output(self, message: Message) -> bool:
        return False

    def message_set_ovp(self, message: Message) -> bool:
        return False

    def message_set_ocp(self, message: Message) -> bool:
        return False

    def message_measure(self, message: Message) -> bool:
        return False

    def message_reset(self, message: Message) -> bool:
        return False

    def message_error_query(self, message: Message) -> bool:
        return False

    def message_custom_action(self, message: Message) -> bool:
        return False


class TestVISAPowerSupply(unittest.TestCase):
    """Tests for the VISAPowerSupply factory module."""

    def setUp(self):
        self.protocol = Protocol()
        self.created_modules = []

    def tearDown(self):
        for module in self.created_modules:
            try:
                if module.background_task_running:
                    self.protocol.send_action(module.address, "stop")
                    time.sleep(0.1)
            except Exception:
                pass
            try:
                self.protocol.send_action(module.address, "shutdown")
            except Exception:
                pass
            try:
                module.thread.join(timeout=1.0)
            except Exception:
                pass

        # Wait for threads to fully terminate
        time.sleep(0.5)

        for module_name in list(self.protocol.get_registered_modules()):
            try:
                self.protocol.unregister_module(module_name)
            except Exception:
                pass

    def test_create_returns_simulated_by_default(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.assertIsInstance(module, SimulatedVISAPowerSupply)
        self.assertEqual(module.address, "test_visa_power_supply")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_visa_power_supply", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

    def test_create_with_registered_implementation(self):
        VISAPowerSupply.register("dummy", DummyVISAPowerSupply)

        module = VISAPowerSupply.create(
            "test_dummy",
            self.protocol,
            debug=1,
            implementation_type="DUMMY",
        )
        self.created_modules.append(module)

        self.assertIsInstance(module, DummyVISAPowerSupply)
        self.assertEqual(module.debug, 1)

    def test_create_invalid_implementation_raises_value_error(self):
        with self.assertRaises(ValueError):
            VISAPowerSupply.create("invalid_visa_power_supply", self.protocol, implementation_type="missing")

    def test_handle_message_custom_action(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_visa_power_supply", "custom_action", {"key": "value"})

        result = module.handle_message(msg)
        self.assertFalse(result)

    def test_message_custom_action(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_visa_power_supply", "custom_action", {"data": "test"})

        result = module.message_custom_action(msg)
        self.assertFalse(result)

    def test_handle_message_unknown(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_visa_power_supply", "unknown_command")

        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)

    def test_background_task_running(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_action("test_visa_power_supply", "start")
        time.sleep(0.2)

        self.assertTrue(module.background_task_running)

    def test_handle_message_start(self):
        """Test start command begins background task."""
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        # Initially background task should not be running
        self.assertFalse(module.background_task_running)

        # Send start command
        self.protocol.send_action("test_visa_power_supply", "start")
        time.sleep(0.2)  # Allow time for start to process

        # Background task should now be running
        self.assertTrue(module.background_task_running)

    def test_handle_message_stop(self):
        """Test stop command halts background task."""
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        # Start the background task
        self.protocol.send_action("test_visa_power_supply", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)

        # Send stop command
        self.protocol.send_action("test_visa_power_supply", "stop")
        time.sleep(0.2)

        # Background task should now be stopped
        self.assertFalse(module.background_task_running)

    def test_handle_message_status_not_running(self):
        """Test status command reports correct state when not running."""
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        response = self.protocol.send_request("test_visa_power_supply", "status", timeout=1.0)
        self.assertIn("not running", response)

    def test_handle_message_status_running(self):
        """Test status command reports correct state when running."""
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        # Start background task
        self.protocol.send_action("test_visa_power_supply", "start")
        time.sleep(0.2)

        response = self.protocol.send_request("test_visa_power_supply", "status", timeout=1.0)
        self.assertIn("running", response)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles work correctly (validates thread pooling fix)."""
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        # Cycle start/stop multiple times to ensure thread pooling works
        for i in range(3):
            self.protocol.send_action("test_visa_power_supply", "start")
            time.sleep(0.2)
            self.assertTrue(module.background_task_running, f"Background task should be running on iteration {i}")

            self.protocol.send_action("test_visa_power_supply", "stop")
            time.sleep(0.2)
            self.assertFalse(module.background_task_running, f"Background task should be stopped on iteration {i}")

    def test_measure_reports_not_connected_when_disconnected(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        response = self.protocol.send_request("test_visa_power_supply", "measure", timeout=1.0)

        self.assertEqual(response["status"], "not_connected")
        self.assertFalse(response["connected"])
        self.assertEqual(response["voltage"], 0.0)
        self.assertEqual(response["current"], 0.0)
        self.assertEqual(response["power"], 0.0)

    def test_measure_reports_output_off_when_connected_but_disabled(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_request("test_visa_power_supply", "connect", timeout=1.0)
        response = self.protocol.send_request("test_visa_power_supply", "measure", timeout=1.0)

        self.assertEqual(response["status"], "output_off")
        self.assertTrue(response["connected"])
        self.assertFalse(response["output_enabled"])
        self.assertEqual(response["power"], 0.0)

    def test_measure_returns_simulated_values_when_output_enabled(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_request("test_visa_power_supply", "connect", timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_voltage", {"voltage": 12.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_current", {"current": 2.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "toggle_output", {"enable": True}, timeout=1.0)
        response = self.protocol.send_request("test_visa_power_supply", "measure", timeout=1.0)

        self.assertEqual(response["status"], "ok")
        self.assertTrue(response["connected"])
        self.assertTrue(response["output_enabled"])
        self.assertGreater(response["voltage"], 0.0)
        self.assertGreater(response["current"], 0.0)
        self.assertGreater(response["power"], 0.0)
        self.assertLessEqual(response["voltage"], 12.0)
        self.assertLessEqual(response["current"], 2.0)

    def test_measure_trips_protection_when_limits_exceeded(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_request("test_visa_power_supply", "connect", timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_voltage", {"voltage": 10.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_current", {"current": 1.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_ovp", {"threshold": 5.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "toggle_output", {"enable": True}, timeout=1.0)

        response = self.protocol.send_request("test_visa_power_supply", "measure", timeout=1.0)

        self.assertEqual(response["status"], "protection_tripped")
        self.assertFalse(response["output_enabled"])
        self.assertEqual(response["power"], 0.0)

    def test_reset_restores_default_operating_state(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_request("test_visa_power_supply", "connect", timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_voltage", {"voltage": 24.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_current", {"current": 3.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_ovp", {"threshold": 20.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "set_ocp", {"threshold": 2.0}, timeout=1.0)
        self.protocol.send_request("test_visa_power_supply", "toggle_output", {"enable": True}, timeout=1.0)

        reset_response = self.protocol.send_request("test_visa_power_supply", "reset", timeout=1.0)
        measure_response = self.protocol.send_request("test_visa_power_supply", "measure", timeout=1.0)

        self.assertEqual(reset_response["status"], "ok")
        self.assertFalse(reset_response["output_enabled"])
        self.assertEqual(measure_response["status"], "output_off")
        self.assertEqual(measure_response["set_voltage"], 0.0)
        self.assertEqual(measure_response["set_current"], 0.0)

    def test_error_query_returns_no_error_by_default(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        response = self.protocol.send_request("test_visa_power_supply", "error_query", timeout=1.0)

        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["error"], "0,No error")
        self.assertEqual(response["queue_depth"], 0)

    def test_error_query_returns_and_clears_oldest_error(self):
        module = VISAPowerSupply("test_visa_power_supply", self.protocol, debug=0)
        self.created_modules.append(module)

        # Generates a simulated error while disconnected.
        self.protocol.send_request("test_visa_power_supply", "set_voltage", {"voltage": 5.0}, timeout=1.0)

        first_query = self.protocol.send_request("test_visa_power_supply", "error_query", timeout=1.0)
        second_query = self.protocol.send_request("test_visa_power_supply", "error_query", timeout=1.0)

        self.assertEqual(first_query["status"], "error")
        self.assertIn("Power supply is not connected", first_query["error"])
        self.assertEqual(first_query["queue_depth"], 0)
        self.assertEqual(second_query["status"], "ok")
        self.assertEqual(second_query["error"], "0,No error")


if __name__ == '__main__':
    unittest.main()
