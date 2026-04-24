"""
Unit tests for the {{ClassName}} class
"""
import unittest
import time
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Protocol, Message, Module
from paf.modules.{{module_name}}.module import {{ClassName}}


class Test{{ClassName}}(unittest.TestCase):

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
        """Test {{ClassName}} initialization"""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        self.assertEqual(module.address, "test_{{module_name}}")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_{{module_name}}", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_init_with_debug(self):
        """Test {{ClassName}} initialization with debug enabled"""
        module = {{ClassName}}("test_{{module_name}}_debug", self.protocol, debug=1)
        self.assertEqual(module.debug, 1)

        # Clean up
        self.protocol.send_action("test_{{module_name}}_debug", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_custom_action(self):
        """Test handle_message with custom_action command"""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        msg = Message("test_{{module_name}}", "custom_action", {"key": "value"})

        result = module.handle_message(msg)
        self.assertFalse(result)  # Should return False to continue running

        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_message_custom_action(self):
        """Test message_custom_action method directly"""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        msg = Message("test_{{module_name}}", "custom_action", {"data": "test"})

        result = module.message_custom_action(msg)
        self.assertFalse(result)  # Returns False

        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_unknown(self):
        """Test handle_message with unknown command raises NotImplementedError"""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        msg = Message("test_{{module_name}}", "unknown_command")

        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)

        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_background_task_running(self):
        """Test background task runs when enabled"""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)

        # Start background task
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)  # Give it time to start

        self.assertTrue(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_start(self):
        """Test start command begins background task."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        
        # Initially background task should not be running
        self.assertFalse(module.background_task_running)
        
        # Send start command
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)  # Allow time for start to process
        
        # Background task should now be running
        self.assertTrue(module.background_task_running)
        
        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_stop(self):
        """Test stop command halts background task."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        
        # Start the background task
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)
        
        # Send stop command
        self.protocol.send_action("test_{{module_name}}", "stop")
        time.sleep(0.2)
        
        # Background task should now be stopped
        self.assertFalse(module.background_task_running)
        
        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_not_running(self):
        """Test status command reports correct state when not running."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        
        response = self.protocol.send_request("test_{{module_name}}", "status", timeout=1.0)
        self.assertIn("not running", response)
        
        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_running(self):
        """Test status command reports correct state when running."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        
        # Start background task
        self.protocol.send_action("test_{{module_name}}", "start")
        time.sleep(0.2)
        
        response = self.protocol.send_request("test_{{module_name}}", "status", timeout=1.0)
        self.assertIn("running", response)
        
        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles work correctly (validates thread pooling fix)."""
        module = {{ClassName}}("test_{{module_name}}", self.protocol, debug=0)
        
        # Cycle start/stop multiple times to ensure thread pooling works
        for i in range(3):
            self.protocol.send_action("test_{{module_name}}", "start")
            time.sleep(0.2)
            self.assertTrue(module.background_task_running, f"Background task should be running on iteration {i}")
            
            self.protocol.send_action("test_{{module_name}}", "stop")
            time.sleep(0.2)
            self.assertFalse(module.background_task_running, f"Background task should be stopped on iteration {i}")
        
        # Clean up
        self.protocol.send_action("test_{{module_name}}", "shutdown")
        module.thread.join(timeout=1.0)


if __name__ == '__main__':
    unittest.main()
