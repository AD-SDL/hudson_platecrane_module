#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import time
from pathlib import Path
from typing import Union

from fastapi.datastructures import State
from typing_extensions import Annotated
from wei.modules.rest_module import RESTModule
from wei.types.step_types import StepSucceeded
from wei.utils import extract_version

from platecrane_driver.resource_types import Falcon_96_well, Labware
from platecrane_driver.sciclops_driver import SCICLOPS

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
    state.sciclops.home()
    return StepSucceeded()


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
    return StepSucceeded()


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
    return StepSucceeded()


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
    return StepSucceeded()


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
    time.sleep(5)

    return StepSucceeded()


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
    return StepSucceeded()


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
    return StepSucceeded()


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
    return StepSucceeded()


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
    return StepSucceeded()


@rest_module.action(name="move_to_location")
def move_to_location(
    state: State,
    location: Annotated[str, "The location to move to"],
):
    """Move the sciclops to a specific location at a specific height"""
    state.sciclops.move_loc(loc=location)
    return StepSucceeded()


@rest_module.action(name="move_above_location")
def move_above_location(
    state: State,
    location: Annotated[str, "The location to move above"],
):
    """Move the sciclops above a specific location at a safe height"""
    state.sciclops.move_above_loc(loc=location)
    return StepSucceeded()


@rest_module.action(name="move_to_location_with_height")
def move_to_location_with_height(
    state: State,
    location: Annotated[str, "The location to move to"],
    height: Annotated[int, "The height to move to in mm"] = 0,
):
    """Move the sciclops to a specific location at a specific height"""
    state.sciclops.move_loc_at_height(loc=location, height=height)
    return StepSucceeded()


@rest_module.action(name="set_limp_mode")
def limp(
    state: State,
    limp: Annotated[bool, "Whether to set the sciclops in limp mode or not"] = True,
):
    """Frees or locks the joints of the sciclops, allowing it to be moved manually"""
    state.sciclops.limp(limp_bool=limp)
    return StepSucceeded()


@rest_module.action(name="jog")
def jog(
    state: State,
    axis: Annotated[str, "The axis to jog in (R, Z, Y, P)"] = "Z",
    distance: Annotated[int, "The distance to jog in mm"] = 1,
):
    """Jog the sciclops in a specific direction"""
    state.sciclops.jog(axis=axis, distance=distance)
    return StepSucceeded()


@rest_module.action(name="set_speed")
def set_speed(
    state: State,
    speed: Annotated[int, "The speed to set the sciclops to, as a percentage"] = 100,
):
    """Set the speed of the sciclops"""
    state.sciclops.set_speed(speed=speed)
    return StepSucceeded()


@rest_module.action(name="open_gripper")
def open_gripper(
    state: State,
):
    """Open the gripper of the sciclops"""
    state.sciclops.open()
    return StepSucceeded()


@rest_module.action(name="close_gripper")
def close_gripper(
    state: State,
):
    """Close the gripper of the sciclops"""
    state.sciclops.close()
    return StepSucceeded()


@rest_module.action(name="get_position")
def get_position(
    state: State,
):
    """Get the current position of the sciclops"""
    try:
        position = state.sciclops.get_position()
        return StepSucceeded(result=position)
    except Exception:  # * Sometimes the first call to get_position fails due
        position = state.sciclops.get_position()
        return StepSucceeded(
            result=position,
        )


rest_module.start()
