
from serial_port import SerialPort



class PlateHandler:

    def __init__(self, serial_port: SerialPort) -> None:
        self.__serial_port = serial_port
        
    @property
    def exchange_station_occupied(self) -> bool:
        """True if the exchange station is occupied, False otherwise"""
        pass