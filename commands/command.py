from abc import ABC, abstractmethod

class Command(ABC):
    registry = {}

    name = ""
    description = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name:  # only register real commands
            Command.registry[cls.name] = cls

    @abstractmethod
    def execute(self, *args):
        pass
