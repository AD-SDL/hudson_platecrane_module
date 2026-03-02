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
from madsci.common.types.resource_types import Slot, Stack, Resource, Collection, Grid
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode

from pathlib import Path

from platecrane_driver.platecrane_driver import PlateCrane, PlateCraneLocation


"""
TODOs: 
- why can't I change self.node_definition.node_name to platecrane_poly no matter what I do here or in the rapid350_sdl repo?

Below is the plate with lid standard that I'm working with:

        # # TESTING (create a properly formatted plate resource with lid slot)
        # test_lid = Resource(
        #     resource_name = "TEST_LID",
        #     attributes={
        #         "lid": True
        #     }
        # )
        # test_plate_resource = Collection(
        #     resource_name = "FORMATTED_TEST_PLATE3", 
        #     capacity=2,
        #     children={
        #         "lid_slot": Slot(
        #             resource_name = "lid slot resource on test plate",
        #             children=[test_lid]
        #         )
        #     }
        # )
        # self.resource_client.add_resource(test_plate_resource)


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
                if len(source_resource.children) > 0:
                    plate_resource = source_resource.children[0] 
                    # this accounts for the source resource being a stack
                else: 
                    return ActionFailed(errors=[f"No plate resource exists at source location {source.name}"])
                        
                
                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(errors=[f"A resource is already in the gripper. Pick action cannot be completed."])
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

        # Physically place the plate.
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
        plate_type: Annotated[str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[bool, "True to ignore ResourceClient validations, False otherwise."] = False
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = PlateCraneLocation.model_validate(source.representation)
        target = PlateCraneLocation.model_validate(target.representation)

        # Complete MADSci resource checks.
        lid_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structyre conformity with a Pydantic model.
            if (self.resource_client is not None) and (self.location_client is not None):

                # Is a lid resource present on the source location for removal?
                source_resource_id = self.location_client.get_location_by_name(source.name).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if len(source_resource.children) == 1:
                    plate_resource = source_resource.child 
                    if "lid_slot" in plate_resource.children:
                        lid_slot_child_value = plate_resource.children["lid_slot"]
                        if isinstance(lid_slot_child_value, Slot):
                            if len(lid_slot_child_value.children) == 1: 
                                lid_resource = lid_slot_child_value.child  # collect lid resource
                                self.logger.log_info(f"Identified lid Slot resource {lid_resource.resource_id} for removal.")
                            else: 
                                return ActionFailed(errors=[f"No lid resource exists in the lid slot. {lid_slot_child_value}"])
                        else: 
                            return ActionFailed(errors=[f"Lid slot child value is not of type Slot. {lid_slot_child_value=}"])
                    else:
                        return ActionFailed(errors=f"No \"lid\" child exists on the plate resource {plate_resource.resource_id}")
                else: 
                    return ActionFailed(errors=[f"No plate resource exists at source location {source.name}"])
                
                # Is the target location clear?
                target_resource_id = self.location_client.get_location_by_name(target.name).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if not len(target_resource.children) == 0: 
                    return ActionFailed(errors=[f"A plate resource already exists at the target location {target.name}. The remove lid action cannot be completed."])
                    
                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(errors=[f"A resource is already in the gripper. Pick action cannot be completed."])
            else: 
                return ActionFailed(f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}")
        else: 
            self.logger.log_info("Skipping resources validation for remove lid action.")    

        self.platecrane.remove_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )

        # transfer the lid resource 
        # TODO: this skips transferring through the gripper for now
        # since pick and place for the lid are not called separately
        if target_resource and lid_resource:
            # Push lid resource onto target Slot resource.
            try: 
                self.resource_client.push(target_resource, lid_resource)
            except Exception as e: 
                # Return Action Failed. Do not put device into an error state.
                return ActionFailed(errors=[f"Lid resource could not be removed in ResourceClient. {e}"])
        else: 
            return ActionFailed(f"lid_resource or target_resource do not exist. {lid_resource=}, {target_resource=}")


    @action()
    def replace_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[bool, "True to ignore ResourceClient validations, False otherwise."] = False

    ) -> None:
        """Replaces a lid on a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = PlateCraneLocation.model_validate(source.representation)
        target = PlateCraneLocation.model_validate(target.representation)

        # Complete MADSci resource checks.
        lid_resource = None
        lid_slot_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structyre conformity with a Pydantic model.
            if (self.resource_client is not None) and (self.location_client is not None):
                # Check for a lid resource in the source location.
                source_resource_id = self.location_client.get_location_by_name(source.name).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if len(source_resource.children) == 1:  # source slot resource can only have one child
                    child_resource = source_resource.child
                    if "lid" in child_resource.attributes: 
                        if source_resource.child.attributes["lid"] is True: 
                            lid_resource = source_resource.child  # a lid exists at the source location
                        else: 
                            return ActionFailed(errors=[f"\"lid\" attribute is set to {source_resource.child.attributes["lid"]}."])
                    else: 
                        self.logger.log_warning(f"Lid resource found does not conform to standard. No \"lid\" attribute found. {lid_resource}")
                else: 
                    return ActionFailed(errors=["No lid resource exists at source location."])
                
                # Check for a plate without a lid at the target location
                target_resource_id = self.location_client.get_location_by_name(target.name).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if len(target_resource.children) == 1: 
                    plate_resource = target_resource.child
                    if "lid_slot" in plate_resource.children:
                        if len(plate_resource.children["lid_slot"].children) != 0: 
                            return ActionFailed(errors=[f"A lid resource already exists on the plate resource at the target location. plate_resource={plate_resource=}"])
                        else: 
                            lid_slot_resource = plate_resource.children["lid_slot"]
                    else: 
                        return ActionFailed(errors=[f"Target plate resource has no lid slot resource. {target_resource=}"])
                else:
                    return ActionFailed(errors=[f"No plate resource exists at the target location {target.name}. The remove lid action cannot be completed."])
                    
                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(self.gripper_resource)  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(errors=[f"A resource is already in the gripper. Pick action cannot be completed."])
                
            else:
                return ActionFailed(f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}")
        else: 
            self.logger.log_info("Skipping resources validation for replace lid action.")  

        self.platecrane.replace_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )

        # Transfer the lid resource 
        # TODO: this skips transferring through the gripper for now
        # since pick and place for the lid are not called separately
        if lid_resource and lid_slot_resource:
            # push lid resource onto the plate resource's lid slot
            try: 
                self.resource_client.push(lid_slot_resource, lid_resource)
            except Exception as e: 
                # Return Action Failed.Do not put device into an error state.
                return ActionFailed(errors=[f"Lid resource could not be replaced in ResourceClient. {e}"])
        else: 
            return ActionFailed(f"lid_resource or lid_slot_resourse do not exist. {lid_resource=}, {lid_slot_resource=}")


    @action()
    def home(self) -> None:
        """Moves the PlateCrane to the home position."""
        self.platecrane.home()

    @action()
    def move(self, target: LocationArgument) -> None:
        """Moves the PlateCrane to a specified position."""
        target.representation["name"] = target.location_name
        target = PlateCraneLocation.model_validate(target.representation)
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
