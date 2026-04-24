"""
file: simulated.py
description: Simulated implementation of {{ClassName}} for development and testing.
author: {{AUTHOR}}
"""

from time import sleep
from paf.communication import Message
from .module import {{ClassName}}, Base{{ClassName}}


class Simulated{{ClassName}}(Base{{ClassName}}):
    """Simulated implementation of {{ClassName}}."""

    def background_task(self):
        """Simulated background task."""
        while self.background_task_running:
            if self.debug: print(f"{self.__class__.__name__} ({self.address}): Performing background task.")
            # TODO: implement simulated background task logic
            sleep(1)

    def message_custom_action(self, message: Message) -> bool:
        """Handles the "custom_action" message.

        Args:
            message (Message): Incoming message.

        Returns:
            bool: False to continue running.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling custom action: {message}")
        # TODO: implement simulated custom action logic
        return False


# Register this implementation with the factory
{{ClassName}}.register("simulated", Simulated{{ClassName}})
