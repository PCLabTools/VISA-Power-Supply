"""
Unit tests for the HelloWorld class
"""
import unittest
import time
import sys
import os
from queue import PriorityQueue

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from paf.communication import Protocol, Message
from paf.modules.hello_world.module import HelloWorld


class TestHelloWorld(unittest.TestCase):

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
        """Test HelloWorld initialization"""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        self.assertEqual(module.address, "test_hello_world")
        self.assertEqual(module.protocol, self.protocol)
        self.assertEqual(module.debug, 0)
        self.assertIn("test_hello_world", self.protocol.registered_modules)
        self.assertTrue(module.thread.is_alive())
        self.assertFalse(module.background_task_running)

        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_init_with_debug(self):
        """Test HelloWorld initialization with debug enabled"""
        module = HelloWorld("test_hello_world_debug", self.protocol, debug=1)
        self.assertEqual(module.debug, 1)

        # Clean up
        self.protocol.send_action("test_hello_world_debug", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_greet_via_request(self):
        """Test greet command returns expected response through protocol."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)

        response = self.protocol.send_request("test_hello_world", "greet", timeout=1.0)
        self.assertEqual(response, {"response": "Hello, World!"})

        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_greet_method_direct(self):
        """Test greet method sends response and keeps module running."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        response_queue = PriorityQueue()
        msg = Message("test_hello_world", "greet", source=response_queue)

        result = module.greet(msg)
        self.assertFalse(result)

        _, response = response_queue.get(timeout=1.0)
        self.assertEqual(response, {"response": "Hello, World!"})

        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_unknown(self):
        """Test handle_message with unknown command raises NotImplementedError"""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        msg = Message("test_hello_world", "unknown_command")

        with self.assertRaises(NotImplementedError):
            module.handle_message(msg)

        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_start(self):
        """Test start command begins background task."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        
        # Initially background task should not be running
        self.assertFalse(module.background_task_running)
        
        # Send start command
        self.protocol.send_action("test_hello_world", "start")
        time.sleep(0.2)  # Allow time for start to process
        
        # Background task should now be running
        self.assertTrue(module.background_task_running)
        
        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_stop(self):
        """Test stop command halts background task."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        
        # Start the background task
        self.protocol.send_action("test_hello_world", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)
        
        # Send stop command
        self.protocol.send_action("test_hello_world", "stop")
        time.sleep(0.2)
        
        # Background task should now be stopped
        self.assertFalse(module.background_task_running)
        
        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_not_running(self):
        """Test status command reports correct state when not running."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        
        response = self.protocol.send_request("test_hello_world", "status", timeout=1.0)
        self.assertIn("not running", response)
        
        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_handle_message_status_running(self):
        """Test status command reports correct state when running."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        
        # Start background task
        self.protocol.send_action("test_hello_world", "start")
        time.sleep(0.2)
        
        response = self.protocol.send_request("test_hello_world", "status", timeout=1.0)
        self.assertIn("running", response)
        
        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_start_stop_cycle(self):
        """Test multiple start/stop cycles work correctly (validates thread pooling fix)."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)
        
        # Cycle start/stop multiple times to ensure thread pooling works
        for i in range(3):
            self.protocol.send_action("test_hello_world", "start")
            time.sleep(0.2)
            self.assertTrue(module.background_task_running, f"Background task should be running on iteration {i}")
            
            self.protocol.send_action("test_hello_world", "stop")
            time.sleep(0.2)
            self.assertFalse(module.background_task_running, f"Background task should be stopped on iteration {i}")
        
        # Clean up
        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_start_stop_background_task(self):
        """Test start and stop commands toggle background task state."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)

        self.protocol.send_action("test_hello_world", "start")
        time.sleep(0.2)
        self.assertTrue(module.background_task_running)

        self.protocol.send_action("test_hello_world", "stop")
        time.sleep(1.2)
        self.assertFalse(module.background_task_running)

        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)

    def test_status_reports_running_state(self):
        """Test status command returns expected module state string."""
        module = HelloWorld("test_hello_world", self.protocol, debug=0)

        status = self.protocol.send_request("test_hello_world", "status", timeout=1.0)
        self.assertEqual(status, "Module test_hello_world is not running")

        self.protocol.send_action("test_hello_world", "shutdown")
        module.thread.join(timeout=1.0)
