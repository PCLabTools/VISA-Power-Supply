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


if __name__ == '__main__':
    unittest.main()
