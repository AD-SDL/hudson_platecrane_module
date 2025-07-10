"""Driver for the Hudson Robotics Sciclops robot."""

import re
import time
from threading import Lock
from typing import Optional, Union

import usb.core
import usb.util
from usb.core import Device

from platecrane_driver.resource_types import Labware

# from resource_types import Labware


class SCICLOPS:
    """
    Description:
    Python interface that allows remote commands to be executed to the Sciclops.
    """

    def __init__(self, VENDOR_ID=0x7513, PRODUCT_ID=0x0002):
        """Creates a new SCICLOPS driver object. The default VENDOR_ID and PRODUCT_ID are for the Sciclops robot."""
        self.VENDOR_ID = VENDOR_ID
        self.PRODUCT_ID = PRODUCT_ID
        self.command_lock = Lock()
        self.usb_connection: Device = self.connect_sciclops()
        self.TEACH_PLATE = 15.0
        self.STD_FINGER_LENGTH = 17.2
        self.COMPRESSION_DISTANCE = 3.35
        self.current_pos = [0, 0, 0, 0]
        self.STATUS = 0
        self.ERROR = ""
        self.GRIPLENGTH = 0
        self.locations = self.load_locations()
        self.status = self.get_status()

    def __del__(self):
        """Destructor for the SCICLOPS driver. Disconnects from the Sciclops robot."""
        self.disconnect_robot()

    def connect_sciclops(self) -> Device:
        """
        Connect to USB device. If wrong device, inform user
        """
        usb_connection = usb.core.find(
            idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID
        )

        if usb_connection is None:
            raise Exception("Could not establish connection.")
        else:
            print("Device Connected")
            return usb_connection

    def is_sciclops_connected(self, device: Optional[Device] = None):
        """Checks if the Sciclops robot is connected via USB."""
        try:
            # Try to get device descriptor
            if device is None:
                device = self.usb_connection
            _ = device.get_active_configuration()
            return True
        except usb.core.USBError:
            # Device likely disconnected
            return False
        except Exception:
            return False

    def disconnect_robot(self):
        """Disconnects from the sciclops robot."""
        try:
            usb.util.dispose_resources(self.usb_connection)
        except Exception as err:
            print(err)
        else:
            print("Robot is disconnected")

    def load_locations(self):
        """
        Loads plate information which affects get_plate function.
        """

        # Dictionary for plate information
        locations = {
            "stack1": {
                "pos": {"Z": -397.1688, "R": 137.1106, "Y": 173.0127, "P": 9.6875},
                "type": "stack",
            },
            "stack2": {
                "pos": {"Z": -397.2875, "R": 154.9712, "Y": 172.5352, "P": 9.6875},
                "type": "stack",
            },
            "stack3": {
                "pos": {"Z": -397.3563, "R": 173.0506, "Y": 172.7398, "P": 9.6875},
                "type": "stack",
            },
            "stack4": {
                "pos": {"Z": -396.1000, "R": 191.1141, "Y": 172.4918, "P": 9.6875},
                "type": "stack",
            },
            "stack5": {
                "pos": {"Z": -394.4875, "R": 209.0771, "Y": 172.5104, "P": 9.6875},
                "type": "stack",
            },
            "lidnest1": {  # Z:-381.0938, R:173.1300, Y:26.1751, P:10.3409
                # "pos": {"Z": -388.8563, "R": 172.8812, "Y": 26.9317, "P": 10.3409},
                "pos": {"Z": -386.8563, "R": 173.1300, "Y": 26.1751, "P": 10.3409},
                "type": "nest",
            },
            "lidnest2": {  # Z:-379.2313, R:205.2971, Y:26.4480, P:10.2841
                # "pos": {"Z": -388.4625, "R": 205.2900, "Y": 26.8139, "P": 10.2841},
                "pos": {"Z": -386.8563, "R": 205.2971, "Y": 26.4480, "P": 10.2841},
                "type": "nest",
            },
            "exchange": {
                "pos": {"Z": -416.8438, "R": 299.8747, "Y": 153.6526, "P": 21.5057},
                "type": "nest",
            },
            "neutral": {
                "pos": {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955},
                "type": "point",
            },
        }

        return locations

    def send_command(self, command: str, wait_for_status: bool = True):
        """
        Sends provided command to Sciclops and stores data outputted by the sciclops.
        """
        with self.command_lock:
            if not self.is_sciclops_connected():
                print("No sciclops connection, attempting to reconnect")
                self.connect_sciclops()

            # * Clear USB buffer
            while self.read_usb(timeout=100):
                continue

            print("<<<")
            print(f"Sending command: {command.strip()}")
            self.usb_connection.write(4, command)

            # * Wait for ACK from Sciclops (Sciclops will send back the command it received)
            response_buffer: str = ""
            start_time = time.time()
            while command not in response_buffer:
                if time.time() - start_time > 60:
                    raise TimeoutError("Timeout waiting for command acknowledgment.")
                response_buffer += self.read_usb()
            if wait_for_status:
                # * Wait for a STATUS message from Sciclops (for certain commands, sciclops responds with messages)
                start_time = time.time()
                while True:
                    if time.time() - start_time > 60:
                        raise TimeoutError("Timeout waiting for status message.")
                    response_buffer += self.read_usb()
                    # * Check if we have received a response status or error message
                    # * 4-digit code at the start of a line indicates a message
                    if re.search(r"\n\d{4} ", response_buffer):
                        break
            # * Read any additional data
            while temp_buffer := self.read_usb():
                response_buffer += temp_buffer

            print("Response:")
            print(response_buffer)
            print(">>>")

            return response_buffer

    def is_ok(self, response: Optional[str] = None) -> bool:
        """
        Returns False if any error codes are found in the response or the current status is non-1.
        """
        if get_status := self.get_status() != "1":
            print(f"Sciclops status is not OK: {get_status}")
            return False
        if response:
            response_codes = self.get_response_codes(response)
            if any(response_code != 0 for response_code in response_codes):
                print(f"Sciclops response codes indicate an error: {response_codes}")
                return False
        return True

    def get_response_codes(self, response: str):
        """
        Extracts the 4-digit response codes from a Sciclops response.
        """
        # * Find all occurrences of 4-digit codes at the start of a line
        codes = re.findall(r"\n(\d{4}) ", response)
        if not codes:
            raise ValueError(f"No response codes found in response: {response}")
        return [int(code) for code in codes]

    def check_boolean_response(self, response: str) -> bool:
        """
        Checks a Sciclops boolean response for truthiness.
        """
        if "true" in response.lower():
            return True
        elif "false" in response.lower():
            return False
        else:
            raise ValueError(f"Unexpected response when checking boolean: {response}.")

    def read_usb(self, timeout: int = 100) -> str:
        """Reads from the USB connection"""
        response = ""
        try:
            response = self.usb_connection.read(0x83, 500, timeout=timeout)
        except Exception as e:
            if e.errno == 110:  # Timeout error
                # * This error is expected if there is no data to read
                return ""
            print(f"Error while reading from USB device: {e}")
        response = "".join(chr(i) for i in response)
        return response

    def get_position(self):
        """
        Requests and stores sciclops position.
        Coordinates:
        Z: Vertical axis
        R: Base turning axis
        Y: Extension axis
        P: Gripper turning axis
        """

        out_msg = self.send_command("GETPOS\r\n")

        # Checks if specified format is found in feedback
        exp = r"Z:([-.\d]+), R:([-.\d]+), Y:([-.\d]+), P:([-.\d]+)"  # Format of coordinates provided in feedback
        find_current_pos = re.search(exp, out_msg)
        self.current_pos = [
            float(find_current_pos[1]),
            float(find_current_pos[2]),
            float(find_current_pos[3]),
            float(find_current_pos[4]),
        ]

        return self.current_pos

    def get_status(self):
        """
        Checks status of Sciclops
        """

        out_msg = self.send_command("STATUS\r\n")

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
        find_status = re.search(exp, out_msg)
        self.status = find_status[1]

        return self.status

    def get_version(self):
        """
        Checks version of Sciclops
        """

        command = "VERSION\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
        find_version = re.search(exp, out_msg)
        self.VERSION = find_version[1]

        print(self.VERSION)

    def reset(self):
        """
        Resets Sciclops
        """

        self.set_speed(5)

        out_msg = self.send_command("RESET\r\n")

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
        find_reset = re.search(exp, out_msg)
        self.RESET = find_reset[1]

    def get_config(self):
        """
        Checks configuration of Sciclops
        """

        out_msg = self.send_command("GETCONFIG\r\n")

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the configuration
        find_config = re.search(exp, out_msg)
        self.CONFIG = find_config[1]

        return self.CONFIG

    def get_grip_length(self):
        """
        Checks the current length of the gripper of Sciclops
        """

        out_msg = self.send_command("GETGRIPPERLENGTH\r\n")

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the gripper length
        find_grip_length = re.search(exp, out_msg)
        self.GRIPLENGTH = find_grip_length[1]

        return self.GRIPLENGTH

    def get_collapsed_distance(self):
        """
        Gets the collapse distance (how far the gripper will compress vertically when colliding with an object).
        """

        out_msg = self.send_command("GETCOLLAPSEDISTANCE\r\n")

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the collapsed distance
        find_collapsed_distance = re.search(exp, out_msg)
        self.COLLAPSEDDISTANCE = find_collapsed_distance[1]
        return self.COLLAPSEDDISTANCE

    def get_steps_per_unit(self):
        """
        Gets the number of steps per unit for each axis.
        """

        out_msg = self.send_command("GETSTEPSPERUNIT\r\n")

        # Checks if specified format is found in feedback
        exp = r"Z:([-.\d]+),R:([-.\d]+),Y:([-.\d]+),P:([-.\d]+)"  # Format of the coordinates provided in feedback
        find_steps_per_unit = re.search(exp, out_msg)
        self.STEPSPERUNIT = [
            float(find_steps_per_unit[1]),
            float(find_steps_per_unit[2]),
            float(find_steps_per_unit[3]),
            float(find_steps_per_unit[4]),
        ]
        return self.STEPSPERUNIT

    def home(self, axis: str = "") -> str:
        """
        Homes all or one of the axes.
        """

        # Moves axes to home position
        if axis:
            return self.send_command(f"HOME {axis}\r\n")
        else:
            return self.send_command("HOME\r\n")

    def open(self) -> str:
        """
        Opens the gripper
        """

        return self.send_command("OPEN\r\n")

    def close(self) -> str:
        """
        Closes the gripper
        """

        return self.send_command("CLOSE\r\n")

    def check_open(self) -> bool:
        """
        Checks if gripper is open
        """

        return self.check_boolean_response(self.send_command("GETGRIPPERISOPEN\r\n"))

    def check_closed(self) -> bool:
        """
        Checks if gripper is closed
        """

        return self.check_boolean_response(self.send_command("GETGRIPPERISCLOSED\r\n"))

    def check_plate(self) -> bool:
        """
        Checks if there is currently a plate in the gripper
        """

        return self.check_boolean_response(self.send_command("GETPLATEPRESENT\r\n"))

    def set_speed(self, speed: int) -> str:
        """
        Sets the movement speed of the Sciclops (as a percentage of max speed).
        """

        return self.send_command(f"SETSPEED {speed}\r\n")

    def list_points(self) -> str:
        """
        Lists all of the preset points
        """

        return self.send_command("LISTPOINTS\r\n")

    def jog(self, axis: str, distance: float) -> tuple[bool, str]:
        """
        Moves the specified axis the specified distance.

        Returns:
            True if a limit switch was hit, False otherwise.
        """

        response = self.send_command(f"JOG {axis},{distance}\r\n")
        response_codes = self.get_response_codes(response)
        if 1214 in response_codes:
            print("Limit switch hit during jog")
            return True, response
        else:
            return False, response

    def loadpoint(self, name: str, R: float, Z: float, P: float, Y: float) -> str:
        """
        Saves named point on Sciclops
        """

        return self.send_command(f"LOADPOINT {name}, Z:{Z}, P:{P}, Y:{Y}, R:{R}\r\n")

    def deletepoint(self, name: str) -> str:
        """
        Deletes point from listpoints function
        """

        return self.send_command(f"DELETEPOINT {name}\r\n")

    def move(self, R, Z, P, Y):
        """
        Moves to specified coordinates
        """

        self.loadpoint("TEMP", R, Z, P, Y)
        response = self.send_command("MOVE TEMP\r\n")
        if status := self.get_status() != "1":
            raise Exception(f"Move failed, status code {status}")
        response_codes = self.get_response_codes(response)
        if [response_code for response_code in response_codes if response_code != 0]:
            raise Exception(
                f"Move failed, non-zero response codes {response_codes} found in response:\r\n{response}"
            )
        self.deletepoint("TEMP")
        position = self.get_position()
        if not all(
            [
                abs(position[0] - Z) < 1.0,
                abs(position[1] - R) < 1.0,
                abs(position[2] - Y) < 1.0,
                abs(position[3] - P) < 1.0,
            ]
        ):
            raise Exception(
                f"Move failed, expected position {[Z, R, Y, P]} but got {position}"
            )

    def move_loc(self, loc):
        """
        Move to preset locations located in load_labware function
        """

        # check if loc exists (later)
        self.move(
            self.locations[loc]["pos"]["R"],
            self.locations[loc]["pos"]["Z"],
            self.locations[loc]["pos"]["P"],
            self.locations[loc]["pos"]["Y"],
        )

    def move_loc_at_height(self, location, height):
        """
        Move to preset locations located in load_labware function
        """

        # check if loc exists (later)
        self.move(
            self.locations[location]["pos"]["R"],
            height,
            self.locations[location]["pos"]["P"],
            self.locations[location]["pos"]["Y"],
        )

    def move_above_loc(self, loc):
        """
        Move to preset locations located in load_labware function
        """

        # check if loc exists (later)
        self.move(
            self.locations[loc]["pos"]["R"],
            self.locations["neutral"]["pos"]["Z"],
            self.locations[loc]["pos"]["P"],
            self.locations[loc]["pos"]["Y"],
        )

    def pick_labware(
        self,
        location_name: str,
        grip_height: float,
        labware_height: float,
        gentle_lift: bool = False,
    ):
        """
        Grabs labware from the provided location
        """

        location = self.locations[location_name]

        self.open()
        self.set_speed(50)
        self.jog("Z", 1000)
        self.jog("Y", -1000)
        # self.move_loc("neutral")
        self.move_above_loc(location_name)
        if location.get("type") == "stack":
            self.set_speed(10)
            self.close()
            self.jog("Z", -1000)
            self.jog("Z", 10)
            self.open()
            self.jog("Z", -2.5 - labware_height + grip_height)
        elif location.get("type") == "nest":
            self.move_loc_at_height(
                location_name, location["pos"]["Z"] + grip_height + 10
            )
            self.set_speed(10)
            self.move_loc_at_height(location_name, location["pos"]["Z"] + grip_height)
        self.close()
        if gentle_lift:
            self.set_speed(1)
            self.jog("Z", 10)
            self.jog("Z", 10)
            self.jog("Z", 10)
        self.set_speed(20)
        self.move_above_loc(location_name)
        if self.check_closed():
            raise Exception(
                f"Failed to pick labware from {location_name} at height {grip_height}: no plate detected."
            )

    def place_labware(self, location_name: str, grip_height: float):
        """
        Places labware in the provided location
        """

        location = self.locations[location_name]

        self.set_speed(20)
        self.move_above_loc(location_name)
        if location.get("type") == "stack":
            self.set_speed(10)
            self.jog("Z", -1000)
            self.jog("Z", 5)
            self.open()
            self.set_speed(50)
            self.jog("Z", 1000)
        elif location.get("type") == "nest":
            self.move_loc_at_height(
                location_name, location["pos"]["Z"] + grip_height + 10
            )
            self.set_speed(1)
            self.move_loc_at_height(location_name, location["pos"]["Z"] + grip_height)
            self.open()
            self.set_speed(50)
            self.jog("Z", 1000)
        self.move_above_loc(location_name)

    def transfer_labware(
        self,
        source: str,
        plate: Union[Labware, dict],
        target: str,
        has_lid: bool = True,
    ):
        """
        Moves labware from a source location to a target location
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_labware(
            location_name=source,
            grip_height=plate.grip_height,
            labware_height=plate.height_with_lid if has_lid else plate.height,
        )
        self.place_labware(
            location_name=target,
            grip_height=plate.grip_height,
        )
        self.move_loc("neutral")

    def remove_lid(self, source: str, plate: Union[Labware, dict], target: str):
        """
        Removes lid from a plate
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_labware(
            location_name=source,
            grip_height=plate.lid_removal_grip_height,
            labware_height=plate.height_with_lid,
            gentle_lift=True,
        )
        self.place_labware(
            location_name=target,
            grip_height=plate.lid_grip_height,
        )
        self.move_loc("neutral")
        if self.check_closed():
            raise Exception(
                f"Failed to pick lid from {source}: no lid detected in gripper."
            )

    def replace_lid(self, source: str, plate: Union[Labware, dict], target: str):
        """
        Places lid on a plate
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_labware(
            location_name=source,
            grip_height=plate.lid_grip_height,
            labware_height=plate.lid_height,
        )
        self.place_labware(
            location_name=target,
            grip_height=plate.lid_removal_grip_height,
        )
        self.move_loc("neutral")

    def remove_and_replace_lid(
        self, source: str, plate: Union[Labware, dict], target: str
    ):
        """
        Removes a lid from a plate and places it on a different plate
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_labware(
            location_name=source,
            grip_height=plate.lid_removal_grip_height,
            labware_height=plate.height_with_lid,
        )
        self.place_labware(
            location_name=target,
            grip_height=plate.lid_removal_grip_height,
        )
        self.move_loc("neutral")

    def pick_lid(self, source: str, plate: Union[Labware, dict]):
        """
        Picks up lid from nest/stack
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_labware(
            location_name=source,
            grip_height=plate.lid_grip_height,
            labware_height=plate.lid_height,
        )
        self.move_above_loc(source)

    def place_lid(self, plate: Union[Labware, dict], target: str):
        """
        Places lid in a nest/stack
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.place_labware(
            location_name=target,
            grip_height=plate.lid_grip_height,
        )
        self.move_above_loc(target)

    def transfer_lid(self, source: str, plate: Union[Labware, dict], target: str):
        """
        Moves a lid from source to target
        """
        if isinstance(plate, dict):
            plate = Labware.model_validate(plate)

        self.pick_lid(
            source=source,
            plate=plate,
        )
        self.place_lid(
            target=target,
            plate=plate,
        )
        self.move_loc("neutral")

    def limp(self, limp_bool):
        """
        Turns on/off limp mode (allows someone to manually move joints)
        """
        self.send_command(f"LIMP {'FALSE' if limp_bool else 'TRUE'}\r\n")
