"""Provides SerialPort class to interface with the plate_crane."""

import threading
import time
from typing import Optional, Union

import serial
from madsci.client.event_client import EventClient
from serial import Serial, SerialException


class SerialPort:
    """
    Description:
    Python interface that allows remote commands to be executed on the serial device.
    """

    connection: Optional[Serial] = None
    """Serial connection to the device."""
    device: Union[str, int]
    """Path to the serial device or, on windows, integer COM port identifier. Example: '/dev/ttyUSB1' or 1."""
    baud_rate: int
    """Baud rate for the serial connection."""

    def __init__(
        self,
        device: str = "/dev/ttyUSB2",
        baud_rate: int = 9600,
        logger: Optional[EventClient] = None,
    ) -> None:
        """Creates a new SerialPort object.
        Params:
        - host_path (str): The path to the serial port. Default is '/dev/ttyUSB2'.
        - baud_rate (int): The baud rate of the serial port. Default is 9600.
        """
        self.device = device
        self.baud_rate = baud_rate
        self.connection = None
        self.logger = logger or EventClient()

        self.status = 0
        self.error = ""
        self._serial_lock = threading.Lock()

    def __del__(self) -> None:
        """Destructor to ensure the device is disconnected when the object is deleted."""
        self.disconnect()

    def connect(self) -> None:
        """
        Connect to the serial device, raising an exception if the connection fails.
        """
        self.connection = Serial(self.device, self.baud_rate, timeout=1)
        if not self.connection.is_open:
            raise SerialException(f"Failed to open serial port {self.device}")
        self.logger.log_info(f"Connected to {self.device} at {self.baud_rate} baud")

    def disconnect(self) -> None:
        """Disconnects the robot from the serial port."""
        if self.connection and self.connection.is_open:
            self.connection.close()

    def read_messages(self) -> None:
        """
        Reads messages from the serial port and store results.
        """
        if not self.connection or not self.connection.is_open:
            self.connect()

        with self._serial_lock:
            try:
                while self.connection.in_waiting > 0:
                    message = self.connection.readline().decode("utf-8")
                    if message:
                        self.logger.log_debug(f"Received message: {message}")
                        self.process_message(message)
                    else:
                        self.logger.log_debug("No message received")
            except serial.SerialException as e:
                self.logger.error(f"Serial error: {e}")
            except Exception as e:
                self.logger.error(f"Error reading messages: {e}")

    def process_message(self, message: str) -> None:
        """
        Processes the message received from the serial port.
        This method can be overridden to handle specific messages.
        """
        self.logger.log_debug(f"Processing message: {message.strip('\r\n')}")
        self.response_buffer.append(message.strip("\r\n"))
        if self.last_command and message.startswith(self.last_command):
            self.logger.log_debug(
                f"Command '{self.last_command}' acknowledged by device."
            )
            self.acknowledged = True
        else:
            self.logger.log_debug(f"Recieved response: {message.strip('\r\n')}")
            self.last_response = message.strip("\r\n")

    def send_command(
        self,
        command: str,
        wait_for_response: bool = True,
        timeout: Union[float, int] = 60,
        expected_response: Optional[str] = None,
    ) -> str:
        """
        Sends a command to the device and waits for a response.
        Params:
        - command (str): The command to send to the device.
        - wait_for_response (bool): Whether to wait for a response from the device. Default is True.
        - timeout (float): The time to wait for a response before timing out. Default is 60 seconds.
        - expected_response (str): The expected response from the device. Default is None.
        Returns:
        - str: The last response from the device.
        """
        self.logger.log_info(
            f"Sending command '{command.strip('\r\n')}' to {self.device}"
        )

        if not self.connection or not self.connection.is_open:
            self.connect()

        with self._serial_lock:
            self.connection.read_all()  # *Clear the input buffer
            self.last_command_time = time.time()
            self.acknowledged = False
            self.last_response = None
            self.response_buffer = []
            self.last_command = command.strip("\r\n")
            self.connection.write(command.encode("utf-8"))

        while time.time() - self.last_command_time < timeout:
            self.read_messages()
            if self.acknowledged and not wait_for_response:
                self.logger.log_debug(
                    f"Command '{self.last_command}' acknowledged by device."
                )
                break
            if self.acknowledged and self.last_response:
                if expected_response and self.last_response != expected_response:
                    continue
                self.logger.log_debug(
                    f"Command '{self.last_command}' received response {self.last_response}."
                )
                break
        else:
            error_msg = (
                f"Command '{self.last_command}' timed out after {timeout} seconds."
            )
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)

        return self.last_response
