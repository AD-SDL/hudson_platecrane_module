"""A REST Node Module for the Hudson PlateCrane EX robot.

This module provides a MADSci Node-compliant REST API for controlling the Hudson PlateCrane EX robot.
It includes actions for transferring plates, removing lids, and
placing lids.
"""

import traceback
from typing import Annotated, Optional

from madsci.common.types.action_types import ActionFailed
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.common.types.resource_types import Slot, Stack
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode

from pathlib import Path

from platecrane_driver.platecrane_driver import PlateCrane, PlateCraneLocation


"""
TODOs: 
- why can't I change self.node_definition.node_name to platecrane_poly no matter what I do here or in the rapid350_sdl repo?
"""


class PlateCraneConfig(RestNodeConfig):
    """Configuration for the PlateCrane REST Node."""

    device: str = "/dev/ttyUSB0"
    """A device path for the serial port to connect to the PlateCrane robot."""
    baud_rate: int = 9600
    """The baud rate for the serial connection to the PlateCrane robot."""
    default_speed: int = 100
    """The default speed for the PlateCrane robot arm to move, as a percentage."""

class PlateCraneNode(RestNode):
    """A REST MADSci Node for controlling the Hudson PlateCrane robot."""

    platecrane: Optional[PlateCrane] = None
    """The PlateCrane driver instance."""
    config_model = PlateCraneConfig
    """The configuration model for the PlateCrane REST Node."""
    config: PlateCraneConfig = PlateCraneConfig()
    """The default configuration for the PlateCrane REST Node."""
    module_version: str = "2.1.0"
    """The version of the PlateCrane REST Node module."""

    def startup_handler(self) -> None:
        """Handles initializing the PlateCrane driver at node startup."""
        self.platecrane = PlateCrane(
            device_path=self.config.device, baud_rate=self.config.baud_rate
        )
        self.platecrane.initialize_platecrane()
        # self.gripper_resource = self.resource_client.add_resource(
        #     Slot(name="platecrane_gripper")
        # )

        # Create resources: 
        self.create_resources()

    # ADD MADSCI RESOURCES



    def create_resources(self): 

        # TESTING
        print("TESTING")
        print(f"{self.node_definition}")
        print(f"{self.node_definition.node_name=}")


        # Does the gripper resource already exist?
        self.gripper_resource_id = None
        gripper_resource_name = f"{self.node_definition.node_name}_gripper.nest"
        self.gripper_resource = None
        try: 
            self.gripper_resource = self.resource_client.query_resource(
                resource_name=gripper_resource_name,
            )
            print("gripper already exists!")
        except Exception as e: 
            self.logger.log_info(f"Creating a new instance of the {gripper_resource_name} resource.")

        if not self.gripper_resource:
            # Gripper
            gripper_slot = Slot(
                resource_name = f"{self.node_definition.node_name}_gripper.nest",
                resource_description="Gripper location on the Plate Crane EX.",
            )
            self.gripper_resource = self.resource_client.add_resource(
                resource = gripper_slot,
            )


    @action()
    def pick(
        self,
        source: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        has_lid: Annotated[bool, "Does the plate have a lid?"] = False,
        source_grip_height_in_steps: Annotated[
            int, "Source grip height in motor steps"
        ] = 0,
        incremental_lift: Annotated[bool, "Incremental lift during transfer"] = False,
    ) -> None:
        """Transfers a plate from one location to another."""
        source.representation["name"] = source.location_name
        source = PlateCraneLocation.model_validate(source.representation)

        self.platecrane.pick(
            source=source,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            source_grip_height_in_steps=source_grip_height_in_steps,
            incremental_lift=incremental_lift,
        )
        try:
            if self.resource_client is not None:
                object, _ = self.resource_client.pop(source.resource_id)
                self.resource_client.push(self.gripper_resource, object)
        except Exception as e:
            self.logger.log_error(f"Error during gripper pick: {e}")
            return ActionFailed(error=traceback.format_exc())

    @action()
    def place(
        self,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        target_grip_height_in_steps: Annotated[
            int, "Target grip height in motor steps"
        ] = 0,
    ) -> None:
        """Transfers a plate from one location to another."""
        target.representation["name"] = target.location_name
        target = PlateCraneLocation.model_validate(target.representation)
        self.platecrane.place(
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            target_grip_height_in_steps=target_grip_height_in_steps,
        )
        try:
            if self.resource_client is not None:
                object, _ = self.resource_client.pop(self.gripper_resource)
                self.resource_client.push(target.resource_id, object)
        except Exception as e:
            self.logger.log_error(f"Error during gripper place: {e}")
            return ActionFailed(error=traceback.format_exc())

    @action()
    def transfer(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        has_lid: Annotated[bool, "Does the plate have a lid?"] = False,
        source_grip_height_in_steps: Annotated[
            int, "Source grip height in motor steps"
        ] = 0,
        target_grip_height_in_steps: Annotated[
            int, "Target grip height in motor steps"
        ] = 0,
        incremental_lift: Annotated[bool, "Incremental lift during transfer"] = False,
    ) -> None:
        """Transfers a plate from one location to another."""
        self.pick(
            source=source,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            source_grip_height_in_steps=source_grip_height_in_steps,
            incremental_lift=incremental_lift,
        )
        self.place(
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            target_grip_height_in_steps=target_grip_height_in_steps,
        )

    @action()
    def remove_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. '96-well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = PlateCraneLocation.model_validate(source.representation)
        target = PlateCraneLocation.model_validate(
            name=target.location_name, **target.representation
        )
        self.platecrane.remove_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )

    @action()
    def replace_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. '96-well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = PlateCraneLocation.model_validate(source.representation)
        target = PlateCraneLocation.model_validate(target.representation)
        self.platecrane.replace_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )

    @action()
    def home(self) -> None:
        """Moves the PlateCrane to the home position."""
        self.platecrane.home()

    @action()
    def move(self, target: LocationArgument) -> None:
        """Moves the PlateCrane to a specified position."""
        target = PlateCraneLocation.model_validate(
            name=target.location_name, **target.representation
        )
        self.platecrane.move_joint_angles(
            r=target.joint_angles[0],
            z=target.joint_angles[1],
            p=target.joint_angles[2],
            y=target.joint_angles[3],
        )


if __name__ == "__main__":
    plate_crane_node = PlateCraneNode(
        node_definition=NodeDefinition(
            node_name="platecrane_node", module_name="hudson_platecrane_node"
        )
    )
    plate_crane_node.start_node()
