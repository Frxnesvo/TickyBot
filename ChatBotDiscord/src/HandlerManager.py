from ClientManager import ClientManager
import importlib

class HandlerManager:
    def __init__(self, client: ClientManager):
        self.client = client   #TODO: questo stato è necessario? Al momento no

    def getHandler(self, command_name):
        handler_path = self.client.getHandlersMap().get(command_name)
        if handler_path:
            try:
                # Separa il percorso del modulo dal nome dell'handler
                module_path, handler_name = handler_path.rsplit('.', 1)
                modul = importlib.import_module(module_path)
                return getattr(modul, handler_name)
            except Exception as e:
                print(f"Errore nell'importare l'handler {handler_path}: {e}")
                return None
        else:
            return None