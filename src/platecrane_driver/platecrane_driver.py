"""Handle Proper Interfacing with the PlateCrane"""
import json
import re
from pathlib import Path
import time

#from platecrane_driver.serial_port import SerialPort      # use when running through wei/REST clients
from serial_port import SerialPort   # use when running through driver
from resource_defs import locations, plate_definitions
from resource_types import PlateResource

#import platecrane_driver.resource_defs as resource_defs


# TODOs: 
# get rid of stack place and nest place, call place_plate_direct
# look into how to slow speed of stack pick and place
# fine tune (z height) of all positions
# check RestNode


class PlateCrane:
    """
    Description:
    Python interface that allows remote commands to be executed to the plate_crane.
    """

    __serial_port: SerialPort

    def __init__(self, host_path="/dev/ttyUSB2", baud_rate=9600):
        """[Summary]

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        self.__serial_port = SerialPort(host_path=host_path, baud_rate=baud_rate)
        self.robot_error = "NO ERROR"
        self.status = 0
        self.error = ""
        self.gripper_length = 0
        # self.plate_above_height = 700 # was 700  # TODO: This seems to change nothing
        # self.plate_pick_steps_stack = 1600
        # self.plate_pick_steps_module = 1400
        # self.plate_lid_steps = 800
        # self.lid_destination_height = 1400

        self.stack_exchange_Z_height = -31887
        self.stack_exchange_Y_axis_steps = 200  # TODO: Find the correct number of steps to move Y axis from the stack to the exchange location
        self.exchange_location = "LidNest2"

        self.robot_status = ""
        self.movement_state = "READY"
        self.platecrane_current_position = None

        self.plate_resources = json.load(
            open(Path(__file__).parent / "plate_resources.json")
        )
        self.stack_resources = json.load(
            open(Path(__file__).parent / "stack_resources.json")
        )

        self.initialize()

    def initialize(self):
        """[Summary]

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        self.get_status()
        if self.robot_status == "0":
            self.home()
        self.platecrane_current_position = self.get_position()

    def home(self, timeout=28):
        """Homes all of the axes. Returns to neutral position (above exchange)


        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        # Moves axes to home position
        command = "HOME\r\n"
        self.__serial_port.send_command(command, timeout)

    # def get_robot_movement_state(self):   # NEVER USED
    #     """Summary

    #     :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
    #     :type [ParamName]: [ParamType](, optional)
    #     ...
    #     :raises [ErrorType]: [ErrorDescription]
    #     ...
    #     :return: [ReturnDescription]
    #     :rtype: [ReturnType]
    #     """

    #     # current_postion = self.get_position()
    #     # print(current_postion)
    #     # print(self.platecrane_current_position)
    #     # if self.platecrane_current_position != current_postion:
    #     #     self.movement_state = "BUSY"
    #     #     self.platecrane_current_position = current_postion
    #     # else:
    #     #     self.movement_state = "READY"
    #     # print(self.movement_state)
    #     self.movement_state = "READY"

    # def wait_robot_movement(self):    # NEVER USED
    #     """Summary

    #     :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
    #     :type [ParamName]: [ParamType](, optional)
    #     ...
    #     :raises [ErrorType]: [ErrorDescription]
    #     ...
    #     :return: [ReturnDescription]
    #     :rtype: [ReturnType]
    #     """

    #     self.get_robot_movement_state()
    #     if self.movement_state != "READY":
    #         self.wait_robot_movement()

    def get_status(self):
        """Checks status of plate_crane

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

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

    def get_location_list(self):
        """Checks status of plate_crane

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

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

    def __update_locations(self, robot_onboard: list, known_locations: list) -> None:
        """Checks the location database on the robot and saves the missing locations to robot onboard

        :param robot_onboard: List of string locations that are saved on the robot
        :type robot_onboard: list

        :param known_locations: List of known locations that should exist on robot database
        :type known_locations: list

        :return: None

        """

        for loc in known_locations:
            if loc not in robot_onboard:
                loc_values = loc.replace(",", "").split(
                    " "
                )  # Removing the ',' caracter
                loc_values[0] = loc_values[0][
                    loc_values[0].find(":") + 1 :
                ]  # Removing the index number from the location name
                self.set_location(
                    loc_values[0],
                    int(
                        loc_values[1],
                        int(loc_values[2], int(loc_values[3]), int(loc_values[4])),
                    ),
                )

    def get_location_joint_values(self, location: str = None) -> list:
        """Checks status of plate_crane

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "GETPOINT " + location + "\r\n"

        joint_values = list(self.__serial_port.send_command(command).split(" "))
        joint_values = [eval(x.strip(",")) for x in joint_values]

        return joint_values

    def get_position(self) -> list:
        """
        Requests and stores plate_crane position.
        Coordinates:
        Z: Vertical axis
        R: Base turning axis
        Y: Extension axis
        P: Gripper turning axis

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        # time.sleep(10)
        command = "GETPOS\r\n"
        time.sleep(2)

        try: 
            current_position = list(self.__serial_port.send_command(command).split(" "))

            print(f"current 1:{current_position}")
            current_position = [eval(x.strip(",")) for x in current_position]

            print(f"current 2:{current_position}")
        except Exception: 
            print("Responses overlapping! waiting 5 seconds to resend command")
            
            time.sleep(5)
            current_position = list(self.__serial_port.send_command(command).split(" "))
            
            
            print(f"current 1:{current_position}")
            current_position = [eval(x.strip(",")) for x in current_position]

            print(f"current 2:{current_position}")

        return current_position

    def set_location(
        self,
        location_name: str = "TEMP_0",
        R: int = 0,
        Z: int = 0,
        P: int = 0,
        Y: int = 0,
    ):
        """Saves a new location onto robot

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
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
        """Deletes a location from the robot's database

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """
        if not location_name:
            raise Exception("No location name provided")

        command = "DELETEPOINT %s\r\n" % (
            location_name
        )  # Command interpreted by Sciclops
        self.__serial_port.send_command(command)

    def gripper_open(self):
        """Opens gripper

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "OPEN\r\n"  # Command interpreted by Sciclops
        self.__serial_port.send_command(command)
        # time.sleep(2)

    def gripper_close(self):
        """Closes gripper

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "CLOSE\r\n"  # Command interpreted by Sciclops
        self.__serial_port.send_command(command)
        # time.sleep(2)

    def check_open(self):
        """Checks if gripper is open

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "GETGRIPPERISOPEN\r\n"  # Command interpreted by Sciclops
        self.__serial_port.send_command(command)

    def check_closed(self):
        """Checks if gripper is closed

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "GETGRIPPERISCLOSED\r\n"  # Command interpreted by Sciclops
        self.__serial_port.send_command(command)

    def jog(self, axis, distance) -> None:
        """Moves the specified axis the specified distance.

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        command = "JOG %s,%d\r\n" % (axis, distance)
        self.__serial_port.send_command(command, timeout=1.5)

    def move_joint_angles(self, R: int, Z: int, P: int, Y: int) -> None:
        """Moves on a single axis, using an existing location on robot's database

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """

        self.set_location("TEMP", R, Z, P, Y)

        command = "MOVE TEMP\r\n"

        try:
            self.__serial_port.send_command(command)

        except Exception as err:
            print(err)
            self.robot_error = err
        else:
            self.move_status = "COMPLETED"
            pass

        #self.delete_location("TEMP", R, Z, P, Y)
        self.delete_location("TEMP")

    def move_single_axis(self, axis: str, loc: str, delay_time=1.5) -> None:
        """Moves on a single axis using an existing location on robot's database

        :param axis: Axis name (R,Z,P,Y)
        :type axis: str
        :param loc: Name of the location.
        :type loc: str

        :raises [PlateCraneLocationException]: [Error for None type locations]
        :return: None
        """

        # TODO:Handle the error raising within error_codes.py
        if not loc:
            raise Exception(
                "PlateCraneLocationException: NoneType variable is not compatible as a location"
            )

        command = "MOVE_" + axis.upper() + " " + loc + "\r\n"
        self.__serial_port.send_command(command, timeout=delay_time)
        self.move_status = "COMPLETED"

    def move_location(self, loc: str = None, move_time: float = 4.7) -> None:
        """Moves all joint to the given location.

        :param loc: Name of the location.
        :type loc: str
        :param move_time: Number of seconds that will take to complete this movement. Defaults to 4.7 seconds which is the longest possible movement time.
        :type move_time: float
        :raises [PlateCraneLocationException]: [Error for None type locations]
        :return: None
        """

        # TODO:Handle the error raising within error_codes.py
        if not loc:
            raise Exception(
                "PlateCraneLocationException: NoneType variable is not compatible as a location"
            )

        cmd = "MOVE " + loc + "\r\n"
        self.__serial_port.send_command(cmd, timeout=move_time)

    def move_tower_neutral(self) -> None:
        """Moves the tower to neutral position

        :return: None
        """
        #self.move_single_axis("Z", "Safe", delay_time=1.5)

        # TODO: This still creates a TEMP position, moves to it, then deletes it after
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations["Safe"].joint_angles[1],
            P=current_pos[2], 
            Y=current_pos[3]
        )

    def move_arm_neutral(self) -> None:
        """Moves the arm to neutral position

        :return: None
        """
        self.move_single_axis("Y", "Safe", delay_time=1)

    def move_gripper_neutral(self) -> None:
        """Moves the gripper to neutral position

        :return: None
        """
        self.move_single_axis("P", "Safe", delay_time=0.3)

    def move_joints_neutral(self) -> None:
        """Moves all joints neutral position

        :return: None
        """
        self.move_arm_neutral()
        self.move_tower_neutral()

    # def move_nest_approach(self, 
    #     location: str, 
    #     plate_type: str,
    #     grip_height_in_steps: int,
    # ) -> None:
    #     """Moves to the entry location of the location that is given. It moves the R,P and Z joints step by step to aviod collisions.

    #     :param source: Name of the source location.
    #     :type source: str
    #     :param height_jog_steps: Number of jogging steps that will be used to move the Z axis to the plate location
    #     :type height_jog_steps: int
    #     :raises [PlateCraneLocationException]: [Error for None type locations]
    #     :return: None
    #     """
    #     # TODO:Handle the error raising within error_codes.py

    #     # if not location:
    #     #     raise Exception(
    #     #         "PlateCraneLocationException: NoneType variable is not compatible as a location"
    #     #     )

    #     # Rotate base (R axis) toward plate location
    #     current_pos = self.get_position()
    #     self.move_joint_angles(
    #         R=locations[location].joint_angles[0], 
    #         Z=current_pos[1],
    #         P=current_pos[2],
    #         Y=current_pos[3],
    #     )

    #     # Lower z axis to safe_approach_z height
    #     current_pos = self.get_position()
    #     self.move_joint_angles(
    #         R=current_pos[0], 
    #         Z=locations[plate_type].safe_approach_height,
    #         P=current_pos[2],
    #         Y=current_pos[3],
    #     )

    #     # extend arm over plate and rotate gripper to correct orientation 
    #     current_pos = self.get_position()
    #     self.move_joint_angles(
    #         R=current_pos[0], 
    #         Z=current_pos[1],
    #         P=locations[location].joint_angles[2], 
    #         Y=locations[location].joint_angles[3],
    #     )

    #     # lower arm (z axis) to correct plate grip height
    #     current_pos = self.get_position()
    #     self.move_joint_angles(
    #         R=current_pos[0], 
    #         Z=locations[location].joint_angles[1] + grip_height_in_steps,
    #         P=current_pos[2],
    #         Y=current_pos[3],
    #     )

        





    #      # get joint values of given location
    #     joint_values = resource_defs.location.joint_angles
    #     current_pos = self.get_position() # get joint values of current position

    #     self.plate_above_height = resource_defs.location.safe_approach_height
    #     module_safe_height = joint_values[1] + self.plate_above_height
    #     self.module_safe_height = module_safe_height

    #     height_jog_steps = current_pos[1] - module_safe_height # first step of safe approach

    #     self.move_joint_angles(R=resource_defs.location.joint_angles[0], Z=current_pos[1], P=current_pos[2], Y=current_pos[3])
    #     # self.move_single_axis("R", location) # TODO: adjust to use config instead of values stored in platecrane
    #     current_pos = self.get_position() # get joint values of current position
    #     self.move_joint_angles(R=current_pos[0], Z=current_pos[1], P=resource_defs.location.joint_angles[2], Y=current_pos[3])
    #     # self.move_single_axis("P", location)
    #     self.jog("Z", -height_jog_steps)

    def pick_plate_safe_approach(
        self, 
        source: str, 
        plate_type: str,
        grip_height_in_steps: int, 
    ) -> None:
        """Pick a module plate from a module location.

        :param source: Name of the source location.
        :type source: str
        :param height_jog_steps: Number of jogging steps that will be used to move the Z axis to the plate location
        :type height_jog_steps: int
        :raises [PlateCraneLocationException]: [Error for None type locations]
        :return: None
        """

        # MOVE TO PICK UP PLATE
        self.move_joints_neutral()
        self.gripper_open()

        # Rotate base (R axis) toward plate location
        current_pos = self.get_position()
        self.move_joint_angles(
            R=locations[source].joint_angles[0], 
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        # Lower z axis to safe_approach_z height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0], 
            Z=locations[plate_type].safe_approach_height,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # extend arm over plate and rotate gripper to correct orientation 
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0], 
            Z=current_pos[1],
            P=locations[source].joint_angles[2], 
            Y=locations[source].joint_angles[3],
        )

        # lower arm (z axis) to correct plate grip height
        current_pos = self.get_position()
        self.move_joint_angles(
            R=current_pos[0], 
            Z=locations[source].joint_angles[1] + grip_height_in_steps,
            P=current_pos[2],
            Y=current_pos[3],
        )

        # grip the plate
        self.gripper_close()

        # MOVE WITH PLATE SAFELY BACK TO NEUTRAL
        # Move arm up to safe approach height
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
        self.move_arm_neutral()


    # def place_plate_safe_approach(
    #     self, target: str, height_offset: int = 0
    # ) -> None:
    #     """Place a module plate onto a module location.

    #     :param target: Name of the target location.
    #     :type target: str
    #     :param height_jog_steps: Number of jogging steps that will be used to move the Z axis to the plate location
    #     :type height_jog_steps: int
    #     :raises [PlateCraneLocationException]: [Error for None type locations]
    #     :return: None
    #     """

    #     self.move_joints_neutral()

    #     self.move_nest_approach(target) # faces destination, lowers to safe approach height
    #     current_pos = self.get_position()
    #     self.move_joint_angles(R=current_pos[0], Z=current_pos[1], P=current_pos[2], Y=resource_defs.source.joint_angless[3])
    #     self.move_single_axis("Y", target)
    #     # self.jog("Z", -(self.plate_pick_steps_module - height_offset))
    #     self.jog("Z", (resource_defs.target.joint_angles[1] - self.module_safe_height + height_offset)) #TODO: test, replace height offsetwith plate dimensions
    #     self.gripper_open()
    #     self.jog("Z", resource_defs.target.safe_approach_height)

        self.move_arm_neutral()

    def pick_plate_direct(
            self, 
            source: str, 
            source_type: str, 
            plate_type: str, 
            # height_offset: int = 0, 
            grip_height_in_steps: int,
            has_lid: bool,
            incremental_lift: bool=False
    ) -> None:
        """Pick a stack plate from stack location.

        :param source: Name of the source location.
        :type source: str
        :raises [PlateCraneLocationException]: [Error for None type locations]
        :return: None
        """

        print("PICK PLATE DIRECT CALLED")
        self.move_joints_neutral()
        current_pos = self.get_position()

        # rotate R axis (base rotation) over the plate
        self.move_joint_angles(
            R=locations[source].joint_angles[0], 
            Z=current_pos[1], 
            P=current_pos[2], 
            Y=current_pos[3],
        )
        # self.move_single_axis("R", source)

        if source_type == "stack":
            self.gripper_close()
            # self.move_location(source)

            # tap arm on top of plate stack to determine stack height
            self.move_joint_angles(
                R=locations[source].joint_angles[0], 
                Z=locations[source].joint_angles[1], 
                P=locations[source].joint_angles[2], 
                Y=locations[source].joint_angles[3],
            )

            # move up, open gripper, grab plate at correct height
            self.jog("Z", 1000) 
            self.gripper_open()

            # calculate z travel from grip height with/without lid
            if has_lid: 
                z_jog_down_from_plate_top = PlateResource.convert_to_steps(plate_definitions[plate_type].plate_height_with_lid) - grip_height_in_steps
                # z_jog_down_from_plate_top = plate_definitions[plate_type].plate_height_with_lid - grip_height_in_steps
            else: # does not have lid
                z_jog_down_from_plate_top = PlateResource.convert_to_steps(plate_definitions[plate_type].plate_height) - grip_height_in_steps
                # z_jog_down_from_plate_top = plate_definitions[plate_type].plate_height - grip_height_in_steps

            # move down to correct z height to grip plate 
            self.jog("Z", -(1000 + z_jog_down_from_plate_top))


            #self.jog("Z", -1000 + plate_definitions[plate_type].grip_height + height_offset) # move down to grab height location
            
            # current_pos = self.get_position()
            # self.move_joint_angles(
            #     R=current_pos[0],
            #     Z=current_pos
            # )
        
        else: # if source_type == nest:
            self.gripper_open()

            # TODO: might need to account for if the plate is a lid here?
            self.move_joint_angles(
                R=locations[source].joint_angles[0], 
                Z=locations[source].joint_angles[1] + grip_height_in_steps, 
                P=locations[source].joint_angles[2], 
                Y=locations[source].joint_angles[3],
            )
            
        self.gripper_close()

        if incremental_lift: 
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)
            self.jog("Z", 100)

        self.move_tower_neutral()

        self.move_arm_neutral()

        print("PICK PLATE DIRECT FINISHED")

    def place_plate_direct(
            self, 
            target: str,
            grip_height_in_steps: str, 
        ) -> None:

        """Place a stack plate either onto the exhange location or into a stack

        :param target: Name of the target location. Defults to None if target is None, it will be set to exchange location.
        :type target: str
        :return: None
        """

        self.move_arm_neutral()

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

        # Lower arm (z axis) to plate grip height
        current_pos=self.get_position()
        self.move_joint_angles(
            R=current_pos[0],
            Z=locations[target].joint_angles[1] + grip_height_in_steps,
            P=current_pos[2],
            Y=current_pos[3],
        )

        self.gripper_open()

        self.move_tower_neutral()
        self.move_joints_neutral()

    def _is_location_joint_values(self, location: str, name: str = "temp") -> str:
        """
        If the location was provided as joint values, transfer joint values into a saved location on the robot and return the location name.
        If location parameter is a name of an already saved location, do nothing.

        :param location: Location to be checked if this is an already saved location on the robot database or a new location with 4 joint values
        :type location: string
        :param name: Location name to be used to save a new location if the location parameter was provided as 4 joint values
        :type name: string
        :raises [ErrorType]: [ErrorDescription]
        :return: location_name = Returns the location name that is saved on robot database with location joint values
        :rtype: str
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
        """
        Remove the plate lid

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :param plate_type: Type of the plate
        :type plate_type: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """
        # self.get_new_plate_height(plate_type) # pulls plate dimenstions, now do from config
        #TODO: pull plate dimenstions?
        # plate_height = resource_defs.plate_type.plate_height

        # target_offset = (
        #     2 * self.plate_above_height - self.plate_pick_steps_stack + self.lid_destination_height
        #     # + height_offset
        # )  # Finding the correct target hight when only transferring the plate lid
        # target_loc = self.get_location_joint_values(target)
        # remove_lid_target = "Temp_Lid_Target_Loc"

        # self.set_location(
        #     remove_lid_target,
        #     target_loc[0],
        #     target_loc[1] - target_offset,
        #     target_loc[2],
        #     target_loc[3],
        # )
        # self.plate_pick_steps_stack = self.plate_lid_steps + height_offset

        source_grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].lid_removal_grip_height + height_offset)
        target_grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].plate_height_with_lid - plate_definitions[plate_type].lid_height + height_offset)

        self.transfer(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=True,
            source_grip_height_in_steps=source_grip_height_in_steps,
            target_grip_height_in_steps=target_grip_height_in_steps,
            incremental_lift = True,
        )


    def replace_lid(
        self,
        source: str,
        target: str,
        plate_type: str,
        height_offset: int = 0,
    ) -> None:
        """
        Replace the lid back to the plate

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :param plate_type: Type of the plate
        :type plate_type: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """

        # self.get_new_plate_height(plate_type)

        # target_offset = (
        #     2 * self.plate_above_height - self.plate_pick_steps_stack + self.lid_destination_height
        # )

        # source_loc = self.get_location_joint_values(source)
        # remove_lid_source = "Temp_Lid_Source_loc"

        # self.set_location(
        #     remove_lid_source,
        #     source_loc[0],
        #     source_loc[1] - target_offset,
        #     source_loc[2],
        #     source_loc[3],
        # )
        # self.plate_pick_steps_stack = self.plate_lid_steps + height_offset

        source_grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].lid_grip_height + height_offset)
        target_grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].lid_removal_grip_height + height_offset)


        self.transfer(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            source_grip_height_in_steps=source_grip_height_in_steps,
            target_grip_height_in_steps=target_grip_height_in_steps,
            is_lid=True,
        )


    def get_new_plate_height(self, plate_type):
        """
        Gets the new plate height values for the given plate_type
        :param plate_type: Plate type.
        :type source: str
        :return: None
        """
        if plate_type not in self.plate_resources.keys():
            raise Exception("Unkown plate type")
        self.plate_above_height = self.plate_resources[plate_type]["plate_above_height"]
        self.plate_lid_steps = self.plate_resources[plate_type]["plate_lid_steps"]
        self.plate_pick_steps_stack = self.plate_resources[plate_type][
            "plate_pick_steps_stack"
        ]
        self.plate_pick_steps_module = self.plate_resources[plate_type][
            "plate_pick_steps_module"
        ]
        self.lid_destination_height = self.plate_resources[plate_type]["lid_destination_height"]

    def get_stack_resource(
        self,
    ):
        """
        Gets the new plate height values for the given plate_type
        :param plate_type: Plate type.
        :type source: str
        :return: None
        """
        pass

    def update_stack_resource(self):
        """
        Gets the new plate height values for the given plate_type
        :param plate_type: Plate type.
        :type source: str
        :return: None
        """
        pass

    def transfer(
        self,
        source: str,
        target: str,
        plate_type: str,
        height_offset: int = 0, # units = mm
        is_lid: bool = False,
        has_lid: bool = False,
        source_grip_height_in_steps: int = None,  # if iremoving/replacing lid
        target_grip_height_in_steps: int = None,  # if iremoving/replacing lid
        incremental_lift: bool = False,
        # use_safe_approach: bool = False
    ) -> None:
        """
        Handles the transfer request

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :param plate_type: Type of the plate
        :type plate_type: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """

        # # self.get_stack_resource() # doesn't do anything
        # if plate_type:
        # #     self.get_new_plate_height(plate_type) # TODO: replace with pulling plate dimenstions from config (or just do later as needed), for now just putting plate type in global
        #     self.plate_type = plate_type
        # # if source_type == "stack" or target_type == "stack":
        # #     self.stack_transfer(source, target, source_type, target_type, height_offset, incremental_lift)
        # # elif source_type == "module" and target_type == "module":
        # #     self.module_transfer(source, target, height_offset)

        # Extract the source and target location_types
        source_type = locations[source].location_type
        target_type = locations[target].location_type

        # PICK HEIGHT 
        # Determine pick height from bottom of plate (converted to z motor steps)

        if not is_lid: 
            grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].grip_height + height_offset)
            source_grip_height_in_steps = grip_height_in_steps
            target_grip_height_in_steps = grip_height_in_steps
        # if is_lid: 
        #     grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].lid_grip + height_offset)

        #     # calculations

            
        # else: # not a lid
        #     grip_height_in_steps = PlateResource.convert_to_steps(plate_definitions[plate_type].grip_height + height_offset)

        # # Define temporary pick location in plate crane memory #TODO: change this so we're never setting new location in the plate crane
        # self.set_location(
        #     "pick_location_temp", 
        #     locations[source].joint_angles[0], 
        #     locations[source].joint_angles[1] + pick_height_in_steps, 
        #     locations[source].joint_angles[2], 
        #     locations[source].joint_angles[3], 
        # )

        # # PLACE HEIGHT
        # # Define temporary place location based on pick_height_in_steps variable. 
        # self.set_location


        # is safe approach required for source and/or target?
        source_use_safe_approach = False if locations[source].safe_approach_height == 0 else True
        target_use_safe_approach = False if locations[target].safe_approach_height == 0 else True
        print(f"Source safe approach: {source_use_safe_approach}")
        print(f"Target safe approach: {target_use_safe_approach}")

        # Grab from source location
        if source_type == "stack":
            # self.stack_pick(
            #     source=source, 
            #     source_type=source_type, 
            #     plate_type=plate_type, 
            #     grip_height_in_steps=grip_height_in_steps,
            #     has_lid=has_lid,
            #     incremental_lift=incremental_lift
            # )
            self.pick_plate_direct(
                source=source,
                source_type=source_type, # "stack"
                plate_type=plate_type,
                grip_height_in_steps=source_grip_height_in_steps,
                has_lid=has_lid,
                incremental_lift=incremental_lift
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


            # self.nest_pick(
            #     source=source, 
            #     plate_type=plate_type, 
            #     #height_offset=height_offset, 
            #     grip_height_in_steps=grip_height_in_steps,
            #     incremental_lift=incremental_lift, 
            #     use_safe_approach=source_use_safe_approach,
            # )
        else: 
            raise Exception(
                "Source location type not defined correctly"
            )
        

        # PLACE PLATE
        if target_type == "stack": 
            self.stack_place(
                target=target,
                grip_height_in_steps=target_grip_height_in_steps,
            )
        elif target_type == "nest": 
            self.nest_place(
                target=target, 
                target_type=target_type,
                plate_type=plate_type,
                grip_height_in_steps=target_grip_height_in_steps,
                use_safe_approach=target_use_safe_approach,
            )
        else: 
            raise Exception(
                "Target location type not defined correctly"
            )


        self.move_joints_neutral()
        self.move_joint_angles(
            R=locations["Safe"].joint_angles[0], 
            Z=locations["Safe"].joint_angles[1], 
            P=locations["Safe"].joint_angles[2], 
            Y=locations["Safe"].joint_angles[3]
        )

        # self.update_stack_resource()  #TODO: does nothing, could be nice preventing slamming

    def stack_pick(
        self,
        source: str,
        source_type: str,
        plate_type: str,
        # height_offset: int = 0,
        grip_height_in_steps: int,
        has_lid: bool,
        incremental_lift: bool = False,
    ) -> None:
        """
        Transfer a plate plate from a plate stack to the exchange location or make a transfer in between stacks and stack entry locations

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """

        # source = self._is_location_joint_values(location=source, name="source") # TODO: removed coordinate functionality for simplicity

        # block here sets source location as new location in platecrane, can remove
        # source_loc = self.get_location_joint_values(source) 
        # stack_source = "stack_source_loc"
        # source_offset = self.plate_above_height + height_offset

        # self.set_location(
        #     stack_source,
        #     source_loc[0],
        #     source_loc[1] + source_offset,
        #     source_loc[2],
        #     source_loc[3],
        # )
        # self.pick_plate_direct(stack_source, "stack", height_offset=height_offset, is_lid=incremental_lift)
        self.pick_plate_direct(
            source=source, 
            source_type=source_type, 
            plate_type=plate_type, 
            # height_offset=height_offset, 
            grip_height_in_steps=grip_height_in_steps,
            has_lid=has_lid,
            incremental_lift=incremental_lift
        )


    def stack_place(
        self,
        target: str,
        grip_height_in_steps: str,
    ) -> None:
        """
        Transfer a plate plate from a plate stack to the exchange location or make a transfer in between stacks and stack entry locations

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """
        
        # TODO: Do we even need this funtion? 
        self.place_plate_direct(
            target=target, 
            grip_height_in_steps=grip_height_in_steps,
        )


    # def nest_pick(
    #     self, 
    #     source: str, 
    #     plate_type: str,  
    #     grip_height_in_steps: int,
    #     incremental_lift: bool = False, 
    #     use_safe_approach: bool = False
    # ) -> None:
    #     """
    #     Transfer a plate in between two modules using source and target locations

    #     :param source: Source location, provided as either a location name or 4 joint values.
    #     :type source: str
    #     :param target: Target location, provided as either a location name or 4 joint values.
    #     :type target: str
    #     :raises [ErrorType]: [ErrorDescription]
    #     :return: None
    #     """
    #     self.move_joints_neutral()
    #     #source = self._is_location_joint_values(location=source, name="source")
        
    #     if use_safe_approach:
    #         self.pick_plate_safe_approach(
    #             source=source, 
    #             plate_type=plate_type, 
    #             grip_height_in_steps=grip_height_in_steps,
    #         )
    #     else:
    #         self.pick_plate_direct(
    #             source=source, 
    #             source_type="nest",
    #             plate_type=plate_type,
    #             grip_height_in_steps=grip_height_in_steps,
    #             incremental_lift=incremental_lift,
    #         )

    def nest_place(
        self, 
        target: str,
        target_type: str,
        plate_type: str,
        grip_height_in_steps: int, 
        use_safe_approach: bool = False
    ) -> None:
        """
        Transfer a plate in between two modules using source and target locations

        :param source: Source location, provided as either a location name or 4 joint values.
        :type source: str
        :param target: Target location, provided as either a location name or 4 joint values.
        :type target: str
        :raises [ErrorType]: [ErrorDescription]
        :return: None
        """

        # Rotate base (R axix) toward target location
        current_pos = self.get_position()
        self.move_joint_angles(
            R=locations[target].joint_angles[0],
            Z=current_pos[1],
            P=current_pos[2],
            Y=current_pos[3],
        )

        if use_safe_approach: 
            # Lower z axis to safe_approach_z height
            current_pos = self.get_position()
            self.move_joint_angles(
                R=current_pos[0], 
                Z=locations[target].safe_approach_height,
                P=current_pos[2],
                Y=current_pos[3],
            )

            # extend arm over plate and rotate gripper to correct orientation 
            current_pos = self.get_position()
            self.move_joint_angles(
                R=current_pos[0], 
                Z=current_pos[1],
                P=locations[target].joint_angles[2], 
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
            time.sleep(2)

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

        else: 
            # extend arm over plate and rotate gripper to correct orientation 
            current_pos = self.get_position()
            self.move_joint_angles(
                R=current_pos[0], 
                Z=current_pos[1],
                P=locations[target].joint_angles[2], 
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


        self.move_tower_neutral()
        self.move_arm_neutral()

        
if __name__ == "__main__":
    """
    Runs given function.
    """
    s = PlateCrane("/dev/ttyUSB4")
    # s.initialize()
    # s.home()
    stack4 = "Stack4"
    stack5 = "Stack5"
    solo6 = "Solo.Position6"
    solo4 = "Solo.Position4"
    solo3 = "Solo.Position3"
    target_loc = "HidexNest2"
    lidnest3 = "LidNest3"
    sealer = "SealerNest"
    # s.move_location("Safe")

# TESTING
# s.pick_stack_plate("Stack1")
# a = s.get_position()
# s.set_location("LidNest3",R=231449,Z=-31500,P=484,Y=-306)

# s.set_location("Hidex.Nest",R=a[0],Z=a[1],P=a[2],Y=a[3])
# s.place_module_plate("Hidex.Nest")
# s.move_single_axis("Z","Hidex.Nest")
# s.transfer("Hidex.Nest","Solo.Position1",source_type="module",target_type="stack",height_offset=800)
# s.transfer("Stack1", "PeelerNest",source_type="stack",target_type="stack")

# s.place_module_plate()
# s.get_location_list()

# s.move_joints_neutral()
# s.move_single_axis("R", "Safe", delay_time=1)
# s.set_location("Safe",R=195399,Z=0,P=0,Y=0)
# s.set_location("LidNest2",R=131719,Z=-31001,P=-5890,Y=-315)
# s.transfer(source="LidNest1",target="LidNest2",source_type="stack",target_type="stack", plate_type="96_well")

# s.transfer(source="LidNest2",target="LidNest3",source_type="stack",target_type="stack", plate_type="96_well")
# s.transfer("Stack1","Stack1")
# s.free_joints()
# s.lock_joints()

# s.set_location("LidNest3",R=99817,Z=-31001,P=-5890,Y=-315)

# s.get_location_joint_values("HidexNest2")
# s.set_location("HidexNest2", R=210015,Z=-30400,P=490,Y=2323)

# s.transfer(stack5, solo4, source_type = "stack", target_type = "module", plate_type = "96_deep_well")
# s.transfer(solo4, stack5, source_type = "module", target_type = "stack", plate_type = "96_deep_well")

# s.remove_lid(source = "LidNest1", target="LidNest2", plate_type="96_well")
# s.transfer("Stack4", solo3, source_type = "stack", target_type = "stack", plate_type = "tip_box_lid_off")
# s.remove_lid(source = solo6, target="LidNest3", plate_type="tip_box_lid_on")
# s.replace_lid(source = "LidNest3", target = solo6, plate_type = "tip_box_lid_on")
# s.replace_lid(source = "LidNest2", target = solo4, plate_type = "96_well")
# s.transfer(solo4, stack5, source_type = "module", target_type = "stack", plate_type = "96_well")
# s.transfer(solo6, "Stack2", source_type = "module", target_type = "stack", plate_type = "tip_box_lid_on")


#    Crash error outputs 21(R axis),14(z axis), 02 Wrong location name. 1400 (Z axis hits the plate), 00 success
# TODO: Need a response handler function. Unkown error messages T1, ATS, TU these are about connection issues (multiple access?)
# TODO: Slow the arm before hitting the plate in pick_stack_plate
# TODO: Create a plate detect function within pick stack plate function
# TODO: Maybe write another pick stack funtion to remove the plate detect movement
