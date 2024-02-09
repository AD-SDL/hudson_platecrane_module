"""Provides SerialPort class to interface with the plate_crane."""
import time

from serial import Serial, SerialException


class SerialPort:
    """
    Description:
    Python interface that allows remote commands to be executed to the plate_crane.
    """

    def __init__(self, host_path="/dev/ttyUSB2", baud_rate=9600):
        """Creates a new SerialPort object.
        Params:
        - host_path (str): The path to the serial port. Default is '/dev/ttyUSB2'.
        - baud_rate (int): The baud rate of the serial port. Default is 9600.
        """
        self.host_path = host_path
        self.baud_rate = baud_rate
        self.connection = None

        self.status = 0
        self.error = ""

        self.__connect_plate_crane()

    def __del__(self):
        """Destructor to ensure the robot is disconnected when the object is deleted."""
        self.__disconnect_robot()

    def __connect_plate_crane(self):
        """
        Connect to serial port / If wrong port entered inform user
        """
        try:
            self.connection = Serial(self.host_path, self.baud_rate, timeout=1)
            self.connection_status = Serial(self.host_path, self.baud_rate, timeout=1)
        except Exception as e:
            raise Exception("Could not establish connection") from e

    def __disconnect_robot(self):
        """Disconnects the robot from the serial port."""
        try:
            self.connection.close()
        except Exception as err:
            print(err)
        else:
            print("Robot is successfully disconnected")

    def send_command(self, command, timeout=0):
        """
        Sends provided command to Peeler and stores data outputted by the peeler.
        Indicates when the confirmation that the Peeler received the command by displaying 'ACK TRUE.'
        """

        try:
            self.connection.write(command.encode("utf-8"))

        except SerialException as err:
            print(err)
            self.robot_error = err

        response_msg = ""
        initial_command_msg = ""

        time.sleep(timeout)

        while initial_command_msg == "":
            response_msg, initial_command_msg = self.receive_command(timeout)

        # Print the full output message including the initial command that was sent
        print(initial_command_msg)
        print(response_msg)

        error_codes = {
            "21": "R axis error",
            "14": "z axis error",
            "02": "Invalid location",
            "1400": "Z axis crash",
            "T1": "Serial connection issue",
            "ATS": "Serial connection issue",
            "TU": "Serial connection issue",
        }  # TODO: Import the full list from error_codes.py

        if response_msg in error_codes.keys():
            pass

        return response_msg

    def receive_command(self, time_wait):
        """
        Records the data outputted by the plate_crane and sets it to equal "" if no data is outputted in the provided time.
        """

        # response_string = self.connection.read_until(expected=b'\r').decode('utf-8')
        response = ""
        response_string = ""
        initial_command_msg = ""

        if self.connection.in_waiting != 0:
            response = self.connection.readlines()
            initial_command_msg = response[0].decode("utf-8").strip("\r\n")
            if len(response) > 1:
                for line_index in range(1, len(response)):
                    response_string += "\n" + response[line_index].decode(
                        "utf-8"
                    ).strip("\r\n")
            else:
                response_string = ""
        return response_string, initial_command_msg
