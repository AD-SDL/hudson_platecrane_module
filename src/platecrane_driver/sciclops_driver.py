"""Driver for the Hudson Robotics Sciclops robot."""
import asyncio
import re

import usb.core
import usb.util


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
        self.labware = self.load_labware()
        self.plate_info = self.load_plate_info()
        self.success_count = 0
        self.status = self.get_status()
        self.error = self.get_error()
        self.movement_state = "READY"

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

    def load_plate_info(self):
        """
        hard-codes size information for any possible plates
        """
        plates = {
            "96_well": {
                "height": 16.2562,
                "grab_exchange": -30,  # downward motion from Z = -356.5375
                "grab_lid_exchange": -21,  # downward motion from Z = -356.5375
                "grab_tower": -18,  # downward motion from 10 above top of plate
                "grab_lid_tower": -13,
                "grab_lid_nest": -12,
            },
            "pcr_plate": {
                "height": 15.2762,
                "grab_exchange": -28,  # from Z = -356.5375
                "grab_lid_exchange": 0,  # downward motion from Z = -356.5375, no lid
                "grab_tower": -17,  # downward motion from 10 above top of plate
                "grab_lid_tower": 0,  # no lid
                "grab_lid_nest": 0,  # no lid
            },
        }

        return plates

    def load_labware(self, labware_file=None):
        """
        Loads plate information which affects get_plate function.
        """
        if labware_file:
            pass  # will load file in the future

        # Dictionary for plate information
        labware = {
            "tower1": {
                "pos": {"Z": 23.5188, "R": 133.5, "Y": 171.9895, "P": 8.6648},
                "type": "pcr_plate",
                "howmany": 1,
                "grab_height": 8,
                "cap_height": 20,
                "size": [10, 11, 12],
                "has_lid": True,
            },
            "tower2": {
                "pos": {"Z": 23.5188, "R": 151.3, "Y": 171.4872, "P": 8.4943},
                "type": "96_well",
                "howmany": 0,
                "grab_height": 8,
                "cap_height": 20,
                "size": [10, 11, 12],
                "has_lid": True,
            },
            "tower3": {
                "pos": {"Z": 23.5188, "R": 169.5, "Y": 171.4810, "P": 12.4716},
                "type": "96_well",
                "howmany": 0,
                "grab_height": 8,
                "cap_height": 20,
                "size": [10, 11, 12],
                "has_lid": True,
            },
            "tower4": {
                "pos": {"Z": 23.5188, "R": 187.5, "Y": 169.4470, "P": 5.9091},
                "type": "96_well",
                "howmany": 0,
                "grab_height": 8,
                "cap_height": 20,
                "size": [10, 11, 12],
                "has_lid": True,
            },
            "tower5": {
                "pos": {"Z": 23.5188, "R": 205.4, "Y": 171.2082, "P": 10.8807},
                "type": "96_well",
                "howmany": 0,
                "grab_height": 8,
                "cap_height": 20,
                "size": [10, 11, 12],
                "has_lid": True,
            },
            "lidnest1": {
                "pos": {"Z": 23.5188, "R": 169.2706, "Y": 25.7535, "P": 10.2159},
                "type": "96_well",
                "howmany": 0,  # can only hold one
                "size": [10, 11, 12],
                "grab_height": 15,  # Z of -372.4625 ( 10 above lid)
            },
            "lidnest2": {
                "pos": {"Z": 23.5188, "R": 201.2665, "Y": 25.7535, "P": 8.0909},
                "type": "96_well",
                "howmany": 0,  # can only hold one
                "size": [10, 11, 12],
                "grab_height": 15,
            },
            "exchange": {
                "pos": {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 100.8955},
                "type": "96_well",
                "howmany": 0,
                "size": [10, 11, 2],
                "grab_height": 0,
                "cap_height": 15,
                "has_lid": False,
            },
            "neutral": {
                "pos": {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955}
            },
            "trash": {"pos": {"Z": 23.5188, "R": 259.2688, "Y": 62.7497, "P": 98.2670}},
        }

        return labware

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
                response = self.host_path.read(0x83, 200, timeout=5000)
            except Exception:
                break
            msg = "".join(chr(i) for i in response)
            response_buffer = response_buffer + "Read: " + msg

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
        except Exception:
            pass

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

    async def check_complete(self):
        """
        Checks to see if current sciclops action has completed
        """
        print("Checking if complete")
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
            await asyncio.sleep(0.1)

    async def check_complete_loop(self):
        """
        continuously runs check_complete until it returns True
        """
        a = False
        while not a:
            a = await self.check_complete()

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
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )

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

        self.deletepoint(R, Z, P, Y)

    def move_loc(self, loc):
        """
        Move to preset locations located in load_labware function
        """

        # check if loc exists (later)
        self.move(
            self.labware[loc]["pos"]["R"],
            self.labware[loc]["pos"]["Z"],
            self.labware[loc]["pos"]["P"],
            self.labware[loc]["pos"]["Y"],
        )

    def get_plate(self, location, remove_lid=False, trash=False):
        """
        Grabs plate and places on exchange. Paramater is the stack that the Sciclops is requested to remove the plate from.
        Format: "Stack<num>"
        remove lid and trash bools tell whether to remove lid from plate and whether to throw said lid in the trash or place in nest
        """

        # check to see if plate already on the exchange
        # removed for now until labware can be  edited in a file
        # if self.labware['exchange']['howmany'] != 0:
        #     print("PLATE ALREADY ON THE EXCHANGE")
        # else:
        tower_info = self.labware[location]
        plate_type = tower_info["type"]

        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)  #
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )

        # check coordinates
        asyncio.run(self.check_complete_loop())

        # Move above desired tower
        self.set_speed(100)
        self.move(
            R=tower_info["pos"]["R"],
            Z=23.5188,
            P=tower_info["pos"]["P"],
            Y=tower_info["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # Remove plate from tower
        self.close()
        self.set_speed(15)
        self.jog("Z", -1000)
        # move up certain amount
        self.jog("Z", 10)
        self.open()
        grab_height = self.plate_info[plate_type]["grab_tower"]
        self.jog("Z", grab_height)
        self.close()
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        # asyncio.run(self.check_complete_loop())

        # Place in exchange
        self.move(
            R=self.labware["exchange"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["exchange"]["pos"]["P"],
            Y=self.labware["exchange"]["pos"]["Y"],
        )
        # check coordinates
        # asyncio.run(self.check_complete_loop())
        self.jog("Z", -380)
        self.set_speed(5)
        self.jog("Z", -30)
        self.open()
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        # asyncio.run(self.check_complete_loop())
        self.labware["exchange"]["howmany"] += 1
        self.labware["exchange"]["type"] = self.labware[location]["type"]
        self.labware["exchange"]["size"] = self.labware[location]["size"]
        self.labware["exchange"]["has_lid"] = self.labware[location]["has_lid"]

        # check if lid needs to be removed
        if remove_lid:
            self.remove_lid(trash=trash)
        else:
            self.labware["exchange"]["has_lid"] = True

        # Move back to neutral
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        # check coordinates
        # asyncio.run(self.check_complete_loop())

        # update labware
        self.labware[location]["howmany"] -= 1

    def limp(self, limp_bool):
        """
        Turns on/off limp mode (allows someone to manually move joints)
        """
        if limp_bool:
            limp_string = "FALSE"
        else:
            limp_string = "TRUE"
        command = "LIMP %s" % limp_string  # Command interpreted by Sciclops
        self.send_command(command)

    def check_for_lid(
        self,
    ):  # TODO: conditional for no available lid to prevent delays?
        """Checks all lid nests to see if there's a lid of same type present, returns occupied lid nest"""
        if (
            self.labware["lidnest1"]["howmany"] >= 1
            and self.labware["lidnest1"]["type"] == self.labware["exchange"]["type"]
        ):
            return "lidnest1"
        elif (
            self.labware["lidnest2"]["howmany"] >= 1
            and self.labware["lidnest2"]["type"] == self.labware["exchange"]["type"]
        ):
            return "lidnest2"
        else:
            print("NO MATCHING LID IN LID NESTS")
        pass

    # * check all lid nests to see if there's an empty "available" lid nst, returns open lid nest
    def check_for_empty_nest(
        self,
    ):  # TODO: maybe add conditional to throw away lids in nests if none available?
        """Check all lid nests to see if there's an empty "available" lid nest, returns open lid nest"""
        if self.labware["lidnest1"]["howmany"] == 0:
            return "lidnest1"
        elif self.labware["lidnest2"]["howmany"] == 0:
            return "lidnest2"
        else:
            print("NO AVAILABLE LID NESTS")
        pass

    def check_stack(self, tower):
        """Check a stack to see if there's room for another plate, returns True if there is room, False if not."""
        # save z height of stack Z = -36
        tower_z_height = -50
        tower_z_bottom = -421.8625
        # get type of plate in desired tower
        plate_type = self.labware[tower]["type"]
        # get height of plate type
        plate_height = self.plate_info[plate_type]["height"]
        # number of plates in stack
        num_stack = self.labware[tower]["howmany"]
        total_height = plate_height * num_stack
        remaining = total_height + tower_z_bottom
        if remaining < tower_z_height:  # room for another plate
            return True
        else:  # stack full
            return False

    def remove_lid(self, trash):
        """Remove lid, (self, lidnest, plate_type), removes lid from plate in exchange, trash bool will throw lid into trash"""
        #  move above plate exchange
        self.set_speed(100)
        self.open()
        self.move(
            R=self.labware["exchange"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["exchange"]["pos"]["P"],
            Y=self.labware["exchange"]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())
        plate_type = self.labware["exchange"]["type"]

        # check to make sure plate has lid
        if not self.labware["exchange"]["has_lid"]:
            print("NO LID ON PLATE IN EXCHANGE")
        else:
            # remove lid
            self.jog("Z", -380)
            self.set_speed(7)
            lid_height = self.plate_info[plate_type]["grab_lid_exchange"]
            self.jog("Z", lid_height)
            self.close()

            self.set_speed(100)
            self.jog("Z", 1000)
            # check coordinates
            asyncio.run(self.check_complete_loop())

            if trash:
                # move above trash
                self.move(
                    R=self.labware["trash"]["pos"]["R"],
                    Z=23.5188,
                    P=self.labware["trash"]["pos"]["P"],
                    Y=self.labware["trash"]["pos"]["Y"],
                )
                asyncio.run(self.check_complete_loop())

                # drop in trash
                self.jog("Z", -400)
                self.open()
                self.jog("Z", 1000)

                # return to home
                self.move(
                    R=self.labware["neutral"]["pos"]["R"],
                    Z=23.5188,
                    P=self.labware["neutral"]["pos"]["P"],
                    Y=self.labware["neutral"]["pos"]["Y"],
                )
                # check coordinates
                asyncio.run(self.check_complete_loop())

                # update labware
                self.labware["exchange"]["has_lid"] = False
            else:
                # find empty plate nest
                lid_nest = self.check_for_empty_nest()

                # move above desired lid nest
                self.move(
                    R=self.labware[lid_nest]["pos"]["R"],
                    Z=23.5188,
                    P=self.labware[lid_nest]["pos"]["P"],
                    Y=self.labware[lid_nest]["pos"]["Y"],
                )
                # check coordinates
                asyncio.run(self.check_complete_loop())

                # place in lid nest
                self.jog("Z", -400)
                self.open()
                self.jog("Z", 1000)
                # check coordinates
                asyncio.run(self.check_complete_loop())

                # return to home
                self.move(
                    R=self.labware["neutral"]["pos"]["R"],
                    Z=23.5188,
                    P=self.labware["neutral"]["pos"]["P"],
                    Y=self.labware["neutral"]["pos"]["Y"],
                )
                # check coordinates
                asyncio.run(self.check_complete_loop())

                # update labware dict
                self.labware[lid_nest]["howmany"] += 1
                self.labware[lid_nest]["type"] = self.labware["exchange"]["type"]
                self.labware["exchange"]["has_lid"] = False

    def replace_lid(self):
        """Plate on exchange, replace lid (self, plateinfo, lidnest)"""
        # find a lid
        self.set_speed(100)
        self.open()
        lid_nest = self.check_for_lid()
        plate_type = self.labware["exchange"]["type"]

        # make sure current plate doesn't already have lid
        if self.labware["exchange"]["has_lid"]:
            print("PLATE IN EXCHANGE ALREADY HAS LID")
        else:
            # move above desired lidnest
            self.move(
                R=self.labware[lid_nest]["pos"]["R"],
                Z=23.5188,
                P=self.labware[lid_nest]["pos"]["P"],
                Y=self.labware[lid_nest]["pos"]["Y"],
            )
            # check coordinates
            asyncio.run(self.check_complete_loop())

            # grab lid
            self.close()
            self.jog("Z", -380)
            self.set_speed(7)
            self.jog("Z", -1000)
            self.jog("Z", 10)
            self.open()
            lid_height = self.plate_info[plate_type]["grab_lid_nest"]
            self.jog("Z", lid_height)
            self.close()
            self.set_speed(100)
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # move above exchange
            self.move(
                R=self.labware["exchange"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["exchange"]["pos"]["P"],
                Y=self.labware["exchange"]["pos"]["Y"],
            )
            # check coordinates
            asyncio.run(self.check_complete_loop())

            # place lid onto plate
            self.jog("Z", -400)
            self.open()
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # return to home
            self.move(
                R=self.labware["neutral"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["neutral"]["pos"]["P"],
                Y=self.labware["neutral"]["pos"]["Y"],
            )
            # check coordinates
            asyncio.run(self.check_complete_loop())

            # update labware dict
            self.labware[lid_nest]["howmany"] -= 1
            self.labware["exchange"]["has_lid"] = True

    def plate_to_stack(self, tower, add_lid):
        """Plate from exchange to stack (self, tower, plateinfo)"""
        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        asyncio.run(self.check_complete_loop())
        plate_type = self.labware["exchange"]["type"]
        if add_lid:
            self.check_for_lid()
            self.replace_lid()

        # TODO: check to see if given stack is full, use function to account for different labware, maybe checks all stacks to find one with same labware?

        # move over exchange
        self.open()
        self.move(
            R=self.labware["exchange"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["exchange"]["pos"]["P"],
            Y=self.labware["exchange"]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())
        # grab plate
        self.set_speed(100)
        self.jog("Z", -380)
        grab_height = self.plate_info[plate_type]["grab_exchange"]
        self.jog("Z", grab_height)
        self.close()
        self.set_speed(100)
        self.jog("Z", 1000)
        asyncio.run(self.check_complete_loop())

        # move above tower, place plate in tower
        self.move(
            R=self.labware[tower]["pos"]["R"],
            Z=23.5188,
            P=self.labware[tower]["pos"]["P"],
            Y=self.labware[tower]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())
        self.set_speed(10)
        self.jog("Z", -1000)
        self.open()
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # move to home
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # update labware dict
        self.labware["exchange"]["howmany"] -= 1
        self.labware[tower]["howmany"] += 1

    def lidnest_to_trash(self, lidnest):
        """Remove lid from lidnest, throw away"""
        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        asyncio.run(self.check_complete_loop())
        # check to make sure lid present
        if self.labware[lidnest]["howmany"] >= 1:  # lid in nest
            lid_type = self.labware[lidnest]["type"]
            # move above lidnest
            self.set_speed(100)
            self.close()
            self.move(
                R=self.labware[lidnest]["pos"]["R"],
                Z=23.5188,
                P=self.labware[lidnest]["pos"]["P"],
                Y=self.labware[lidnest]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # grab lid
            self.jog("Z", -380)
            self.set_speed(7)
            self.jog("Z", -1000)
            self.jog("Z", 10)
            self.open()
            lid_height = self.plate_info[lid_type]["grab_lid_nest"]
            self.jog("Z", lid_height)
            self.close()
            self.set_speed(100)
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # move above trash
            self.move(
                R=self.labware["trash"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["trash"]["pos"]["P"],
                Y=self.labware["trash"]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # drop lid
            self.jog("Z", -1000)
            self.open()
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # back to neutral
            self.move(
                R=self.labware["neutral"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["neutral"]["pos"]["P"],
                Y=self.labware["neutral"]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # update labware
            self.labware[lidnest]["howmany"] -= 1

        else:
            print("NO LID IN NEST")

    def plate_to_trash(self, add_lid):
        """Remove plate from exchange, throw away"""
        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        asyncio.run(self.check_complete_loop())
        # check if plate is present
        if self.labware["exchange"]["howmany"] >= 1:
            # check if add_lid is true, if yes, add lid
            if add_lid:
                self.replace_lid()

            plate_type = self.labware["exchange"]["type"]

            # move over exchange
            self.set_speed(100)
            self.open()
            self.move(
                R=self.labware["exchange"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["exchange"]["pos"]["P"],
                Y=self.labware["exchange"]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # grab plate
            self.jog("Z", -380)
            self.set_speed(7)
            grab_height = self.plate_info[plate_type]["grab_plate_exchange"]
            self.jog("Z", grab_height)
            self.close()
            self.set_speed(100)
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # move over trash
            self.move(
                R=self.labware["trash"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["trash"]["pos"]["P"],
                Y=self.labware["trash"]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # drop plate
            self.jog("Z", -1000)
            self.open()
            self.jog("Z", 1000)
            asyncio.run(self.check_complete_loop())

            # back to neutral
            self.move(
                R=self.labware["neutral"]["pos"]["R"],
                Z=23.5188,
                P=self.labware["neutral"]["pos"]["P"],
                Y=self.labware["neutral"]["pos"]["Y"],
            )
            asyncio.run(self.check_complete_loop())

            # update labware
            self.labware["exchange"]["howmany"] -= 1

        else:
            print("NO PLATE IN EXCHANGE")


if __name__ == "__main__":
    """
    Runs given function.
    """
    s = SCICLOPS()
    # s.get_error()
    # s.get_status()
    # for i in range(1):
    #     # s.jog("R", -1000)
    #     # s.reset()
    # #     sleep(5)
    #     # s.home()
    #     # s.send_command("")
    # #     sleep(5)
    #     s.get_plate("tower4")
    # #     sleep(25)
    # print("STATUS MSG: ", s.status)
    # s.check_closed()
    # print(s.CURRENT_POS)
    s.reset()
    # s.home()
    # s.get_plate("tower1")
    # dummy_sciclops.check_plate()

# Finished commands
# "GETPOS"
# "STATUS"
# "VERSION"
# "GETCONFIG"
# "GETGRIPPERLENGTH"
# "GETCOLLAPSEDISTANCE"
# "GETSTEPSPERUNIT"
# "HOME"
# "OPEN"
# "CLOSE"
# "GETGRIPPERISCLOSED"
# "GETGRIPPERISOPEN"
# "GETPLATEPRESENT"
# "SETSPEED "
# "MOVE "
# "JOG"
# "DELETEPOINT (ADD POINT)"
# "LISTPOINTS"
# "LOADPOINT R:0,Z:0,P:0,Y:0"
# "LIMP TRUE/FALSE"

# #Unfinished Commands
# "GETLIMITS"

# #Unknown Commands
# "LISTMOTIONS"
# "AUTOTEACH"
# "GETPOINT"
# "READINP 15"
# "GETGRIPSTRENGTH"
# "READINP"
