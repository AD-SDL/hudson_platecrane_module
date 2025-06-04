"""Driver for the Hudson Robotics Sciclops robot."""

import re
import time
from typing import Union

import usb.core
import usb.util

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
        self.host_path = self.connect_sciclops()
        self.TEACH_PLATE = 15.0
        self.STD_FINGER_LENGTH = 17.2
        self.COMPRESSION_DISTANCE = 3.35
        self.current_pos = [0, 0, 0, 0]
        # self.NEST_ADJUSTMENT = 20.0
        self.STATUS = 0
        # self.VERSION = 0
        # self.CONFIG = 0
        self.ERROR = ""
        self.GRIPLENGTH = 0
        # self.COLLAPSEDDISTANCE = 0
        # self.STEPSPERUNIT = [0, 0 ,0, 0]
        # self.HOMEMSG = ""
        # self.OPENMSG = ""
        # self.CLOSEMSG = ""
        self.locations = self.load_locations()
        self.success_count = 0
        self.status = self.get_status()
        self.error = self.get_error()
        self.movement_state = "READY"

    def __del__(self):
        """Destructor for the SCICLOPS driver. Disconnects from the Sciclops robot."""
        self.disconnect_robot()

    def connect_sciclops(self):
        """
        Connect to USB device. If wrong device, inform user
        """
        host_path = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)

        if host_path is None:
            raise Exception("Could not establish connection.")

        else:
            print("Device Connected")
            return host_path

    def disconnect_robot(self):
        """Disconnects from the sciclops robot."""
        try:
            usb.util.dispose_resources(self.host_path)
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
                # Z:-397.1688, R:134.9400, Y:172.5228, P:9.7159
                # "pos": {"Z":-397.6188, "R":133.5247, "Y":172.5228, "P":9.7159},
                "pos": {"Z": -397.1688, "R": 134.7400, "Y": 172.5228, "P": 9.7159},
                "type": "stack",
            },
            "stack2": {
                # "pos": {"Z":-395.2313, "R":151.3112, "Y":173.0375, "P":11.392},
                "pos": {"Z": -397.2875, "R": 152.8218, "Y": 172.5166, "P": 9.7159},
                "type": "stack",
            },
            "stack3": {  # Z:-397.3563, R:170.8571, Y:172.5166, P:9.7159
                # "pos": {"Z":-397.5500, "R":169.4188, "Y":171.8531, "P":10.2557},
                "pos": {"Z": -397.3563, "R": 170.8571, "Y": 172.5166, "P": 9.7159},
                "type": "stack",
            },
            "stack4": {  # Z:-396.1000, R:188.8588, Y:172.5166, P:9.7159
                # "pos": {"Z":-397.4563, "R":187.3500, "Y":171.2330, "P":10.2557},
                "pos": {"Z": -396.1000, "R": 188.6588, "Y": 172.5166, "P": 9.7159},
                "type": "stack",
            },
            "stack5": {  # Z:-394.4875, R:206.8553, Y:172.5166, P:9.7159
                # "pos": {"Z":-397.8000, "R":205.3147, "Y":171.2330, "P":10.2557},
                "pos": {"Z": -394.4875, "R": 206.6553, "Y": 172.5166, "P": 9.7159},
                "type": "stack",
            },
            "lidnest1": {
                # Z:-385.0500, R:170.6876, Y:27.2231, P:10.2841
                # "pos": {"Z":-388.4625, "R":169.4965, "Y":25.6853, "P":10.2557}
                # "pos": {"Z":-388.8563, "R":170.8412, "Y":25.6977, "P":10.2841},
                "pos": {"Z": -388.8563, "R": 170.6876, "Y": 27.2231, "P": 10.2841},
                "type": "nest",
            },
            "lidnest2": {  # Z:-384.9375, R:202.8318, Y:26.8139, P:10.2841
                # "pos": {"Z":-388.4625, "R":201.6388, "Y":25.6853, "P":10.2557},
                # "pos": {"Z":-388.4625, "R":203.1618, "Y":26.1503, "P":10.2557},
                "pos": {"Z": -388.4625, "R": 202.8318, "Y": 26.8139, "P": 10.2841},
                "type": "nest",
            },
            # "exchange": {
            #     # "pos": {"Z": -417.2938, "R": 305.5588, "Y": 143.8300, "P": 198.2102 - 181},
            #     "pos": {"Z": -418.2938, "R": 305.75, "Y": 142.8300, "P": 198.2102 - 181.5},
            #     "type": "nest"
            # }, # "Z":-414.8438, "R":288.9053, "Y":192.5526, "P":22.7841
            "exchange": {  # new Z:-415.5188, R:288.8029, Y:193.2781, P:22.7841
                # "pos": {"Z": -417.2938, "R": 305.5588, "Y": 143.8300, "P": 198.2102 - 181},
                # "pos": {"Z":-415.8438, "R":288.9053, "Y":192.5526, "P":22.7841},
                "pos": {"Z": -415.8438, "R": 288.8029, "Y": 193.2781, "P": 22.7841},
                "type": "nest",
            },
            "neutral": {
                "pos": {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955},
                "type": "point",
            },
        }

        return locations

    def send_command(self, command):
        """
        Sends provided command to Sciclops and stores data outputted by the sciclops.
        """

        self.host_path.write(4, command)

        response_buffer = "Write: " + command
        msg = None

        # Adds SciClops output to response_buffer
        while msg != command:
            # or "success" not in msg or "error" in msg
            try:
                response = self.host_path.read(0x83, 200, timeout=1000)
            except Exception:
                break
            msg = "".join(chr(i) for i in response)
            response_buffer = response_buffer + "Read: " + msg
        # if not command.startswith("STATUS"):
        print(response_buffer)

        self.success_count = self.success_count + response_buffer.count("0000 Success")

        self.get_error(response_buffer)

        return response_buffer

    def get_error(self, response_buffer=None):
        """
        Gets error message from the feedback.
        """

        if not response_buffer:
            return

        output_line = response_buffer[response_buffer[:-1].rfind("\n") :]
        exp = r"(\d)(\d)(\d)(\d)(.*\w)"  # Format of feedback that indicates an error message
        output_line = re.search(exp, response_buffer)

        try:
            # Checks if specified format is found in the last line of feedback
            if output_line[5][5:9] != "0000":
                self.ERROR = "ERROR: %s" % output_line[5]

        except Exception:
            pass

    ################################
    # Individual Command Functions

    def get_position(self):
        """
        Requests and stores sciclops position.
        Coordinates:
        Z: Vertical axis
        R: Base turning axis
        Y: Extension axis
        P: Gripper turning axis
        """

        command = "GETPOS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)
        print(out_msg)

        try:
            # Checks if specified format is found in feedback
            exp = r"Z:([-.\d]+), R:([-.\d]+), Y:([-.\d]+), P:([-.\d]+)"  # Format of coordinates provided in feedback
            find_current_pos = re.search(exp, out_msg)
            self.current_pos = [
                float(find_current_pos[1]),
                float(find_current_pos[2]),
                float(find_current_pos[3]),
                float(find_current_pos[4]),
            ]

            print(self.current_pos)
            return self.current_pos
        except Exception:
            import traceback

            traceback.print_exc()

    def get_status(self):
        """
        Checks status of Sciclops
        """

        command = "STATUS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
            find_status = re.search(exp, out_msg)
            self.status = find_status[1]

            print(self.status)

        except Exception:
            pass

    def check_complete(self):
        """
        Checks to see if current sciclops action has completed
        """
        command = "STATUS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
            find_status = re.search(exp, out_msg)
            self.status = find_status[1]
            self.movement_state = "READY"

            return True

        except Exception:
            self.movement_state = "BUSY"

            return False
        finally:
            time.sleep(0.1)

    def check_complete_loop(self):
        """
        continuously runs check_complete until it returns True
        """
        a = False
        while not a:
            a = self.check_complete()

        print("ACTION COMPLETE")

    def get_version(self):
        """
        Checks version of Sciclops
        """

        command = "VERSION\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
            find_version = re.search(exp, out_msg)
            self.VERSION = find_version[1]

            print(self.VERSION)

        except Exception:
            pass

    # TODO: swings outward and collides with pf400
    def reset(self):
        """
        Resets Sciclops
        """

        self.set_speed(5)

        command = "RESET\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
            find_reset = re.search(exp, out_msg)
            self.RESET = find_reset[1]

            print(self.RESET)

        except Exception:
            pass

    def get_config(self):
        """
        Checks configuration of Sciclops
        """

        command = "GETCONFIG\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the configuration
            find_config = re.search(exp, out_msg)
            self.CONFIG = find_config[1]

            print(self.CONFIG)

        except Exception:
            pass

    def get_grip_length(self):
        """
        Checks current length of the gripper (units unknown) of Sciclops
        """

        command = "GETGRIPPERLENGTH\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the gripper length
            find_grip_length = re.search(exp, out_msg)
            self.GRIPLENGTH = find_grip_length[1]

            print(self.GRIPLENGTH)

        except Exception:
            pass

    def get_collapsed_distance(self):
        """
        ???
        """

        command = "GETCOLLAPSEDISTANCE\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the collapsed distance
            find_collapsed_distance = re.search(exp, out_msg)
            self.COLLAPSEDDISTANCE = find_collapsed_distance[1]

            print(self.COLLAPSEDDISTANCE)

        except Exception:
            pass

    def get_steps_per_unit(self):
        """
        ???
        """

        command = "GETSTEPSPERUNIT\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"Z:([-.\d]+),R:([-.\d]+),Y:([-.\d]+),P:([-.\d]+)"  # Format of the coordinates provided in feedback
            find_steps_per_unit = re.search(exp, out_msg)
            self.STEPSPERUNIT = [
                float(find_steps_per_unit[1]),
                float(find_steps_per_unit[2]),
                float(find_steps_per_unit[3]),
                float(find_steps_per_unit[4]),
            ]

            print(self.STEPSPERUNIT)

        except Exception:
            pass

    def home(self, axis=""):
        """
        Homes all of the axes. Returns to neutral position (above exchange)
        """

        # Moves axes to home position
        command = "HOME\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            home_msg = re.search(exp, out_msg)
            self.HOMEMSG = home_msg[1]

            print(self.HOMEMSG)
        except Exception:
            pass

        # Moves axes to neutral position (above exchange)
        self.move_loc("neutral")

    def open(self):
        """
        Opens gripper
        """

        command = "OPEN\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            open_msg = re.search(exp, out_msg)
            self.OPENMSG = open_msg[1]
            print(self.OPENMSG)

        except Exception:
            pass

    def close(self):
        """
        Closes gripper
        """

        command = "CLOSE\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            close_msg = re.search(exp, out_msg)
            self.CLOSEMSG = close_msg[1]

            print(self.CLOSEMSG)
        except Exception:
            pass

    def check_open(self):
        """
        Checks if gripper is open
        """

        command = "GETGRIPPERISOPEN\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line answers if the gripper is open
            check_open_msg = re.search(exp, out_msg)
            self.CHECKOPENMSG = check_open_msg[1]

            print(self.CHECKOPENMSG)
        except Exception:
            pass

    def check_closed(self):
        """
        Checks if gripper is closed
        """

        command = "GETGRIPPERISCLOSED\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line answers if the gripper is closed
            check_closed_msg = re.search(exp, out_msg)
            self.CHECKCLOSEDMSG = check_closed_msg[1]

            print(self.CHECKCLOSEDMSG)

        except Exception:
            pass

    def check_plate(self):
        """
        ???
        """

        command = "GETPLATEPRESENT\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates ???
            check_plate_msg = re.search(exp, out_msg)
            self.CHECKPLATEMSG = check_plate_msg[1]

            print(self.CHECKPLATEMSG)

        except Exception:
            pass

    def set_speed(self, speed):
        """
        Changes speed of Sciclops
        """

        command = "SETSPEED %d\r\n" % speed  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates success message
            set_speed_msg = re.search(exp, out_msg)
            self.SETSPEEDMSG = set_speed_msg[1]
            print(self.SETSPEEDMSG)
        except Exception:
            pass

    def list_points(self):
        """
        Lists all of the preset points
        """

        command = "LISTPOINTS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            list_point_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.LISTPOINTS = out_msg[list_point_msg_index + 4 :]
            print(self.LISTPOINTS)
        except Exception:
            pass

    def jog(self, axis, distance):
        """
        Moves the specified axis the specified distance.
        """

        command = "JOG %s,%d\r\n" % (axis, distance)  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            jog_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.JOGMSG = out_msg[jog_msg_index + 4 :]
            print(self.JOGMSG)
        except Exception:
            pass

    def loadpoint(self, R, Z, P, Y):
        """
        Adds point to listpoints function
        """

        command = "LOADPOINT R:%s, Z:%s, P:%s, Y:%s, R:%s\r\n" % (
            R,
            Z,
            P,
            Y,
            R,
        )  # Command interpreted by Sciclops
        out_msg = self.send_command(command)
        try:
            # Checks if specified format is found in feedback
            loadpoint_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.LOADPOINTMSG = out_msg[loadpoint_msg_index + 5 :]
        except Exception:
            pass

    def deletepoint(self, R, Z, P, Y):
        """
        Deletes point from listpoints function
        """

        command = "DELETEPOINT R:%s\r\n" % R  # Command interpreted by Sciclops
        out_msg = self.send_command(command)
        try:
            # Checks if specified format is found in feedback
            deletepoint_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.DELETEPOINTMSG = out_msg[deletepoint_msg_index + 5 :]
        except Exception:
            pass

    def move(self, R, Z, P, Y):
        """
        Moves to specified coordinates
        """

        self.loadpoint(R, Z, P, Y)

        command = "MOVE R:%s\r\n" % R
        out_msg_move = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            move_msg_index = out_msg_move.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.MOVEMSG = out_msg_move[move_msg_index + 4 :]
        except Exception:
            pass

        # self.check_complete_loop()

        self.deletepoint(R, Z, P, Y)

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
        self.set_speed(100)
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
            self.jog("Z", -5)
            self.jog("Z", 10)
            self.jog("Z", -5)
            self.jog("Z", 10)
            self.jog("Z", -5)
            self.jog("Z", 10)
        self.set_speed(20)
        self.move_above_loc(location_name)

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
            self.set_speed(100)
            self.jog("Z", 1000)
        elif location.get("type") == "nest":
            self.move_loc_at_height(
                location_name, location["pos"]["Z"] + grip_height + 10
            )
            self.set_speed(1)
            self.move_loc_at_height(location_name, location["pos"]["Z"] + grip_height)
            self.open()
            self.set_speed(100)
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
        if limp_bool:
            limp_string = "FALSE\r\n"
        else:
            limp_string = "TRUE\r\n"
        command = "LIMP %s" % limp_string  # Command interpreted by Sciclops
        self.send_command(command)
