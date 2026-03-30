from abc import ABC, abstractmethod

class BaseMainWindow(ABC):
    @abstractmethod
    def show(self):
        pass
    
    @abstractmethod
    def print_file(self):
        pass

    @abstractmethod
    def print_barcode(self):
        pass

    @abstractmethod
    def browse_file(self):
        pass
