"""Driver for the Hudson Robotics Sciclops robot."""

import re
import time
from threading import Lock
from typing import Optional

import usb.core
import usb.util
from pydantic import BaseModel
from usb.core import Device

# from platecrane_driver.resource_types import Labware,
from platecrane_driver.resource_types import PlateResource, SciClopsLocation

# from resource_types import Labware


class PlateCraneLocation(BaseModel):
    """A location accessible by the PlateCrane EX"""

    name: str
    """Internal name of the location"""
    joint_angles: list[int]
    """List of 4 joint angles (unit: integer stepper values)"""
    location_type: str
    """Type of location, either stack or nest. This will be used to determine gripper path for interactions with the location"""
    safe_approach_height: Optional[int] = None
    """A safe height (unit: integer stepper value for Z axis) from which
    to extend the arm when approaching this location."""


class SCICLOPS:
    """
    Description:
    Python interface that allows remote commands to be executed to the Sciclops.
    """

    status_code: int = 0
    sciclops_current_position: Optional[list[float]]

    def __init__(self, vendor_id=0x7513, product_id=0x0002):
        """Creates a new SCICLOPS driver object. The default VENDOR_ID and PRODUCT_ID are for the Sciclops robot."""
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.command_lock = Lock()
        self.usb_connection: Device = self.connect_sciclops()
        self.TEACH_PLATE = 15.0
        self.STD_FINGER_LENGTH = 17.2
        self.COMPRESSION_DISTANCE = 3.35
        self.safe_z_height = 15
        self.current_pos = [0, 0, 0, 0]
        # self.STATUS = 0

        self.ERROR = ""
        self.GRIPLENGTH = 0
        # self.locations = self.load_locations()
        self.status_code = self.get_status()

    def __del__(self):
        """Destructor for the SCICLOPS driver. Disconnects from the Sciclops robot."""
        self.disconnect_robot()

    def connect_sciclops(self) -> Device:
        """
        Connect to USB device. If wrong device, inform user
        """
        usb_connection = usb.core.find(
            idVendor=self.vendor_id, idProduct=self.product_id
        )

        if usb_connection is None:
            raise Exception("Could not establish connection.")
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

    def home(self, axis: str = "") -> str:
        """
        Homes all or one of the axes.
        """
        # Moves axes to home position
        if axis:
            return self.send_command(f"HOME {axis}\r\n")
        return self.send_command("HOME\r\n")

    def get_status(self) -> str:
        """
        Checks status of Sciclops
        """
        out_msg = self.send_command("STATUS\r\n")
        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
        find_status = re.search(exp, out_msg)
        self.status_code = find_status[1]  # status_code is a str here

        return self.status_code

    def disconnect_robot(self):
        """Disconnects from the sciclops robot."""
        try:
            usb.util.dispose_resources(self.usb_connection)
        except Exception as err:
            print(err)
        else:
            print("Robot is disconnected")

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
        if "false" in response.lower():
            return False
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

    def get_current_position(self) -> list:
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

    def get_version(self) -> str:
        """
        Checks version of Sciclops
        """
        command = "VERSION\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        # Checks if specified format is found in feedback
        exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
        find_version = re.search(exp, out_msg)
        self.version = find_version[1]

        return self.version

    def reset(self) -> None:
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
        self.config = find_config[1]

        return self.config

    # def get_grip_length(self):
    #     """
    #     Checks the current length of the gripper of Sciclops
    #     """

    #     out_msg = self.send_command("GETGRIPPERLENGTH\r\n")

    #     # Checks if specified format is found in feedback
    #     exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the gripper length
    #     find_grip_length = re.search(exp, out_msg)
    #     self.GRIPLENGTH = find_grip_length[1]

    #     return self.GRIPLENGTH

    # def get_collapsed_distance(self):
    #     """
    #     Gets the collapse distance (how far the gripper will compress vertically when colliding with an object).
    #     """

    #     out_msg = self.send_command("GETCOLLAPSEDISTANCE\r\n")

    #     # Checks if specified format is found in feedback
    #     exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the collapsed distance
    #     find_collapsed_distance = re.search(exp, out_msg)
    #     self.COLLAPSEDDISTANCE = find_collapsed_distance[1]
    #     return self.COLLAPSEDDISTANCE

    def get_steps_per_unit(self) -> list:
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

    def gripper_open(self) -> str:
        """
        Opens the gripper
        """
        return self.send_command("OPEN\r\n")

    def gripper_close(self) -> str:
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
        Lists all locations saved in the internal SciClops memory - NOT USED!
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
            # TODO: as far as I can tell, it does not ever return 1214
            print("Limit switch hit during jog")
            return True, response
        return False, response

    def loadpoint(self, name: str, R: float, Z: float, P: float, Y: float) -> str:
        """
        Saves named point on Sciclops
        """
        return self.send_command(f"LOADPOINT {name}, Z:{Z}, P:{P}, Y:{Y}, R:{R}\r\n")

    def deletepoint(self, name: str) -> str:
        """
        Deletes point from listpoints function - NOT USED!
        """
        return self.send_command(f"DELETEPOINT {name}\r\n")

    def move(self, R: float, Z: float, P: float, Y: float):
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
        position = self.get_current_position()
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

    def move_loc(self, location_obj: SciClopsLocation) -> None:
        """
        Move to preset locations located in load_labware function
        """
        # TODO: what do we want to pass in here, a SciClops Location obj or string name?
        # location_obj = locations[location_name]
        self.move(
            R=location_obj.joint_angles["R"],
            Z=location_obj.joint_angles["Z"],
            P=location_obj.joint_angles["P"],
            Y=location_obj.joint_angles["Y"],
        )

    # def move_loc_at_height(
    #     self,
    #     location_obj: SciClopsLocation,
    #     height
    # ):
    #     """
    #     Move to preset locations located in load_labware function
    #     """

    #     # check if loc exists (later)
    #     self.move(
    #         self.locations[location]["pos"]["R"],
    #         height,
    #         self.locations[location]["pos"]["P"],
    #         self.locations[location]["pos"]["Y"],
    #     )

    def move_above_loc(
        self, location_obj: SciClopsLocation, z_height: Optional[float] = None
    ) -> None:
        """
        Move to preset locations located in load_labware function
        """
        self.move(
            R=location_obj.joint_angles["R"],
            Z=z_height if z_height is not None else self.safe_z_height,
            P=location_obj.joint_angles["P"],
            Y=location_obj.joint_angles["Y"],
        )

    # -------------------------------------------
    # def pick_plate_direct(
    #     self,
    #     source: PlateCraneLocation,
    #     source_type: str,
    #     plate_type: str,
    #     grip_height_in_steps: int,
    #     has_lid: bool,
    #     incremental_lift: bool = False,
    # ) -> None:
    #     """Picks a plate from a source location of type either "nest" or "stack" using a direct travel path

    #     "nest" transfers: gripper open, direct to grab plate z height
    #     "stack" transfers: gripper closed, touch top of plate, z up, z down to correct grab plate height

    #     Args:
    #         source (str): source location name defined in resource_defs.py
    #         source_type (str): either "nest" or "stack"
    #         plate_type (str): plate definition name defined in resource_defs.py
    #         grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate
    #         has_lid (bool): True if plate has lid, False otherwise
    #         incremental_lift (bool): True if you want to use incremental lift, False otherwise (default False)
    #             incremental lift (good for ensuring lids are removed gently and correctly):
    #                 - grab plate at grip_height_in_steps
    #                 - raise 100 steps along z axis (repeat 5x)
    #                 - continue with rest of transfer

    #     Returns:
    #         None
    #     """

    #     # Rotate R axis (base rotation) over the plate
    #     self.move_abs("R", source.joint_angles[0])

    #     if source_type == "stack":
    #         # close the gripper
    #         self.gripper_close()

    #         # move the arm directly above the stack (P and Y axes)
    #         self.move_abs("P", source.joint_angles[2])
    #         self.move_abs("Y", source.joint_angles[3])

    #         # decrease the plate crane speed
    #         self.set_speed(50)

    #         # move down in z height to tap the top of the plates in stack
    #         self.move_abs("Z", source.joint_angles[1])

    #         # set plate crane back to full speed
    #         self.set_speed(100)

    #         # Move up, open gripper, grab plate at correct height
    #         self.jog("Z", 1000)
    #         self.gripper_open()

    #         # Calculate z travel from grip height with/without lid
    #         if has_lid:
    #             z_jog_down_from_plate_top = (
    #                 PlateResource.convert_to_steps(
    #                     plate_definitions[plate_type].plate_height_with_lid
    #                 )
    #                 - grip_height_in_steps
    #             )
    #         else:
    #             z_jog_down_from_plate_top = (
    #                 PlateResource.convert_to_steps(
    #                     plate_definitions[plate_type].plate_height
    #                 )
    #                 - grip_height_in_steps
    #             )

    #         # Move down to correct z height to grip plate
    #         self.jog("Z", -(1000 + z_jog_down_from_plate_top))

    #     else:  # if source_type == nest:
    #         self.gripper_open()
    #         self.move_abs("P", source.joint_angles[2])
    #         self.move_abs("Y", source.joint_angles[3])
    #         self.move_abs("Z", source.joint_angles[1] + grip_height_in_steps)

    #     # close the gripper to pick up the plate
    #     self.gripper_close()

    #     if incremental_lift:
    #         self.jog("Z", 100)
    #         self.jog("Z", 100)
    #         self.jog("Z", -100)
    #         self.jog("Z", 100)
    #         self.jog("Z", -100)
    #         self.jog("Z", 100)
    #         self.jog("Z", 100)

    #     # return arm to safe location
    #     self.move_safe_vertical_first()
    #     self.update_position()

    # -----------PLATE CRANE EXAMPLE ABOVE  --------------------------- #
    def pick_plate_direct(
        self,
        source: SciClopsLocation,
        plate_type: PlateResource,
        has_lid: bool,
        grip_height_offset: Optional[float] = 0,
        # grip_height_in_steps: float,
        # labware_height: float,
        incremental_lift: bool = False,
    ) -> None:
        #     self,
        #     source: PlateCraneLocation,
        #     source_type: str,
        #     plate_type: str,
        #     grip_height_in_steps: int,
        #     has_lid: bool,
        #     incremental_lift: bool = False,
        # ) -> None:
        #     """
        #     Grabs labware from the provided location
        #     """

        # TESTING
        print(f"{source=}")
        # -------------------------old code -------------
        # location = self.locations[location_name]

        # Reset with gripper high and open.
        self.gripper_open()
        self.set_speed(50)
        self.jog("Z", 1000)
        self.jog("Y", -1000)

        # Move above the source location.
        self.move_above_loc(location_obj=source)

        # If the location is a Stack...
        if source.location_type == "stack":
            # Jog down to touch the top of the stacked plates.
            self.set_speed(10)
            self.gripper_close()
            self.jog("Z", -1000)

            # Once top of plates is touched, jog up 10, open gripper, then move down to grab plate at the correct height.
            self.jog("Z", 100)
            self.gripper_open()

            # Calculate z travel from grip height
            if has_lid:
                z_jog_down_from_plate_top = (
                    plate_type.plate_height_with_lid
                    - plate_type.grip_height
                    - grip_height_offset
                )
            else:
                z_jog_down_from_plate_top = (
                    plate_type.plate_height
                    - plate_type.grip_height
                    - grip_height_offset
                )

            self.jog("Z", -(100 + z_jog_down_from_plate_top))

        # If the location is a Nest....
        elif source.location_type == "nest":
            self.move_above_loc(
                location_obj=source,
                z_height=source.joint_angles["Z"] + plate_type.grip_height + 100,
            )
            self.set_speed(10)
            self.move_above_loc(
                location_obj=source,
                z_height=source.joint_angles["Z"] + plate_type.grip_height,
            )
        self.gripper_close()

        # If incremental lift was specified....
        if incremental_lift:
            self.set_speed(1)
            self.jog("Z", 10)
            self.jog("Z", 10)
            self.jog("Z", 10)
        self.set_speed(20)
        self.move_above_loc(location_obj=source)
        if self.check_closed():
            raise Exception(
                f"Failed to pick labware from {source.name} at height {plate_type.grip_height}: no plate detected."
            )

    def place_plate_direct(
        self,
        target: SciClopsLocation,
        plate_type: PlateResource,
        grip_height_offset: Optional[float] = 0,
    ):
        """
        Places labware in the provided location
        """

        self.set_speed(20)
        self.move_above_loc(location_obj=target)

        if target.location_type == "stack":
            self.set_speed(10)
            self.jog("Z", -1000)
            self.jog("Z", 5)  # why are we jogging up 5?
            self.gripper_open()
            self.set_speed(50)
            self.jog("Z", 1000)
        elif target.location_type == "nest":
            self.move_above_loc(
                location_obj=target,
                z_height=target.joint_angles["Z"] + plate_type.grip_height + 10,
            )
            self.set_speed(1)
            self.move_above_loc(
                location_obj=target,
                z_height=target.joint_angles["Z"] + plate_type.grip_height,
            )
            self.gripper_open()
            self.set_speed(50)
            self.jog("Z", 1000)
        self.move_above_loc(target)

    # def transfer_labware(
    #     self,
    #     source: str,
    #     plate: Union[Labware, dict],
    #     target: str,
    #     has_lid: bool = True,
    # ):
    #     """
    #     Moves labware from a source location to a target location
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.pick_labware(
    #         location_name=source,
    #         grip_height=plate.grip_height,
    #         labware_height=plate.height_with_lid if has_lid else plate.height,
    #     )
    #     self.place_labware(
    #         location_name=target,
    #         grip_height=plate.grip_height,
    #     )
    #     self.move_loc("neutral")

    def remove_lid(
        self,
        source: str,
        target: str,
        plate_type: PlateResource,
    ):
        # TODO: START HERE TOMORROW!
        """
        Removes lid from a plate
        """
        # if isinstance(plate, dict):
        #     plate = Labware.model_validate(plate)

        # self.pick_labware(
        #     location_name=source,
        #     grip_height=plate.lid_removal_grip_height,
        #     labware_height=plate.height_with_lid,
        #     gentle_lift=True,
        # )

        lid_grip_offset = plate_type.grip_height - plate_type.lid_removal_grip_height

        self.pick_plate_direct(
            source=source,
            plate_type=plate_type,
            grip_height_offset=lid_grip_offset,
            incremental_lift=True,
        )
        # self.place_plate_direct(
        #     target=target,
        #     plate_type=plate_type,

        # )
        # self.place_labware(
        #     location_name=target,
        #     grip_height=plate.lid_grip_height,
        # )
        # self.move_loc("neutral")
        # if self.check_closed():
        #     raise Exception(
        #         f"Failed to pick lid from {source}: no lid detected in gripper."
        #     )

    # def replace_lid(self, source: str, plate: Union[Labware, dict], target: str):
    #     """
    #     Places lid on a plate
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.pick_labware(
    #         location_name=source,
    #         grip_height=plate.lid_grip_height,
    #         labware_height=plate.lid_height,
    #     )
    #     self.place_labware(
    #         location_name=target,
    #         grip_height=plate.lid_removal_grip_height,
    #     )
    #     self.move_loc("neutral")

    # def remove_and_replace_lid(
    #     self, source: str, plate: Union[Labware, dict], target: str
    # ):
    #     """
    #     Removes a lid from a plate and places it on a different plate
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.pick_labware(
    #         location_name=source,
    #         grip_height=plate.lid_removal_grip_height,
    #         labware_height=plate.height_with_lid,
    #     )
    #     self.place_labware(
    #         location_name=target,
    #         grip_height=plate.lid_removal_grip_height,
    #     )
    #     self.move_loc("neutral")

    # def pick_lid(self, source: str, plate: Union[Labware, dict]):
    #     """
    #     Picks up lid from nest/stack
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.pick_labware(
    #         location_name=source,
    #         grip_height=plate.lid_grip_height,
    #         labware_height=plate.lid_height,
    #     )
    #     self.move_above_loc(source)

    # def place_lid(self, plate: Union[Labware, dict], target: str):
    #     """
    #     Places lid in a nest/stack
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.place_labware(
    #         location_name=target,
    #         grip_height=plate.lid_grip_height,
    #     )
    #     self.move_above_loc(target)

    # def transfer_lid(self, source: str, plate: Union[Labware, dict], target: str):
    #     """
    #     Moves a lid from source to target
    #     """
    #     if isinstance(plate, dict):
    #         plate = Labware.model_validate(plate)

    #     self.pick_lid(
    #         source=source,
    #         plate=plate,
    #     )
    #     self.place_lid(
    #         target=target,
    #         plate=plate,
    #     )
    #     self.move_loc("neutral")

    def limp(self, limp_bool: bool) -> None:
        """
        Turns on/off limp mode (allows someone to manually move joints)
        """
        self.send_command(f"LIMP {'FALSE' if limp_bool else 'TRUE'}\r\n")
