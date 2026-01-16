"""Handle Proper Interfacing with the PlateCrane"""

import threading
from contextlib import nullcontext
from typing import ClassVar, Optional, Union

from pydantic import BaseModel

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
        self.update_position()
        self.initialized = True

    def send_commmand(
        self,
        command: str,
        timeout: Union[int, float] = 60,
        wait_for_response: bool = True,
        expected_response: Optional[str] = None,
        bypass_locks: bool = False,
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
        with self._device_lock if not bypass_locks else nullcontext():
            response = self._device.send_command(
                command,
                timeout=timeout,
                wait_for_response=wait_for_response,
                expeected_response=expected_response,
                bypass_locks=bypass_locks,
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

        self._device.send_command("HALT\r\n", bypass_locks=True)

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

    def get_location_joint_values(self, location: str) -> list[int]:
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
            int(joint)
            for joint in self._device.send_command(f"GETPOINT {location}\r\n").split(
                ", "
            )
        ]

    def update_position(self) -> list[int]:
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

        self.platecrane_current_position = [
            int(joint) for joint in self._device.send_command("GETPOS\r\n").split(", ")
        ]
        return self.platecrane_current_position

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

        command = f"JOG {axis.upper()},{distance}\r\n"
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

        self._device.send_command(f"MOVE_ABS {axis.upper()},{value}\r\n")

    def move_location(self, location: str) -> None:
        """Moves all joint to the given location.

        Args:
            loc (str): location to move to

        Returns:
            None
        """
        self._device.send_command(f"MOVE {location}\r\n")

    def move_location_joints(self, location: str) -> None:
        """Moves all joint to the given location using software interpolation.

        Args:
            loc (str): location to move to

        Returns:
            None
        """
        r, z, p, y = locations[location].joint_angles
        self.move_joint_angles(r, z, p, y)

    def move_safe_vertical(self) -> None:
        """Moves the arm vertically to the safe location's Z level"""

        self.move_abs("Z", locations["Safe"].joint_angles[1])

    def move_safe_arm_extension(self) -> None:
        """Extends/retracts the arm to the safe location's Y level"""

        self.move_abs("Y", locations["Safe"].joint_angles[3])

    def move_safe_gripper_rotation(self) -> None:
        """Rotates the gripper to the safe location's P level"""

        self.move_abs("P", locations["Safe"].joint_angles[2])

    def move_safe_base_rotation(self) -> None:
        """Rotates the base to the safe location's R level"""

        self.move_abs("R", locations["Safe"].joint_angles[0])

    def move_safe_extension_first(self) -> None:
        """Moves all joints except base rotation to match the safe location, in preparation for travel"""
        self.move_safe_arm_extension()
        self.move_safe_vertical()

    def move_safe_vertical_first(self) -> None:
        """Moves all joints except base rotation to match the safe location, in preparation for travel"""
        self.move_safe_vertical()
        self.move_safe_arm_extension()

    def move_safe(self) -> None:
        """Moves all joints to the safe location"""
        self.move_safe_arm_extension()
        self.move_safe_vertical()
        self.move_safe_base_rotation()
        self.move_safe_gripper_rotation()

    def pick_plate_safe_approach(
        self,
        source: PlateCraneLocation,
        grip_height_in_steps: int,
    ) -> None:
        """Picks a plate from a source type "nest" using a safe travel path.

        Args:
            source (str): source location name defined in resource_defs.py
            plate_type (str): plate definition name defined in resource_defs.py
            grip_height_in_steps (int): z axis steps distance from bottom of plate to grip the plate

        Returns:
            None

        Procedure:
            1. Open the Gripper
            2. Rotate base (R axis) toward plate location
            3. Rotate gripper to match plate orientation
            4. Lower z axis to safe_approach_z height
            5. Extend arm (Y axis) over plate and rotate gripper to correct orientation
            6. Lower arm (z axis) to correct plate grip height
            7. Close the gripperis not
            8. Move arm with plate vertically back to safe approach height
            9. Retract arm to Safe location, then move vertically to safe height
        """

        self.gripper_open()
        self.move_abs("R", source.joint_angles[0])
        self.move_abs("P", source.joint_angles[2])
        self.move_abs("Z", source.safe_approach_height)
        self.move_abs("Y", source.joint_angles[3])
        self.move_abs("Z", source.joint_angles[1] + grip_height_in_steps)
        self.gripper_close()
        self.move_abs("Z", source.safe_approach_height)
        self.move_safe_extension_first()
        self.update_position()

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

        Procedure:
            1. Rotate base (R axis) toward target location
            2. Rotate gripper to correct orientation
            3. Lower z axis to safe_approach_z height
            4. Extend arm (Y axis) over plate and rotate gripper to correct orientation
            5. Lower arm (z axis) to correct plate grip height
            6. Open the gripper
            7. Move arm with plate vertically back to safe approach height
            8. Retract arm to Safe location, then move vertically to safe height
        """

        self.move_abs("R", target.joint_angles[0])
        self.move_abs("P", target.joint_angles[2])
        self.move_abs("Z", target.safe_approach_height)
        self.move_abs("Y", target.joint_angles[3])
        self.move_abs("Z", target.joint_angles[1] + grip_height_in_steps)
        self.gripper_open()
        self.move_abs("Z", target.safe_approach_height)
        self.move_safe_extension_first()
        self.update_position()

    def pick_plate_direct(
        self,
        source: PlateCraneLocation,
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
        self.move_abs("R", source.joint_angles[0])

        if source_type == "stack":
            # close the gripper
            self.gripper_close()

            # move the arm directly above the stack (P and Y axes)
            self.move_abs("P", source.joint_angles[2])
            self.move_abs("Y", source.joint_angles[3])

            # decrease the plate crane speed
            self.set_speed(50)

            # move down in z height to tap the top of the plates in stack
            self.move_abs("Z", source.joint_angles[1])

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
            self.move_abs("P", source.joint_angles[2])
            self.move_abs("Y", source.joint_angles[3])
            self.move_abs("Z", source.joint_angles[1] + grip_height_in_steps)

        # close the gripper to pick up the plate
        self.gripper_close()

        if incremental_lift:
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", -100)
            self.jog("Z", 100)
            self.jog("Z", -100)
            self.jog("Z", 100)
            self.jog("Z", 100)

        # return arm to safe location
        self.move_safe_vertical_first()
        self.update_position()

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
        self.move_abs("R", target.joint_angles[0])

        # Extend arm over plate location (Y axis) and rotate gripper to correct orientation (P axis)
        self.move_abs("Y", target.joint_angles[3])
        self.move_abs("P", target.joint_angles[2])

        if target_type == "stack":
            # lower plate crane speed
            self.set_speed(50)

        # Lower arm (z axis) to plate grip height
        self.move_abs("Z", target.joint_angles[1] + grip_height_in_steps)

        if target_type == "stack":
            # return plate crane to full speed
            self.set_speed(100)

        # open gripper to release the plate
        self.gripper_open()

        self.move_safe_vertical_first()
        self.update_position()

    def remove_lid(
        self,
        source: PlateCraneLocation,
        target: PlateCraneLocation,
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
        source: PlateCraneLocation,
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

    def pick(
        self,
        source: PlateCraneLocation,
        plate_type: str,
        height_offset: int = 0,  # units = mm
        is_lid: bool = False,
        has_lid: bool = False,
        source_grip_height_in_steps: int = 0,  # if removing/replacing lid
        incremental_lift: bool = False,
    ) -> None:
        """Handles the pick request"""
        source_type = source.location_type

        # Determine source and target grip heights from bottom of plate (converted from mm to z motor steps)
        """If the transfer function is called from either remove_lid() or replace_lid(),
        these values will be precalculated and passed in. Otherwise they need to be calculated here."""
        if not is_lid:
            grip_height_in_steps = PlateResource.convert_to_steps(
                plate_definitions[plate_type].grip_height + height_offset
            )
            source_grip_height_in_steps = grip_height_in_steps

        # is safe approach required for source and/or target?
        source_use_safe_approach = source.safe_approach_height != 0

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

    def place(
        self,
        target: PlateCraneLocation,
        plate_type: str,
        height_offset: int = 0,  # units = mm
        is_lid: bool = False,
        target_grip_height_in_steps: int = 0,  # if removing/replacing lid
    ) -> None:
        """Handles the place request"""
        # PLACE PLATE AT TARGET LOCATION
        target_type = target.location_type
        target_use_safe_approach = target.safe_approach_height != 0
        if not is_lid:
            grip_height_in_steps = PlateResource.convert_to_steps(
                plate_definitions[plate_type].grip_height + height_offset
            )
            target_grip_height_in_steps = grip_height_in_steps
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
