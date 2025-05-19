"""Handle Proper Interfacing with the PlateCrane"""

import threading
from typing import ClassVar, Optional, Union

from platecrane_driver.resource_defs import locations, plate_definitions
from platecrane_driver.resource_types import PlateResource
from platecrane_driver.serial_port import (
    SerialPort,  # use when running through WEI REST clients
)

"""
# TODOs:
    * combine two initialization functions
    * Look into how to slow speed of stack pick and place
    * should we be using error_codes.py to be doing some of the error checking/raising

    * Crash error outputs 21(R axis),14(z axis), 02 Wrong location name. 1400 (Z axis hits the plate), 00 success
    * Need a response handler function. Unknown error messages T1, ATS, TU these are about connection issues (multiple access?)
    * Maybe create a plate detect function within pick stack plate function
"""


class PlateCrane:
    """Python interface that allows remote commands to be executed to the plate_crane."""

    _device: Optional[SerialPort] = None
    """SerialPort object for communication with the PlateCrane EX device."""
    response_code: str = "00"
    """Response code from the PlateCrane EX device."""
    response_meaning: str = "OK"
    """Error message from the PlateCrane EX device."""
    status_code: int = 0
    """Status of the PlateCrane EX device."""
    platecrane_current_position: Optional[list[float]] = None
    """Current position of the PlateCrane EX device, if known"""
    _device_lock = threading.Lock()
    """Lock for thread-safe access to the device."""
    initialized: bool = False
    """Flag indicating whether the PlateCrane EX device has been initialized."""

    error_codes: ClassVar[dict[str, str]] = {
        "00": "OK",
        "01": "Unknown or misformatted command",
        "21": "R axis error",
        "14": "z axis error",
        "02": "Invalid location",
        "1400": "Z axis crash",
        "T1": "Serial connection issue",
        "ATS": "Serial connection issue",
        "TU": "Serial connection issue",
    }

    GRIPPER_LIMIT_SWITCH: int = 4

    def __init__(
        self, device_path: Union[str, int] = "/dev/ttyUSB2", baud_rate: int = 9600
    ) -> None:
        """Initializes the PlateCrane object.

        Args:
            device_path (str): path or identifier for the serial port to connect to
            baud_rate (int): baud rate to use for communication with the PlateCrane EX device

        Returns:
            None
        """
        self._device = SerialPort(device=device_path, baud_rate=baud_rate)

    def initialize_platecrane(self) -> None:
        """Connect to the PlateCrane EX device."""
        self.update_status()
        if self.status_code == 0:
            self.home()
        self.platecrane_current_position = self.get_position()
        self.initialized = True

    def send_commmand(
        self,
        command: str,
        timeout: Union[int, float] = 60,
        wait_for_response: bool = True,
        expected_response: Optional[str] = None,
    ) -> str:
        """Sends a command to the PlateCrane EX device.

        Args:
            command (str): command to send to the device
            timeout (int): timeout for the command in seconds
            wait_for_response (bool): whether to wait for a response from the device
            expected_response (str): expected response from the device, if applicable

        Returns:
            str: response from the device, if applicable
        """
        if not self.initialized:
            self.initialize_platecrane()
        with self._device_lock:
            response = self._device.send_command(
                command,
                timeout=timeout,
                wait_for_response=wait_for_response,
                expeected_response=expected_response,
            )
            for response in self._device.response_buffer:
                if response.endswith("\x10"):
                    self.response_code = response.strip("\x10")
                    self.response_meaning = self.error_codes.get(
                        self.response_code, "Unknown error"
                    )
                    if self.response_code != "00":
                        raise ValueError(
                            f"Error {self.response_code}: {self.response_meaning}"
                        )
            return response

    def home(self) -> None:
        """Homes all of the axes."""

        self._device.send_command("HOME\r\n")

    def halt(self) -> None:
        """Halts all of the axes."""

        self._device.send_command("HALT\r\n")

    def update_status(self) -> int:
        """Checks status of plate_crane"""
        self.status_code = int(self._device.send_command("STATUS\r\n"))
        return self.status_code

    def free_joints(self) -> None:
        """Unlocks the joints of the plate_crane"""
        self._device.send_command("limp TRUE\r\n")

    def lock_joints(self) -> None:
        """Locks the joints of the plate_crane"""
        self._device.send_command("limp FALSE\r\n")

    def set_speed(self, speed: int) -> None:
        """Sets the speed of the plate crane arm.

        Args:
            speed (int): (units = % of full speed) Speed at which to move the PlateCrane EX. Appies to all axes

        Returns:
            None
        """
        self._device.send_command(f"SPEED {speed}\r\n")

    def get_location_list(self) -> list[str]:
        """Displays all location information stored in the Plate Crane EX robot's memory"""

        self._device.send_command("LISTPOINTS\r\n", expected_response="End of List")

        return [
            line
            for line in self._device.response_buffer
            if line.strip() not in ("LISTPOINTS", "End of List")
        ]

    def get_location_joint_values(self, location: str) -> list:
        """Returns list of 4 joint values associated with a position name

        Note: right now this returns the joint values stored in the
            PlateCrane EX device memory, not the locations stored in
            resource_defs.py

        TODO: delete this function or associate it with resource_defs.py

        Args:
            location (str): Name of location

        Returns:
            joint_values ([int]): [R, Z, P, Y] joint values
                - R (base rotation)
                - Z (arm vertical axis)
                - P (gripper rotation)
                - Y (arm extension)
        """

        return [
            float(joint)
            for joint in self._device.send_command(f"GETPOINT {location}\r\n").split(
                ", "
            )
        ]

    def get_position(self) -> list:
        """Returns list of joint values for current position of the PlateCrane EX arm

        Args:
            None

        Returns:
            current_position ([int]): [R, Z, P, Y] joint values
                - R (base rotation)
                - Z (arm vertical axis)
                - P (gripper rotation)
                - Y (arm extension)
        """

        return [
            float(joint)
            for joint in self._device.send_command("GETPOS\r\n").split(", ")
        ]

    def set_location(
        self,
        location_name: str,
        r: int = 0,
        z: int = 0,
        p: int = 0,
        y: int = 0,
    ) -> None:
        """Saves a new location into PlateCrane EX device memory

        Args:
            location_name (str): Name of location to be saved
            r (int): base rotation (units: motor steps)
            z (int): vertical axis (units: motor steps)
            p (int): gripper rotation (units: motor steps)
            y (int): arm extension (units: motor steps)

        Returns:
            None
        """
        self._device.send_command(
            f"LOADPOINT {location_name}, {r!s}, {z!s}, {p!s}, {y!s}\r\n"
        )

    def delete_location(self, location_name: str) -> None:
        """Deletes an existing location from the PlateCrane EX device memory

        Args:
        location_name (str): Name of location to delete

        Returns:
            None
        """
        self._device.send_command(f"DELETEPOINT {location_name}\r\n")

    def gripper_open(self) -> None:
        """Opens gripper"""

        self._device.send_command("OPEN\r\n")

    def gripper_close(self) -> None:
        """Closes gripper"""

        command = "CLOSE\r\n"
        self._device.send_command(command)

    def gripped(self) -> bool:
        """Checks if the gripper is currently gripping an object

        Note: This doesn't seem to work. Possibly the gripper limit switch is on a different input than what we extracted from the VB code? There seem to be 48 inputs, so guess and check might work but will take a while.

        Returns:
            bool: True if gripper is gripping, False otherwise
        """
        return (
            self._device.send_command(f"readinp {self.GRIPPER_LIMIT_SWITCH}\r\n") == 0
        )

    def jog(self, axis: str, distance: int) -> None:
        """Moves the specified axis the specified distance.

        Args:
            axis (str): "R", "Z", "P", or "Y"
            distance (int): distance to move along the axis (units = motor steps)

        Returns:
            None
        """

        command = f"JOG {axis},{distance}\r\n"
        self._device.send_command(command)

    def move_joint_angles(self, r: int, z: int, p: int, y: int) -> None:
        """Move to a specified location

        Args:
            R (int): base rotation (unit = motor steps)
            Z (int): vertical axis (unit = motor steps)
            P (int): gripper rotation (unit = motor steps)
            Y (int): arm extension (unit = motor steps)
        """

        self.set_location("TEMP", r, z, p, y)
        self.move_location("TEMP")
        self.delete_location("TEMP")

    def move_single_axis(self, axis: str, location: str) -> None:
        """Moves on a single axis, using an existing location in PlateCrane EX device memory as reference

        Args:
            axis (str): axis to move along
            loc (str): name of location in PlateCrane EX device memory to use as reference

        Returns:
            None
        """

        self._device.send_command(f"MOVE_{axis.upper()} {location}\r\n")

    def move_abs(
        self,
        axis: str,
        value: int,
    ) -> None:
        """Moves a single axis to the specified absolute joint value.

        Args:
            axis (str): axis to move along
            value (int): value to move to (units = motor steps)

        Returns:
            None
        """

        self._device.send_command(f"MOVE_ABS {axis.upper()} {value}\r\n")

    def move_location(self, location: str) -> None:
        """Moves all joint to the given location.

        Args:
            loc (str): location to move to

        Returns:
            None
        """
        self._device.send_command(f"MOVE {location}\r\n")

    def move_safe_vertical(self) -> None:
        """Moves the arm vertically to the safe location's Z level"""

        self.move_abs("Z", locations["Safe"].joint_angles[1])

    def move_safe_arm_extension(self) -> None:
        """Extends/retracts the arm to the safe location's Y level"""

        self.move_abs("Y", locations["Safe"].joint_angles[3])

    def move_safe_gripper_rotation(self) -> None:
        """Rotates the gripper to the safe location's P level"""

        self.move_abs("P", locations["Safe"].joint_angles[2])

    def move_safe(self) -> None:
        """Moves all joints to match the safe location"""
        self.move_safe_arm_extension()
        self.move_safe_vertical()

    def pick_plate_safe_approach(
        self,
        source: str,
        plate_type: str,
        grip_height_in_steps: int,
    ) -> None:
        """Picks a plate from a source type "nest" using a safe travel path.

        Args:
            source (str): source location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate

        Returns:
            None
        """

        # open the gripper
        self.gripper_open()

        # Rotate base (R axis) toward plate location
        current_pos = self.get_position()
        self.move_joint_angles(
            r=locations[source].joint_angles[0],
            z=current_pos[1],
            p=current_pos[2],
            y=current_pos[3],
        )

        # Rotate gripper
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=locations[source].joint_angles[2],
            y=current_pos[3],
        )

        # Lower z axis to safe_approach_z height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[source].safe_approach_height,
            p=current_pos[2],
            y=current_pos[3],
        )

        # extend arm over plate and rotate gripper to correct orientation
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=current_pos[2],
            y=locations[source].joint_angles[3],
        )

        # Lower arm (z axis) to correct plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[source].joint_angles[1] + grip_height_in_steps,
            p=current_pos[2],
            y=current_pos[3],
        )

        # grip the plate
        self.gripper_close()

        # Move arm with plate back to safe approach height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[source].safe_approach_height,
            p=current_pos[2],
            y=current_pos[3],
        )

        # retract arm (Y axis) as much as possible (to same Y axis value as Safe location)
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=current_pos[2],
            y=locations["Safe"].joint_angles[3],
        )

        # move rest of joints to neutral location
        self.move_safe_vertical()
        self.move_safe_arm_extension()

    def place_plate_safe_approach(
        self,
        target: str,
        grip_height_in_steps: int,
    ) -> None:
        """Places a plate to a target location of type "nest" using a safe travel path.

        Args:
            target (str): source location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate

        Returns:
            None
        """

        # Rotate base (R axis) toward target location
        current_pos = self.get_position()
        self.move_joint_angles(
            r=locations[target].joint_angles[0],
            z=current_pos[1],
            p=current_pos[2],
            y=current_pos[3],
        )

        # Rotate gripper to correct orientation
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=locations[target].joint_angles[2],
            y=current_pos[3],
        )

        # Lower z axis to safe_approach_z height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[target].safe_approach_height,
            p=current_pos[2],
            y=current_pos[3],
        )

        # extend arm over plate
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=current_pos[2],
            y=locations[target].joint_angles[3],
        )

        # lower arm (z axis) to correct plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[target].joint_angles[1] + grip_height_in_steps,
            p=current_pos[2],
            y=current_pos[3],
        )

        self.gripper_open()

        # Back away using safe approach path
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[target].safe_approach_height,
            p=current_pos[2],
            y=current_pos[3],
        )

        # retract arm (Y axis) as much as possible (to same Y axis value as Safe location)
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=current_pos[2],
            y=locations["Safe"].joint_angles[3],
        )

        # move arm to safe location
        self.move_safe_vertical()
        self.move_safe_arm_extension()

    def pick_plate_direct(
        self,
        source: str,
        source_type: str,
        plate_type: str,
        grip_height_in_steps: int,
        has_lid: bool,
        incremental_lift: bool = False,
    ) -> None:
        """Picks a plate from a source location of type either "nest" or "stack" using a direct travel path

        "nest" transfers: gripper open, direct to grab plate z height
        "stack" transfers: gripper closed, touch top of plate, z up, z down to correct grab plate height

        Args:
            source (str): source location name defined in resource_defs.py
            source_type (str): either "nest" or "stack"
            plate_type (str): plate definition name defined in resource_defs.py
            grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate
            has_lid (bool): True if plate has lid, False otherwise
            incremental_lift (bool): True if you want to use incremental lift, False otherwise (default False)
                incremental lift (good for ensuring lids are removed gently and correctly):
                    - grab plate at grip_height_in_steps
                    - raise 100 steps along z axis (repeat 5x)
                    - continue with rest of transfer

        Returns:
            None
        """

        # Rotate R axis (base rotation) over the plate
        current_pos = self.get_position()
        self.move_joint_angles(
            r=locations[source].joint_angles[0],
            z=current_pos[1],
            p=current_pos[2],
            y=current_pos[3],
        )

        if source_type == "stack":
            # close the gripper
            self.gripper_close()

            # move the arm directly above the stack
            self.move_joint_angles(
                r=locations[source].joint_angles[0],
                z=current_pos[1],
                p=locations[source].joint_angles[2],
                y=locations[source].joint_angles[3],
            )

            # decrease the plate crane speed
            self.set_speed(50)

            # move down in z height to tap the top of the plates in stack
            self.move_joint_angles(
                r=locations[source].joint_angles[0],
                z=locations[source].joint_angles[
                    1
                ],  # this is the only axis that should need to move
                p=locations[source].joint_angles[2],
                y=locations[source].joint_angles[3],
            )

            # set plate crane back to full speed
            self.set_speed(100)

            # Move up, open gripper, grab plate at correct height
            self.jog("Z", 1000)
            self.gripper_open()

            # Calculate z travel from grip height with/without lid
            if has_lid:
                z_jog_down_from_plate_top = (
                    PlateResource.convert_to_steps(
                        plate_definitions[plate_type].plate_height_with_lid
                    )
                    - grip_height_in_steps
                )
            else:
                z_jog_down_from_plate_top = (
                    PlateResource.convert_to_steps(
                        plate_definitions[plate_type].plate_height
                    )
                    - grip_height_in_steps
                )

            # Move down to correct z height to grip plate
            self.jog("Z", -(1000 + z_jog_down_from_plate_top))

        else:  # if source_type == nest:
            self.gripper_open()

            self.move_joint_angles(
                r=locations[source].joint_angles[0],
                z=locations[source].joint_angles[1] + grip_height_in_steps,
                p=locations[source].joint_angles[2],
                y=locations[source].joint_angles[3],
            )

        # open the gripper
        self.gripper_close()

        if incremental_lift:
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)

        # return arm to safe location
        self.move_safe_vertical()
        self.move_safe_arm_extension()

    def place_plate_direct(
        self,
        target: str,
        target_type: str,  # TODO: use later to slow speed for target_type = "stack"
        grip_height_in_steps: str,
    ) -> None:
        """Places a plate onto a target location of type either "nest" or "stack" using a direct travel path

        Args:
            target (str): target location name defined in resource_defs.py
            target_type (str): either "nest" or "stack"
            plate_type (str): plate definition name defined in resource_defs.py
            grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate

        Returns:
            None

        TODO:
            * use target_type variable to slow approach in "stack" transfers to avoid striking other plates
        """

        # Rotate base (R axis) to target location
        current_pos = self.get_position()
        self.move_joint_angles(
            r=locations[target].joint_angles[0],
            z=current_pos[1],
            p=current_pos[2],
            y=current_pos[3],
        )

        # Extend arm over plate location (Y axis) and rotate gripper to correct orientation (P axis)
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=current_pos[1],
            p=locations[target].joint_angles[2],
            y=locations[target].joint_angles[3],
        )

        if target_type == "stack":
            # lower plate crane speed
            self.set_speed(50)

        # Lower arm (z axis) to plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            r=current_pos[0],
            z=locations[target].joint_angles[1] + grip_height_in_steps,
            p=current_pos[2],
            y=current_pos[3],
        )

        if target_type == "stack":
            # return plate crane to sull speed
            self.set_speed(100)

        # open gripper to release the plate
        self.gripper_open()

        self.move_safe_vertical()
        self.move_safe()

    def _is_location_joint_values(self, location: str, name: str = "temp") -> str:
        """
        If the location was provided as joint values, transfer joint values into a saved location
        on the robot and return the location name. If location parameter is a name of an already saved
        location, do nothing.

        TODO:
            * Is there any reason we should keep this function?
        """
        try:
            # location = eval(location) # replacing with checking config
            from platecrane_driver.resource_defs import location
        except NameError:
            # Location was given as a location name
            print(name + ": " + location)
            location_name = location
        else:
            # Location was given as a joint values
            location_name = name + "_loc"
            self.set_location(
                location_name, location[0], location[1], location[2], location[3]
            )
            print(name + ": " + location_name)

        return location_name

    def remove_lid(
        self,
        source: str,
        target: str,
        plate_type: str,
        height_offset: int = 0,
    ) -> None:
        """Removes lid from a plate at source location and places lid at target location

        Args:
            source (str): source location name defined in resource_defs.py
            target (str): target location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            height_offset (int): change in z height to be applied to grip location on the lid (units = mm)
                defaults to 0mm

        Returns:
            None
        """

        # Calculate grip height in motor steps
        source_grip_height_in_steps = PlateResource.convert_to_steps(
            plate_definitions[plate_type].lid_removal_grip_height + height_offset
        )
        target_grip_height_in_steps = PlateResource.convert_to_steps(
            plate_definitions[plate_type].plate_height_with_lid
            - plate_definitions[plate_type].lid_height
            + height_offset
        )

        # Pass to transfer function but specify that it is a lid we're transferring
        self.transfer(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=True,
            source_grip_height_in_steps=source_grip_height_in_steps,
            target_grip_height_in_steps=target_grip_height_in_steps,
            incremental_lift=True,
        )

    def replace_lid(
        self,
        source: str,
        target: str,
        plate_type: str,
        height_offset: int = 0,
    ) -> None:
        """ "Replaces lid at source location onto a plate at the target location

        Args:
            source (str): source location name defined in resource_defs.py
            target (str): target location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            height_offset (int): change in z height to be applied to grip location on the lid (units = mm)
                defaults to 0mm

        Returns:
            None
        """
        # Calculate grip height in motor steps
        source_grip_height_in_steps = PlateResource.convert_to_steps(
            plate_definitions[plate_type].lid_grip_height + height_offset
        )
        target_grip_height_in_steps = PlateResource.convert_to_steps(
            plate_definitions[plate_type].lid_removal_grip_height + height_offset
        )

        # Pass to transfer function but specify that it is a lid we're transferring
        self.transfer(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            source_grip_height_in_steps=source_grip_height_in_steps,
            target_grip_height_in_steps=target_grip_height_in_steps,
            is_lid=True,
        )

    def transfer(
        self,
        source: str,
        target: str,
        plate_type: str,
        height_offset: int = 0,  # units = mm
        is_lid: bool = False,
        has_lid: bool = False,
        source_grip_height_in_steps: int = None,  # if removing/replacing lid
        target_grip_height_in_steps: int = None,  # if removing/replacing lid
        incremental_lift: bool = False,
    ) -> None:
        """Handles the transfer request

        Args:
            source (str): source location name defined in resource_defs.py
            target (str): target location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            height_offset (int): change in z height to be applied to grip location on the lid (units = mm)
                defaults to 0mm
            is_lid (bool): True if transferring a lid, False otherwise
                defaults to False
            has_lid (bool): True if plate being transferred has a lid, otherwise False
                defaults to False
            source_grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate at source location
                defaults to None
                only used if transfer function is called from remove/replace_lid functions
            target_grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate at target location
                defaults to None
                only used if transfer function is called from remove/replace_lid functions
            incremental_lift (bool): True if you want to use incremental lift, False otherwise (default False)
                incremental lift (good for ensuring lids are removed gently and correctly):
                    - grab plate at grip_height_in_steps
                    - raise 100 steps along z axis (repeat 5x)
                    - continue with rest of transfer

        Raises:
            TODO

        Returns:
            None
        """

        # Extract the source and target location_types
        source_type = locations[source].location_type
        target_type = locations[target].location_type

        # Determine source and target grip heights from bottom of plate (converted from mm to z motor steps)
        """If the transfer function is called from either remove_lid() or replace_lid(),
        these values will be precalculated and passed in. Otherwise they need to be calculated here."""
        if not is_lid:
            grip_height_in_steps = PlateResource.convert_to_steps(
                plate_definitions[plate_type].grip_height + height_offset
            )
            source_grip_height_in_steps = grip_height_in_steps
            target_grip_height_in_steps = grip_height_in_steps

        # is safe approach required for source and/or target?
        source_use_safe_approach = (
            False if locations[source].safe_approach_height == 0 else True
        )
        target_use_safe_approach = (
            False if locations[target].safe_approach_height == 0 else True
        )

        # PICK PLATE FROM SOURCE LOCATION
        if source_type == "stack":
            self.pick_plate_direct(
                source=source,
                source_type=source_type,  # "stack"
                plate_type=plate_type,
                grip_height_in_steps=source_grip_height_in_steps,
                has_lid=has_lid,
                incremental_lift=incremental_lift,
            )

        elif source_type == "nest":
            if source_use_safe_approach:
                self.pick_plate_safe_approach(
                    source=source,
                    plate_type=plate_type,
                    grip_height_in_steps=source_grip_height_in_steps,
                )
            else:
                self.pick_plate_direct(
                    source=source,
                    source_type=source_type,  # nest
                    plate_type=plate_type,
                    grip_height_in_steps=source_grip_height_in_steps,
                    has_lid=has_lid,
                    incremental_lift=incremental_lift,
                )
        else:
            raise Exception("Source location type not defined correctly")

        # PLACE PLATE AT TARGET LOCATION
        if target_type == "stack":
            self.place_plate_direct(
                target=target,
                target_type=target_type,
                grip_height_in_steps=target_grip_height_in_steps,
            )
        elif target_type == "nest":
            if target_use_safe_approach:
                self.place_plate_safe_approach(
                    target=target,
                    grip_height_in_steps=target_grip_height_in_steps,
                )
            else:
                self.place_plate_direct(
                    target=target,
                    target_type=target_type,
                    grip_height_in_steps=target_grip_height_in_steps,
                )
        else:
            raise Exception("Target location type not defined correctly")
