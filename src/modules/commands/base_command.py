from abc import ABC, abstractmethod

class Command(ABC):
    """
    Abstract base class for all commands in the application.
    Implements the Command design pattern for undo/redo functionality.
    """
    @abstractmethod
    def execute(self):
        """
        Executes the command.
        """
        ...

    @abstractmethod
    def undo(self):
        """
        Undoes the command.
        """
        ...
