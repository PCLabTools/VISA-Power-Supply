"""
Unit tests for the PowerSupplyFrontPanel class
"""
import unittest
import time
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Protocol, Message, Module
from paf.modules.power_supply_front_panel.module import PowerSupplyFrontPanel, PowerSupplyRequestHandler


class _FakeProtocol:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def send_request(self, *_args, **_kwargs):
        if self._error is not None:
            raise self._error
        return self._response


class _FakeServer:
    def __init__(self, protocol):
        self.protocol = protocol
        self.power_supply_address = "visa_power_supply"
        self.debug = 0


class TestPowerSupplyFrontPanel(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.protocol = Protocol()

    def tearDown(self):
        """Clean up test fixtures"""
        # Send shutdown to all registered modules to stop their threads
        for module_name in self.protocol.get_registered_modules():
            try:
                self.protocol.send_action(module_name, "shutdown")
            except:
                pass
        # Wait for threads to fully terminate
        time.sleep(0.5)
        # Clean up any registered modules
        for module_name in list(self.protocol.get_registered_modules()):
            try:
                self.protocol.unregister_module(module_name)
            except:
                pass
        del self.protocol

    def test_init(self):
        """Test PowerSupplyFrontPanel initialization"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)
        self.assertEqual(module.address, "test_power_supply_front_panel")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_power_supply_front_panel", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_init_with_debug(self):
        """Test PowerSupplyFrontPanel initialization with debug enabled"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel_debug", self.protocol, debug=1)
        self.assertEqual(module.debug, 1)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel_debug", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_custom_action(self):
        """Test handle_message with custom_action command"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)
        msg = Message("test_power_supply_front_panel", "custom_action", {"key": "value"})

        result = module.handle_message(msg)
        self.assertFalse(result)  # Should return False to continue running

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_message_custom_action(self):
        """Test message_custom_action method directly"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)
        msg = Message("test_power_supply_front_panel", "custom_action", {"data": "test"})

        result = module.message_custom_action(msg)
        self.assertFalse(result)  # Returns False

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_unknown(self):
        """Test handle_message with unknown command raises NotImplementedError"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)
        msg = Message("test_power_supply_front_panel", "unknown_command")

        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_background_task_running(self):
        """Test background task runs when enabled"""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        # Start background task
        self.protocol.send_action("test_power_supply_front_panel", "start")
        time.sleep(0.2)  # Give it time to start

        self.assertTrue(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_start(self):
        """Test start command begins background task."""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        # Initially background task should not be running
        self.assertFalse(module.background_task_running)

        # Send start command
        self.protocol.send_action("test_power_supply_front_panel", "start")
        time.sleep(0.2)  # Allow time for start to process

        # Background task should now be running
        self.assertTrue(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_stop(self):
        """Test stop command halts background task."""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        # Start the background task
        self.protocol.send_action("test_power_supply_front_panel", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)

        # Send stop command
        self.protocol.send_action("test_power_supply_front_panel", "stop")
        time.sleep(0.2)

        # Background task should now be stopped
        self.assertFalse(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_not_running(self):
        """Test status command reports correct state when not running."""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        response = self.protocol.send_request("test_power_supply_front_panel", "status", timeout=1.0)
        self.assertIn("not running", response)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_running(self):
        """Test status command reports correct state when running."""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        # Start background task
        self.protocol.send_action("test_power_supply_front_panel", "start")
        time.sleep(0.2)

        response = self.protocol.send_request("test_power_supply_front_panel", "status", timeout=1.0)
        self.assertIn("running", response)

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles work correctly (validates thread pooling fix)."""
        module = PowerSupplyFrontPanel("test_power_supply_front_panel", self.protocol, debug=0)

        # Cycle start/stop multiple times to ensure thread pooling works
        for i in range(3):
            self.protocol.send_action("test_power_supply_front_panel", "start")
            time.sleep(0.2)
            self.assertTrue(module.background_task_running, f"Background task should be running on iteration {i}")

            self.protocol.send_action("test_power_supply_front_panel", "stop")
            time.sleep(0.2)
            self.assertFalse(module.background_task_running, f"Background task should be stopped on iteration {i}")

        # Clean up
        self.protocol.send_action("test_power_supply_front_panel", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_power_supply_command_uses_dict_response(self):
        """Test handler returns dict payloads directly from protocol.send_request."""
        handler = PowerSupplyRequestHandler.__new__(PowerSupplyRequestHandler)
        handler.server = _FakeServer(_FakeProtocol(response={"status": "ok", "voltage": 12.0}))

        result = handler.handle_power_supply_command("measure", {})

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["voltage"], 12.0)

    def test_handle_power_supply_command_timeout_returns_status_tuple(self):
        """Test handler maps protocol timeouts to 504 responses."""
        handler = PowerSupplyRequestHandler.__new__(PowerSupplyRequestHandler)
        handler.server = _FakeServer(_FakeProtocol(error=TimeoutError()))

        result = handler.handle_power_supply_command("measure", {})

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[1], 504)
        self.assertEqual(result[0]["error"], "Power supply module timeout")


if __name__ == '__main__':
    unittest.main()
