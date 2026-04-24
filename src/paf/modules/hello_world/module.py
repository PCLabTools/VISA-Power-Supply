"""
file: module.py
description: HelloWorld example module
author: Your Name (your.email@example.com)
"""

from time import sleep
from typing import Optional
from paf.communication import Message, Protocol, Module


class HelloWorld(Module):
    """
    HelloWorld example module
    """

    def __init__(self, address: str, protocol: Protocol, debug: Optional[int] = 0):
        """Initialises the module and sets up the protocol.

        Args:
            address (str): The address of the module.
            protocol (Protocol): The protocol instance.
            debug (Optional[int]): Debug level (default is 0).
        """
        self.debug = debug
        super().__init__(address, protocol)

    def handle_message(self, message: Message) -> bool:
        """Handle incoming messages.

        Args:
            message (Message): The message to handle.

        Returns:
            bool: True if the module should shutdown, False otherwise.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling message: {message}")
        if message.command == "greet":
            return self.greet(message)
        return super().handle_message(message)

    def background_task(self):
        """Background task that runs while the module is active."""
        while self.background_task_running:
            if self.debug: print(f"{self.__class__.__name__} ({self.address}): Running background task.")
            # TODO: implement background task logic
            sleep(1)

    def greet(self, message: Message) -> bool:
        """Handles the "greet" message.

        Args:
            message (Message): Incoming message to handle.

        Returns:
            bool: False to indicate that the module should continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling greet message: {message}")
        self.protocol.send_response(message, {"response": "Hello, World!"})
        return False
