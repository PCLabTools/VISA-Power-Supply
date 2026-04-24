"""Unit tests for {{ClassName}} and its simulated implementation."""

import os
import sys
import time
import unittest

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Message, Protocol
from paf.modules.{{module_name}} import (
    Base{{ClassName}},
    {{ClassName}},
    Simulated{{ClassName}},
)


class Dummy{{ClassName}}(Base{{ClassName}}):
    """Concrete test implementation used to validate factory registration."""

    def background_task(self):
        while self.background_task_running:
            time.sleep(0.01)

    def message_custom_action(self, message: Message) -> bool:
        return False


class Test{{ClassName}}(unittest.TestCase):
    """Tests for the {{ClassName}} factory module."""

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
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)

        self.assertIsInstance(module, Simulated{{ClassName}})
        self.assertEqual(module.address, "test_{{module_name}}")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_{{module_name}}", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

    def test_create_with_registered_implementation(self):
        {{ClassName}}.register("dummy", Dummy{{ClassName}})

        module = {{ClassName}}.create(
            "test_dummy",
            self.protocol,
            debug=1,
            implementation_type="DUMMY",
        )
        self.created_modules.append(module)

        self.assertIsInstance(module, Dummy{{ClassName}})
        self.assertEqual(module.debug, 1)

    def test_create_invalid_implementation_raises_value_error(self):
        with self.assertRaises(ValueError):
            {{ClassName}}.create("invalid_{{module_name}}", self.protocol, implementation_type="missing")

    def test_handle_message_custom_action(self):
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_{{module_name}}", "custom_action", {"key": "value"})

        result = module.handle_message(msg)
        self.assertFalse(result)

    def test_message_custom_action(self):
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_{{module_name}}", "custom_action", {"data": "test"})

        result = module.message_custom_action(msg)
        self.assertFalse(result)

    def test_handle_message_unknown(self):
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        msg = Message("test_{{module_name}}", "unknown_command")

        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)

    def test_background_task_running(self):
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)

        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)

        self.assertTrue(module.background_task_running)

    def test_handle_message_start(self):
        """Test start command begins background task."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        
        # Initially background task should not be running
        self.assertFalse(module.background_task_running)
        
        # Send start command
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)  # Allow time for start to process
        
        # Background task should now be running
        self.assertTrue(module.background_task_running)

    def test_handle_message_stop(self):
        """Test stop command halts background task."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        
        # Start the background task
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)
        
        # Send stop command
        self.protocol.send_action("test_{{module_name}}", "stop")
        time.sleep(0.2)
        
        # Background task should now be stopped
        self.assertFalse(module.background_task_running)

    def test_handle_message_status_not_running(self):
        """Test status command reports correct state when not running."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        
        response = self.protocol.send_request("test_{{module_name}}", "status", timeout=1.0)
        self.assertIn("not running", response)

    def test_handle_message_status_running(self):
        """Test status command reports correct state when running."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        
        # Start background task
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)
        
        response = self.protocol.send_request("test_{{module_name}}", "status", timeout=1.0)
        self.assertIn("running", response)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles work correctly (validates thread pooling fix)."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.created_modules.append(module)
        
        # Cycle start/stop multiple times to ensure thread pooling works
        for i in range(3):
            self.protocol.send_action("test_{{module_name}}", "start")
            time.sleep(0.2)
            self.assertTrue(module.background_task_running, f"Background task should be running on iteration {i}")
            
            self.protocol.send_action("test_{{module_name}}", "stop")
            time.sleep(0.2)
            self.assertFalse(module.background_task_running, f"Background task should be stopped on iteration {i}")


if __name__ == '__main__':
    unittest.main()
