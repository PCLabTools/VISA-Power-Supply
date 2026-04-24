"""
file: main.py
description: Main entry point for the application.
author: Your Name (your.email@example.com)
"""

from paf.communication import Message, Protocol
from paf.modules import PowerSupplyFrontPanel, VISAPowerSupply

class Main:
    """
    Main class for the application.
    """

    def __init__(self):
        """Initialises the main class and sets up the protocol.
        """
        self.debug = 1
        self.address = "main"
        self.protocol = Protocol(self.address)

        PowerSupplyFrontPanel("power_supply_front_panel", self.protocol, debug=self.debug, power_supply_address="visa_power_supply", main_module_address=self.address)
        VISAPowerSupply("visa_power_supply", self.protocol, debug=self.debug, implementation_type="simulated")

    def __del__(self):
        """Clean up the main module by deleting the protocol instance.
        """
        del self.protocol

    def run(self):
        """Run the main application loop and handles application shutdown.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Starting main application loop.")

        self.protocol.send_action("visa_power_supply", "connect", {"address": self.address})

        self.protocol.send_action("power_supply_front_panel", "start")

        print(f"\033[92mPower supply control application running. Access it at http://localhost:5000. Press Ctrl+C to exit.\033[0m")

        while True:
            try:
                message = self.protocol.receive_message(self.address, timeout=0.2)
                if self.handle_message(message):
                    break
            except TimeoutError:
                continue
            except KeyboardInterrupt:
                if self.debug: print(f"{self.__class__.__name__} ({self.address}): Keyboard interrupt received. Shutting down.")
                self.protocol.broadcast_message("shutdown")
                break

    def handle_message(self, message: Message) -> bool:
        """Handle incoming messages.

        Args:
            message: The message to handle.

        Returns:
            bool: True if the message was handled successfully, False otherwise.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling message: {message}")
        if message.command == "shutdown":
            if self.debug: print(f"{self.__class__.__name__} ({self.address}): Received shutdown command. Shutting down.")
            self.protocol.send_action("visa_power_supply", "disconnect")
            self.protocol.broadcast_message("shutdown")
            try:
                self.protocol.receive_message(self.address, timeout=5)  # Wait for acknowledgments
            except TimeoutError:
                if self.debug: print(f"{self.__class__.__name__} ({self.address}): Timeout occurred while waiting for acknowledgments.")
            return True
        return False


if __name__ == "__main__":
    main = Main()
    main.run()