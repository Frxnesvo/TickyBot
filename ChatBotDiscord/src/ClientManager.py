from abc import ABC, abstractmethod


class ClientManager(ABC):
    
    def __init__(self, event):
        self.event = event
        self._deserializeEvent(event)

    @abstractmethod
    def _deserializeEvent(self, event):
        pass

    @abstractmethod
    def _auth(self):
        pass

    @abstractmethod
    def getHandlersMap(self):
        pass
    
