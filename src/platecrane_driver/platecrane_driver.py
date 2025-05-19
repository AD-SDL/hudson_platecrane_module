"""Handle Proper Interfacing with the PlateCrane"""

import re
import time

from platecrane_driver.resource_defs import locations, plate_definitions
from platecrane_driver.resource_types import PlateResource
from platecrane_driver.serial_port import (
    SerialPort,  # use when running through WEI REST clients
)

# from serial_port import SerialPort      # use when running through the driver
# from resource_defs import locations, plate_definitions
# from resource_types import PlateResource


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

    __serial_port: SerialPort

    def __init__(self, host_path="/dev/ttyUSB4", baud_rate=9600):
        """Initialization function

        Args:
            host_path (str): usb path of PlateCrane EX device
            baud_rate (int): baud rate to use for communication with the PlateCrane EX device

        Returns:
            None
        """

        # define variables
        self.__serial_port = SerialPort(host_path=host_path, baud_rate=baud_rate)
        self.robot_error = "NO ERROR"
        self.status = 0
        self.error = ""

        self.robot_status = ""
        self.movement_state = "READY"
        self.platecrane_current_position = None

        # initialize actions
        self.initialize()

    def initialize(self):
        """Initialization actions"""
        self.get_status()
        if self.robot_status == "0":
            self.home()
        self.platecrane_current_position = self.get_position()

    def home(self):
        """Homes all of the axes. Returns to neutral position (above exchange)

        Args:
            timeout (int): Seconds to wait for plate crane response after sending serial command, defaults to 28 seconds.

        Returns:
            None
        """

        # Moves axes to home position
        command = "HOME\r\n"
        self.__serial_port.send_command(command, timeout=60)

    def get_status(self):
        """Checks status of plate_crane"""
        command = "STATUS\r\n"
        self.robot_status = self.__serial_port.send_command(command)

    def free_joints(self):
        """Unlocks the joints of the plate_crane"""
        command = "limp TRUE\r\n"
        self.__serial_port.send_command(command)

    def lock_joints(self):
        """Locks the joints of the plate_crane"""
        command = "limp FALSE\r\n"
        self.__serial_port.send_command(command)

    def set_speed(self, speed: int):
        """Sets the speed of the plate crane arm.

        Args:
            speed (int): (units = % of full speed) Speed at which to move the PlateCrane EX. Appies to all axes

        Returns:
            None
        """
        command = "SPEED " + str(speed)
        self.__serial_port.send_command(command, timeout=0, delay=1)
        self.get_position()
        print(f"SPEED SET TO {speed}%")

    def get_location_list(self):
        """Displays all location information stored in the Plate Crane EX robot's memory"""

        command = "LISTPOINTS\r\n"
        out_msg = self.__serial_port.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
            find_status = re.search(exp, out_msg)
            self.status = find_status[1]

            print(self.status)

        except Exception as err:
            print("Error in get_status")
            self.robot_error = err

    def get_location_joint_values(self, location: str = None) -> list:
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

        command = "GETPOINT " + location + "\r\n"

        joint_values = list(self.__serial_port.send_command(command).split(" "))
        joint_values = [eval(x.strip(",")) for x in joint_values]

        return joint_values

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

        command = "GETPOS\r\n"

        try:
            # collect coordinates of current position
            current_position = list(self.__serial_port.send_command(command).split(" "))
            print(current_position)
            current_position = [eval(x.strip(",")) for x in current_position]
            print(current_position)
        except Exception:
            # Fall back: overlapping serial responses were detected. Wait 5 seconds then resend latest command
            time.sleep(5)
            current_position = list(self.__serial_port.send_command(command).split(" "))
            current_position = [eval(x.strip(",")) for x in current_position]

        return current_position

    def set_location(
        self,
        location_name: str = "TEMP_0",
        R: int = 0,
        Z: int = 0,
        P: int = 0,
        Y: int = 0,
    ):
        """Saves a new location into PlateCrane EX device memory

        Args:
            location_name (str): Name of location to be saved
            R (int): base rotation (units: motor steps)
            Z (int): vertical axis (units: motor steps)
            P (int): gripper rotation (units: motor steps)
            Y (int): arm extension (units: motor steps)

        Returns:
            None
        """

        command = "LOADPOINT %s, %s, %s, %s, %s\r\n" % (
            location_name,
            str(R),
            str(Z),
            str(P),
            str(Y),
        )
        self.__serial_port.send_command(command)

    def delete_location(self, location_name: str = None):
        """Deletes an existing location from the PlateCrane EX device memory

        Args:
        location_name (str): Name of location to delete

        Returns:
            None
        """
        if not location_name:
            raise Exception("No location name provided")

        command = "DELETEPOINT %s\r\n" % (location_name)
        self.__serial_port.send_command(command)

    def gripper_open(self):
        """Opens gripper"""

        command = "OPEN\r\n"
        self.__serial_port.send_command(command)

    def gripper_close(self):
        """Closes gripper"""

        command = "CLOSE\r\n"
        self.__serial_port.send_command(command)

    def check_open(self):
        """Checks if gripper is open"""

        command = "GETGRIPPERISOPEN\r\n"
        self.__serial_port.send_command(command)

    def check_closed(self):
        """Checks if gripper is closed"""

        command = "GETGRIPPERISCLOSED\r\n"
        self.__serial_port.send_command(command)

    def jog(self, axis, distance) -> None:
        """Moves the specified axis the specified distance.

        Args:
            axis (str): "R", "Z", "P", or "Y"
            distance (int): distance to move along the axis (units = motor steps)

        Returns:
            None
        """

        command = "JOG %s,%d\r\n" % (axis, distance)
        self.__serial_port.send_command(command)

    def move_joint_angles(self, R: int, Z: int, P: int, Y: int) -> None:
        """Move to a specified location

        Args:
            R (int): base rotation (unit = motor steps)
            Z (int): vertical axis (unit = motor steps)
            P (int): gripper rotation (unit = motor steps)
            Y (int): arm extension (unit = motor steps)
        """

        self.set_location("TEMP", R, Z, P, Y)
        command = "MOVE TEMP\r\n"

        try:
            self.__serial_port.send_command(command, timeout=60)

        except Exception as err:
            print(err)
            self.robot_error = err
        else:
            self.move_status = "COMPLETED"
            pass

        self.delete_location("TEMP")

    def move_single_axis(self, axis: str, loc: str) -> None:
        """Moves on a single axis, using an existing location in PlateCrane EX device memory as reference

        Args:
            axis (str): axis to move along
            loc (str): name of location in PlateCrane EX device memory to use as reference

        Raises:
            TODO

        Returns:
            None

        TODO:
            * Handle errors using error_codes.py
            * Reference locations in resource_defs.py, not device memory
        """

        if not loc:
            raise Exception(
                "PlateCraneLocationException: NoneType variable is not compatible as a location"
            )

        command = "MOVE_" + axis.upper() + " " + loc + "\r\n"
        self.__serial_port.send_command(command)
        self.move_status = "COMPLETED"

    def move_location(self, loc: str = None) -> None:
        """Moves all joint to the given location.

        Args:
            loc (str): location to move to

        Returns:
            None

        TODO:
            * Handle the error raising within error_codes.py
        """
        if not loc:
            raise Exception(
                "PlateCraneLocationException: NoneType variable is not compatible as a location"
            )

        cmd = "MOVE " + loc + "\r\n"
        self.__serial_port.send_command(cmd)

    def move_tower_neutral(self) -> None:
        """Moves the tower to neutral position

        TODO:
            * This still creates a TEMP position, moves to it, then deletes it after.
                Change this, and other related methods below, to use only access
                locations in resource_defs
        """
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations["Safe"].joint_angles[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

    def move_arm_neutral(self) -> None:
        """Moves the arm to neutral position"""

        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=locations["Safe"].joint_angles[3],
        )

    def move_gripper_neutral(self) -> None:
        """Moves the gripper to neutral position"""

        self.move_single_axis("P", "Safe")

        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=locations,
            Y=current_pos[3],
        )

    def move_joints_neutral(self) -> None:
        """Moves all joints neutral position"""
        self.move_arm_neutral()
        self.move_tower_neutral()

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
        print("PICK PLATE SAFE APPROACH CALLED")

        # open the gripper
        self.gripper_open()

        # Rotate base (R axis) toward plate location
        current_pos = self.get_position()
        self.move_joint_angles(
            R=locations[source].joint_angles[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        # Rotate gripper
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=locations[source].joint_angles[2],
            Y=current_pos[3],
        )

        # Lower z axis to safe_approach_z height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[source].safe_approach_height,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # extend arm over plate and rotate gripper to correct orientation
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=locations[source].joint_angles[3],
        )

        # Lower arm (z axis) to correct plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[source].joint_angles[1] + grip_height_in_steps,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # grip the plate
        self.gripper_close()

        # Move arm with plate back to safe approach height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[source].safe_approach_height,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # retract arm (Y axis) as much as possible (to same Y axis value as Safe location)
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=locations["Safe"].joint_angles[3],
        )

        # move rest of joints to neutral location
        self.move_tower_neutral()
        self.move_arm_neutral()

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
            R=locations[target].joint_angles[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        # Rotate gripper to correct orientation
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=locations[target].joint_angles[2],
            Y=current_pos[3],
        )

        # Lower z axis to safe_approach_z height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[target].safe_approach_height,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # extend arm over plate
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=locations[target].joint_angles[3],
        )

        # lower arm (z axis) to correct plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[target].joint_angles[1] + grip_height_in_steps,
            P=current_pos[2],
            Y=current_pos[3],
        )

        self.gripper_open()

        # Back away using safe approach path
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[target].safe_approach_height,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # retract arm (Y axis) as much as possible (to same Y axis value as Safe location)
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=locations["Safe"].joint_angles[3],
        )

        # move arm to safe location
        self.move_tower_neutral()
        self.move_arm_neutral()

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
            R=locations[source].joint_angles[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        if source_type == "stack":
            # close the gripper
            self.gripper_close()

            # move the arm directly above the stack
            self.move_joint_angles(
                R=locations[source].joint_angles[0],
                Z=current_pos[1],
                P=locations[source].joint_angles[2],
                Y=locations[source].joint_angles[3],
            )

            # decrease the plate crane speed
            self.set_speed(50)

            # move down in z height to tap the top of the plates in stack
            self.move_joint_angles(
                R=locations[source].joint_angles[0],
                Z=locations[source].joint_angles[
                    1
                ],  # this is the only axis that should need to move
                P=locations[source].joint_angles[2],
                Y=locations[source].joint_angles[3],
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
                R=locations[source].joint_angles[0],
                Z=locations[source].joint_angles[1] + grip_height_in_steps,
                P=locations[source].joint_angles[2],
                Y=locations[source].joint_angles[3],
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
        self.move_tower_neutral()
        self.move_arm_neutral()

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
            R=locations[target].joint_angles[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        # Extend arm over plate location (Y axis) and rotate gripper to correct orientation (P axis)
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=current_pos[1],
            P=locations[target].joint_angles[2],
            Y=locations[target].joint_angles[3],
        )

        if target_type == "stack":
            # lower plate crane speed
            self.set_speed(50)

        # Lower arm (z axis) to plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[target].joint_angles[1] + grip_height_in_steps,
            P=current_pos[2],
            Y=current_pos[3],
        )

        if target_type == "stack":
            # return plate crane to sull speed
            self.set_speed(100)

        # open gripper to release the plate
        self.gripper_open()

        self.move_tower_neutral()
        self.move_joints_neutral()

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


if __name__ == "__main__":
    """
    Runs given function.
    """
    s = PlateCrane("/dev/ttyUSB2")
