#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path
from typing import Annotated, Optional, Union

from fastapi.datastructures import State
from madsci.common.types.action_types import ActionFailed
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.common.types.resource_types import Slot
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode

from platecrane_driver.sciclops_driver import SCICLOPS, SciClopsLocation
from platecrane_driver.sciclops_resource_defs import plate_definitions

"""
TODO:
- Add all the SciClops locations to the location client!




"""


class SciClopsConfig(RestNodeConfig):
    """Configuration for the SciClops REST Node."""

    # TODO: What else to add here?
    default_speed: int = 100
    """The default speed for the PlateCrane robot arm to move, as a percentage."""


class SciClopsNode(RestNode):
    """A MADSci REST Node for controlling the Hudson SciClops robotic arm."""

    sciclops = Optional[SCICLOPS] = None
    """The SciClops driver instance."""
    config_model = SciClopsConfig
    """The configuration model for the SciClops REST Node."""
    config: SciClopsConfig = SciClopsConfig()
    """The default configuration for the SciClops REST Node."""
    module_version: str = "2.1.0"
    """The version of the SciClops REST Node module."""

    def startup_handler(self):
        """Initializes the SciClops driver at node startup."""
        self.sciclops = SCICLOPS()

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
            self.logger.log_info(
                f"The SciClops gripper resource already exists: {self.gripper_resource.resource_id}"
            )
        except Exception:
            self.logger.log_info(
                f"Creating a new instance of the {gripper_resource_name} resource."
            )

        # If not, create a new gripper resource.
        if not self.gripper_resource:
            gripper_slot = Slot(
                resource_name=f"{self.node_definition.node_name}_gripper.nest",
                resource_description="Gripper location on the Plate Crane EX.",
            )
            self.gripper_resource = self.resource_client.add_resource(
                resource=gripper_slot,
            )

        # Don't create Lid Nests or Stacks here.
        # They're not a requirement to use the SciClops device.

    @action()
    def home(self) -> None:
        """Homes the SciClops."""
        self.sciclops.home()

    @action()
    def pick(
        self,
        source: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in mm"] = 0,
        is_lid: Annotated[bool, "Is the labware a lid?"] = False,
        has_lid: Annotated[bool, "Does the labware have a lid?"] = False,
        incremental_lift: Annotated[bool, "Incremental lift during transfer"] = False,
    ) -> None:
        """Picks labware from a location, ending in the PlateCrane gripper."""
        source.representation["name"] = source.location_name
        source = SciClopsLocation.model_validate(source.representation)

        # extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions."
                ]
            )

        # TESTING
        print(f"{source}")
        print(f"{type(source)=}")

        # Check state of resources in ResourceClient.
        plate_resource = None
        if (self.resource_client is not None) and (self.location_client is not None):
            # Does a plate resource exist at the source location?
            source_resource_id = self.location_client.get_location_by_name(
                source.name
            ).resource_id
            source_resource = self.resource_client.get_resource(source_resource_id)
            if len(source_resource.children) > 0:
                plate_resource = source_resource.children[0]
                # this accounts for the source resource being a stack
            else:
                return ActionFailed(
                    errors=[
                        f"No plate resource exists at source location {source.name}"
                    ]
                )

            # Is the gripper location clear?
            self.gripper_resource = self.resource_client.get_resource(
                self.gripper_resource
            )  # update the gripper resource
            if len(self.gripper_resource.children) == 1:
                return ActionFailed(
                    errors=[
                        "A resource is already in the gripper. Pick action cannot be completed."
                    ]
                )
        else:
            self.logger.log_warning(
                f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
            )

        # Physically pick the plate.
        self.sciclops.pick_plate_direct(
            source=source,
            plate_type=plate_def,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            incremental_lift=incremental_lift,
        )

        # Push plate resource into gripper resource as a child.
        if plate_resource:
            self.resource_client.push(
                resource=self.gripper_resource, child=plate_resource
            )

        return None

    @action()
    def place(
        self,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in mm."] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        replacing_lid: Annotated[bool, "Are you replacing a lid?"] = False,
    ) -> None:
        """Places labware at a location."""

        target.representation["name"] = target.location_name
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{target}")
        print(f"{type(target)}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions."
                ]
            )

        # Check state of resources in ResourceClient.
        plate_resource = None
        if (self.resource_client is not None) and (self.location_client is not None):
            # Does a plate resource exist in the gripper?
            self.gripper_resource = self.resource_client.get_resource(
                self.gripper_resource
            )  # update the gripper resource
            if len(self.gripper_resource.children) == 1:
                plate_resource = self.gripper_resource.child
            else:
                return ActionFailed(
                    errors=[
                        "No plate resource exists in the gripper. Place action cannot be completed."
                    ]
                )

            # Is the target location clear?
            target_resource_id = self.location_client.get_location_by_name(
                target.name
            ).resource_id
            target_resource = self.resource_client.get_resource(target_resource_id)

            if len(target_resource.children) == 1 and target.location_type != "stack":
                # Do not fail the action if there's already a plate in a stack target location.
                return ActionFailed(
                    errors=[
                        f"A plate resource already exists at the target location {target.name}. The place action cannot be completed."
                    ]
                )

        else:
            self.logger.log_warning(
                f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
            )

        # Physically place the plate.
        self.sciclops.place_plate_direct(
            target=target,
            plate_type=plate_def,
            is_lid=is_lid,
            replacing_lid=replace_lid,
            grip_height_offset=height_offset,
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
        source_height_offset: Annotated[int, "Height offset in mm."] = 0,
        target_height_offset: Annotated[int, "Height offset in mm."] = 0,
        has_lid: Annotated[bool, "Does the plate have a lid?"] = False,
    ) -> None:
        """Transfers a plate from one location to another."""

        # Pick the plate.
        pick_result = self.pick(
            source=source,
            plate_type=plate_type,
            height_offset=source_height_offset,
            is_lid=False,  # assuming this transfer funtion is for the main labware. Remove/replace lid works for lids.
            has_lid=has_lid,
        )
        if pick_result is not None:
            # Return any ActionFailed response received.
            # Fails the action, but does not put the device into an error state.
            return pick_result

        # Place the plate.
        place_result = self.place(
            target=target,
            plate_type=plate_type,
            height_offset=target_height_offset,
            is_lid=False,  # assuming we're not using this transfer function to move lids.
            replacing_lid=False,
        )
        return place_result

    @action()
    def remove_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[
            str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well"
        ],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[
            bool, "True to ignore ResourceClient validations, False otherwise."
        ] = False,
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = SciClopsLocation.model_validate(source.representation)
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{source=}")
        print(f"{type(source)=}")

        print(f"{target=}")
        print(f"{type(target)=}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions."
                ]
            )

        # Complete MADSci resource checks.
        lid_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structure conformity with a Pydantic model.
            if (self.resource_client is not None) and (
                self.location_client is not None
            ):
                # Is a lid resource present on the source location for removal?
                source_resource_id = self.location_client.get_location_by_name(
                    source.name
                ).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if len(source_resource.children) == 1:
                    plate_resource = source_resource.child
                    if "lid_slot" in plate_resource.children:
                        lid_slot_child_value = plate_resource.children["lid_slot"]
                        if isinstance(lid_slot_child_value, Slot):
                            if len(lid_slot_child_value.children) == 1:
                                lid_resource = (
                                    lid_slot_child_value.child
                                )  # collect lid resource
                                self.logger.log_info(
                                    f"Identified lid Slot resource {lid_resource.resource_id} for removal."
                                )
                            else:
                                return ActionFailed(
                                    errors=[
                                        f"No lid resource exists in the lid slot. {lid_slot_child_value}"
                                    ]
                                )
                        else:
                            return ActionFailed(
                                errors=[
                                    f"Lid slot child value is not of type Slot. {lid_slot_child_value=}"
                                ]
                            )
                    else:
                        return ActionFailed(
                            errors=f'No "lid" child exists on the plate resource {plate_resource.resource_id}'
                        )
                else:
                    return ActionFailed(
                        errors=[
                            f"No plate resource exists at source location {source.name}"
                        ]
                    )

                # Is the target location clear?
                target_resource_id = self.location_client.get_location_by_name(
                    target.name
                ).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if not len(target_resource.children) == 0:
                    return ActionFailed(
                        errors=[
                            f"A plate resource already exists at the target location {target.name}. The remove lid action cannot be completed."
                        ]
                    )

                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(
                    self.gripper_resource
                )  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(
                        errors=[
                            "A resource is already in the gripper. Pick action cannot be completed."
                        ]
                    )
            else:
                return ActionFailed(
                    f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
                )
        else:
            self.logger.log_info("Skipping resources validation for remove lid action.")

        self.sciclops.remove_lid(
            source=source,
            target=target,
            plate_type=plate_def,
            grip_height_offset=height_offset,
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
                return ActionFailed(
                    errors=[f"Lid resource could not be removed in ResourceClient. {e}"]
                )
        else:
            return ActionFailed(
                f"lid_resource or target_resource do not exist. {lid_resource=}, {target_resource=}"
            )

    @action()
    def replace_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[
            str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well'"
        ],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[
            bool, "True to ignore ResourceClient validations, False otherwise."
        ] = False,
    ) -> None:
        """Replaces a lid on a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = SciClopsLocation.model_validate(source.representation)
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{source=}")
        print(f"{type(source)=}")

        print(f"{target=}")
        print(f"{type(target)=}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions."
                ]
            )

        # Complete MADSci resource checks.
        lid_resource = None
        lid_slot_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structure conformity with a Pydantic model.
            if (self.resource_client is not None) and (
                self.location_client is not None
            ):
                # Check for a lid resource in the source location.
                source_resource_id = self.location_client.get_location_by_name(
                    source.name
                ).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if (
                    len(source_resource.children) == 1
                ):  # source slot resource can only have one child
                    child_resource = source_resource.child
                    if "lid" in child_resource.attributes:
                        if source_resource.child.attributes["lid"] is True:
                            lid_resource = (
                                source_resource.child
                            )  # a lid exists at the source location
                        else:
                            return ActionFailed(
                                errors=[
                                    f'"lid" attribute is set to {source_resource.child.attributes["lid"]}.'
                                ]
                            )
                    else:
                        self.logger.log_warning(
                            f'Lid resource found does not conform to standard. No "lid" attribute found. {lid_resource}'
                        )
                else:
                    return ActionFailed(
                        errors=["No lid resource exists at source location."]
                    )

                # Check for a plate without a lid at the target location
                target_resource_id = self.location_client.get_location_by_name(
                    target.name
                ).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if len(target_resource.children) == 1:
                    plate_resource = target_resource.child
                    if "lid_slot" in plate_resource.children:
                        if len(plate_resource.children["lid_slot"].children) != 0:
                            return ActionFailed(
                                errors=[
                                    f"A lid resource already exists on the plate resource at the target location. plate_resource={plate_resource=}"
                                ]
                            )
                        lid_slot_resource = plate_resource.children["lid_slot"]
                    else:
                        return ActionFailed(
                            errors=[
                                f"Target plate resource has no lid slot resource. {target_resource=}"
                            ]
                        )
                else:
                    return ActionFailed(
                        errors=[
                            f"No plate resource exists at the target location {target.name}. The remove lid action cannot be completed."
                        ]
                    )

                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(
                    self.gripper_resource
                )  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(
                        errors=[
                            "A resource is already in the gripper. Pick action cannot be completed."
                        ]
                    )

            else:
                return ActionFailed(
                    f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
                )
        else:
            self.logger.log_info(
                "Skipping resources validation for replace lid action."
            )

        self.sciclops.replace_lid(
            source=source,
            target=target,
            plate_type=plate_def,
            grip_height_offset=height_offset,
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
                return ActionFailed(
                    errors=[
                        f"Lid resource could not be replaced in ResourceClient. {e}"
                    ]
                )
        else:
            return ActionFailed(
                f"lid_resource or lid_slot_resource do not exist. {lid_resource=}, {lid_slot_resource=}"
            )

    @action
    def get_current_position(self) -> list:
        """Returns the location joint angles of the SciClops."""
        # TODO: test this.
        return self.sciclops.get_current_position()


if __name__ == "__main__":
    sciclops_node = SciClopsNode(
        node_definition=NodeDefinition(
            node_name="sciclops_node", module_name="hudson_sciclops_node"
        )
    )
    sciclops_node.start_node()

# ---------------------------------------------------------------------------------

rest_module = RESTModule(
    name="sciclops_node",
    version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
    description="A node to control the sciclops plate moving robot",
    model="sciclops",
)


@rest_module.startup()
def sciclops_startup(state: State):
    """Initial run function for the app, initializes the state
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    state.sciclops = SCICLOPS()
    print("SCICLOPS online")


@rest_module.action()
def home(state: State):
    """Homes the sciclops"""
    response = state.sciclops.home()
    return (
        StepSucceeded()
        if state.sciclops.is_ok(response)
        else StepFailed(error=response)
    )


@rest_module.action(name="transfer_labware")
def transfer_labware(
    state: State,
    source: Annotated[str, "The source location to pick the labware"],
    target: Annotated[str, "The target location to place the labware"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate to transfer"
    ] = Falcon_96_well,
    has_lid: Annotated[bool, "Whether the labware has a lid currently"] = True,
):
    """Get a plate from a stack position and move it to transfer point (or trash)"""

    plate = Labware.model_validate(plate)
    state.sciclops.transfer_labware(
        source=source,
        target=target,
        plate=plate,
        has_lid=has_lid,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="pick_labware")
def pick_labware(
    state: State,
    source: Annotated[str, "The source location to pick the labware"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate to pick"
    ] = Falcon_96_well,
    gentle_lift: Annotated[
        bool, "Whether to gently lift (useful for separating lids)"
    ] = False,
):
    """Pick a plate from a stack position"""
    plate = Labware.model_validate(plate)
    state.sciclops.pick_labware(
        location_name=source,
        grip_height=plate.grip_height,
        labware_height=plate.height,
        gentle_lift=gentle_lift,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="place_labware")
def place_labware(
    state: State,
    target: Annotated[str, "The target location to place the labware"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate to place"
    ] = Falcon_96_well,
):
    """Place a plate at a stack position"""
    plate = Labware.model_validate(plate)
    state.sciclops.place_labware(
        location_name=target,
        grip_height=plate.grip_height,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="remove_lid")
def remove_lid(
    state: State,
    source: Annotated[str, "The source location to pick the lid from"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate and lid"
    ] = Falcon_96_well,
    target: Annotated[str, "The target location to place the lid"] = None,
):
    """Remove a lid from a plate"""
    plate = Labware.model_validate(plate)
    state.sciclops.remove_lid(
        source=source,
        plate=plate,
        target=target,
    )

    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="replace_lid")
def replace_lid(
    state: State,
    source: Annotated[str, "The source location to pick the lid from"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate and lid"
    ] = Falcon_96_well,
    target: Annotated[str, "The target location to place the lid"] = None,
):
    """Replace a lid on a plate"""
    plate = Labware.model_validate(plate)
    state.sciclops.replace_lid(
        source=source,
        plate=plate,
        target=target,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="remove_and_replace_lid")
def remove_and_replace_lid(
    state: State,
    source: Annotated[str, "The source location to pick the lid from"],
    plate: Annotated[
        Union[dict, Labware], "Information about the plate and lid"
    ] = Falcon_96_well,
    target: Annotated[str, "The target location to place the lid"] = None,
):
    """Remove a lid from a plate and place it on a different plate"""
    plate = Labware.model_validate(plate)
    state.sciclops.remove_and_replace_lid(
        source=source,
        plate=plate,
        target=target,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="pick_lid")
def pick_lid(
    state: State,
    source: Annotated[str, "The source location to pick the lid from"],
    plate: Annotated[
        Union[dict, Labware], "Information about the lid being picked"
    ] = Falcon_96_well,
):
    """Pick a lid from a plate at a location"""
    plate = Labware.model_validate(plate)
    state.sciclops.pick_lid(
        source=source,
        plate=plate,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="place_lid")
def place_lid(
    state: State,
    target: Annotated[str, "The target location to place the lid"],
    plate: Annotated[
        Union[dict, Labware], "Information about the lid being placed"
    ] = Falcon_96_well,
):
    """Place a lid on a plate at a location"""
    plate = Labware.model_validate(plate)
    state.sciclops.place_lid(
        target=target,
        plate=plate,
    )
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="move_to_location")
def move_to_location(
    state: State,
    location: Annotated[str, "The location to move to"],
):
    """Move the sciclops to a specific location at a specific height"""
    state.sciclops.move_loc(loc=location)
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="move_above_location")
def move_above_location(
    state: State,
    location: Annotated[str, "The location to move above"],
):
    """Move the sciclops above a specific location at a safe height"""
    state.sciclops.move_above_loc(loc=location)
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="move_to_location_with_height")
def move_to_location_with_height(
    state: State,
    location: Annotated[str, "The location to move to"],
    height: Annotated[int, "The height to move to in mm"] = 0,
):
    """Move the sciclops to a specific location at a specific height"""
    state.sciclops.move_loc_at_height(loc=location, height=height)
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="set_limp_mode")
def limp(
    state: State,
    limp: Annotated[bool, "Whether to set the sciclops in limp mode or not"] = True,
):
    """Frees or locks the joints of the sciclops, allowing it to be moved manually"""
    response = state.sciclops.limp(limp_bool=limp)
    return (
        StepSucceeded()
        if state.sciclops.is_ok(response)
        else StepFailed(error=response)
    )


@rest_module.action(name="jog")
def jog(
    state: State,
    axis: Annotated[str, "The axis to jog in (R, Z, Y, P)"] = "Z",
    distance: Annotated[int, "The distance to jog in mm"] = 1,
):
    """Jog the sciclops in a specific direction"""
    state.sciclops.jog(axis=axis, distance=distance)
    return (
        StepSucceeded()
        if state.sciclops.is_ok()
        else StepFailed(error="Sciclops status not ok.")
    )


@rest_module.action(name="set_speed")
def set_speed(
    state: State,
    speed: Annotated[int, "The speed to set the sciclops to, as a percentage"] = 100,
):
    """Set the speed of the sciclops"""
    response = state.sciclops.set_speed(speed=speed)
    return (
        StepSucceeded()
        if state.sciclops.is_ok(response)
        else StepFailed(error=response)
    )


@rest_module.action(name="open_gripper")
def open_gripper(
    state: State,
):
    """Open the gripper of the sciclops"""
    response = state.sciclops.open()
    return (
        StepSucceeded()
        if state.sciclops.is_ok(response)
        else StepFailed(error=response)
    )


@rest_module.action(name="close_gripper")
def close_gripper(
    state: State,
):
    """Close the gripper of the sciclops"""
    response = state.sciclops.close()
    return (
        StepSucceeded()
        if state.sciclops.is_ok(response)
        else StepFailed(error=response)
    )


@rest_module.action(name="get_position")
def get_position(
    state: State,
):
    """Get the current position of the sciclops"""
    position = state.sciclops.get_position()
    return StepSucceeded(data={"position": position})


rest_module.start()
