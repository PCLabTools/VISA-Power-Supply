"""
file: module.py
description: {{MODULE_DESCRIPTION}}
author: {{AUTHOR}}
"""

from typing import Optional
from abc import ABC, abstractmethod
from paf.communication import Message, Protocol, Module


class {{ClassName}}:
    """Factory for creating {{ClassName}} instances with swappable implementations at runtime.

    Raises:
        ValueError: When an invalid implementation type is specified.

    Returns:
        Base{{ClassName}}: An instance of the factory module based on the specified implementation type.
    """
    _implementations: dict[str, type["Base{{ClassName}}"]] = {}

    @classmethod
    def register(cls, implementation: str, module_class: type["Base{{ClassName}}"]):
        """Registers a factory implementation.

        Args:
            implementation (str): The name of the implementation.
            module_class (type[Base{{ClassName}}]): The class to register.
        """
        cls._implementations[implementation.lower()] = module_class

    @classmethod
    def create(cls, address: str, protocol: Protocol, debug: int = 0, implementation_type: str = "simulated") -> "Base{{ClassName}}":
        """Creates a factory module instance based on implementation type.

        Args:
            address (str): Unique address for the module.
            protocol (Protocol): The protocol instance.
            debug (int, optional): Debug level. Defaults to 0.
            implementation_type (str, optional): Implementation to create. Defaults to "simulated".

        Returns:
            Base{{ClassName}}: The created module instance.

        Raises:
            ValueError: If the specified implementation type is not registered.
        """
        implementation_type = implementation_type.lower()
        if implementation_type not in cls._implementations:
            raise ValueError(f"{{ClassName}}: No factory implementation registered for type '{implementation_type}'")
        return cls._implementations[implementation_type](address, protocol, debug)

    def __new__(cls, address: str, protocol: Protocol, debug: int = 0, implementation_type: str = "simulated") -> "Base{{ClassName}}":
        return cls.create(address, protocol, debug, implementation_type)


class Base{{ClassName}}(Module, ABC):
    """Abstract base class for {{ClassName}} implementations."""

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
        if message.command == "custom_action":
            return self.message_custom_action(message)
        return super().handle_message(message)

    @abstractmethod
    def background_task(self):
        """Background task — must be implemented by each factory implementation."""
        raise NotImplementedError("background_task must be implemented by subclasses")

    @abstractmethod
    def message_custom_action(self, message: Message) -> bool:
        """Handle the "custom_action" message — must be implemented by each factory implementation.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        raise NotImplementedError("message_custom_action must be implemented by subclasses")
