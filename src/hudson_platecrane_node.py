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

        # Create resources.
        self.create_resources()

    def create_resources(self): 
        # Does the gripper resource already exist?
        gripper_resource_name = f"{self.node_definition.node_name}_gripper.nest"
        self.gripper_resource = None
        try: 
            # Save gripper resource details if it already exists.
            self.gripper_resource = self.resource_client.query_resource(
                resource_name=gripper_resource_name,
            )
            self.logger.log_info(f"The PlateCrane EX gripper resource already exists: {self.gripper_resource.resource_id}")
        except Exception as e: 
            self.logger.log_info(f"Creating a new instance of the {gripper_resource_name} resource.")

        # If not, create a new gripper resource.
        if not self.gripper_resource:
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

        # Check state of resources in ResourceClient.
        plate_resource = None 
        if (self.resource_client is not None) and (self.location_client is not None):
                # Does a plate resource exist at the source location?
                source_resource_id = self.location_client.get_location_by_name(source.name).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if len(source_resource.children) == 1:
                    plate_resource = source_resource.child 
                else: 
                    return ActionFailed(errors=[f"No plate resource exists at source location {source.name}"])
                        
                
                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(errors=[f"A plate resource is already in the gripper. Pick action cannot be completed."])
        else: 
            self.logger.log_warning(f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}")
        
        # Physically pick the plate.
        self.platecrane.pick(
            source=source,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            source_grip_height_in_steps=source_grip_height_in_steps,
            incremental_lift=incremental_lift,
        )

        # Push plate resource into gripper resource as a child.
        if plate_resource:
            self.resource_client.push(
                resource=self.gripper_resource, 
                child=plate_resource
            )

        return None


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

        # Check state of resources in ResourceClient.
        plate_resource = None 
        if (self.resource_client is not None) and (self.location_client is not None):
                # Does a plate resource exist in the gripper? 
                self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
                if len(self.gripper_resource.children) == 1: 
                    print("PLATE EXISTS IN THE GRIPPER")
                    plate_resource = self.gripper_resource.child 
                else: 
                    return ActionFailed(errors=["No plate resource exists in the gripper. Place action cannot be completed."])
                
                # Is the target location clear? 
                target_resource_id = self.location_client.get_location_by_name(target.name).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if len(target_resource.children) == 1:
                    return ActionFailed(errors=[f"A plate resource already exists at the target location {target.name}. The place action cannot be completed."])
                
        else: 
            self.logger.log_warning(f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}")

        # Physically plate the plate.
        self.platecrane.place(
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            target_grip_height_in_steps=target_grip_height_in_steps,
        )

        # Push plate resource into target resource as child.
        self.resource_client.push(
            resource=target_resource,
            child=plate_resource,
        )

        return None

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
        # Pick the plate.
        pick_result = self.pick(
            source=source,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            source_grip_height_in_steps=source_grip_height_in_steps,
            incremental_lift=incremental_lift,
        )
        if pick_result is not None:
            # Return any ActionFailed response received. 
            # Fails the action, but does not put the device into an error state.
            return pick_result
        
        # Place the plate.
        place_result = self.place(
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            target_grip_height_in_steps=target_grip_height_in_steps,
        )
        return place_result


    @action()
    def remove_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. 'flat_bottom_96well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name

        # TESTING
        print(f"{source=}")
        print(f"{source.representation=}")
        print(f"{target=}")
        print(f"{target.representation=}")

        # TODO: start here! remove lid is broken


        source = PlateCraneLocation.model_validate(source.representation)
        # target = PlateCraneLocation.model_validate(
        #     name=target.location_name, **target.representation
        # )
        target = PlateCraneLocation.model_validate(target.representation)

        # # TODO: ResourceClient checks!
        # if (self.resource_client is not None) and (self.location_client is not None):
        #     # 
        # else: 
        #     self.logger.log_warning(f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}")

        #     # # Does a plate resource exist in the gripper? 
        #     # self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
        #     # if len(self.gripper_resource.children) == 1: 
             
        #     #     plate_resource = self.gripper_resource.child 
        #     # else: 
        #     #     return ActionFailed(errors=["No plate resource exists in the gripper. Place action cannot be completed."])
            
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
