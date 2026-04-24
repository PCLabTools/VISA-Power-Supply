"""
file: module.py
description: This module is designed to abstract power supplies through the common PAF communication framework to enable a scalable library of real-world power supplies controlled in a unified manner.
author: Your Name (your.email@example.com)
"""

from typing import Optional
from abc import ABC, abstractmethod
from paf.communication import Message, Protocol, Module


class VISAPowerSupply:
    """Factory for creating VISAPowerSupply instances with swappable implementations at runtime.

    Raises:
        ValueError: When an invalid implementation type is specified.

    Returns:
        BaseVISAPowerSupply: An instance of the factory module based on the specified implementation type.
    """
    _implementations: dict[str, type["BaseVISAPowerSupply"]] = {}

    @classmethod
    def register(cls, implementation: str, module_class: type["BaseVISAPowerSupply"]):
        """Registers a factory implementation.

        Args:
            implementation (str): The name of the implementation.
            module_class (type[BaseVISAPowerSupply]): The class to register.
        """
        cls._implementations[implementation.lower()] = module_class

    @classmethod
    def create(cls, address: str, protocol: Protocol, debug: int = 0, implementation_type: str = "simulated") -> "BaseVISAPowerSupply":
        """Creates a factory module instance based on implementation type.

        Args:
            address (str): Unique address for the module.
            protocol (Protocol): The protocol instance.
            debug (int, optional): Debug level. Defaults to 0.
            implementation_type (str, optional): Implementation to create. Defaults to "simulated".

        Returns:
            BaseVISAPowerSupply: The created module instance.

        Raises:
            ValueError: If the specified implementation type is not registered.
        """
        implementation_type = implementation_type.lower()
        if implementation_type not in cls._implementations:
            raise ValueError(f"VISAPowerSupply: No factory implementation registered for type '{implementation_type}'")
        return cls._implementations[implementation_type](address, protocol, debug)

    def __new__(cls, address: str, protocol: Protocol, debug: int = 0, implementation_type: str = "simulated") -> "BaseVISAPowerSupply":
        return cls.create(address, protocol, debug, implementation_type)


class BaseVISAPowerSupply(Module, ABC):
    """Abstract base class for VISAPowerSupply implementations."""

    def __init__(self, address: str, protocol: Protocol, debug: Optional[int] = 0):
        """Initialises the factory module.

        Args:
            address (str): Unique address for the module.
            protocol (Protocol): The protocol instance.
            debug (int, optional): Debug level. Defaults to 0.
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
        # Route to appropriate command handler
        if message.command == "connect":
            return self.message_connect(message)
        elif message.command == "disconnect":
            return self.message_disconnect(message)
        elif message.command == "identify":
            return self.message_identify(message)
        elif message.command == "set_voltage":
            return self.message_set_voltage(message)
        elif message.command == "set_current":
            return self.message_set_current(message)
        elif message.command == "toggle_output":
            return self.message_toggle_output(message)
        elif message.command == "set_ovp":
            return self.message_set_ovp(message)
        elif message.command == "set_ocp":
            return self.message_set_ocp(message)
        elif message.command == "measure":
            return self.message_measure(message)
        elif message.command == "custom_action":
            return self.message_custom_action(message)
        return super().handle_message(message)

    # Required action handlers
    @abstractmethod
    def message_connect(self, message: Message) -> bool:
        """Handle the "connect" command - establish connection to power supply.

        Args:
            message (Message): Incoming message with connection parameters.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_connect must be implemented by subclasses")

    @abstractmethod
    def message_disconnect(self, message: Message) -> bool:
        """Handle the "disconnect" command - disconnect from power supply.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_disconnect must be implemented by subclasses")

    @abstractmethod
    def message_identify(self, message: Message) -> bool:
        """Handle the "identify" command - identify the power supply.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_identify must be implemented by subclasses")

    # Strongly expected action handlers
    @abstractmethod
    def message_set_voltage(self, message: Message) -> bool:
        """Handle the "set_voltage" command - set output voltage.

        Args:
            message (Message): Incoming message with voltage value.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_set_voltage must be implemented by subclasses")

    @abstractmethod
    def message_set_current(self, message: Message) -> bool:
        """Handle the "set_current" command - set output current limit.

        Args:
            message (Message): Incoming message with current value.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_set_current must be implemented by subclasses")

    @abstractmethod
    def message_toggle_output(self, message: Message) -> bool:
        """Handle the "toggle_output" command - enable or disable power supply output.

        Args:
            message (Message): Incoming message with output state.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_toggle_output must be implemented by subclasses")

    @abstractmethod
    def message_set_ovp(self, message: Message) -> bool:
        """Handle the "set_ovp" command - set over-voltage protection threshold.

        Args:
            message (Message): Incoming message with OVP threshold.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_set_ovp must be implemented by subclasses")

    @abstractmethod
    def message_set_ocp(self, message: Message) -> bool:
        """Handle the "set_ocp" command - set over-current protection threshold.

        Args:
            message (Message): Incoming message with OCP threshold.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_set_ocp must be implemented by subclasses")

    @abstractmethod
    def message_measure(self, message: Message) -> bool:
        """Handle the "measure" command - measure voltage, current, and power.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_measure must be implemented by subclasses")

    @abstractmethod
    def background_task(self):
        """Background task - must be implemented by each factory implementation."""
        raise NotImplementedError("background_task must be implemented by subclasses")

    @abstractmethod
    def message_custom_action(self, message: Message) -> bool:
        """Handle the "custom_action" message - must be implemented by each factory implementation.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_custom_action must be implemented by subclasses")
