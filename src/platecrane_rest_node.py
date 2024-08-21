#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path
from typing import List, Union

from fastapi.datastructures import State
from platecrane_driver.platecrane_driver import PlateCrane
from typing_extensions import Annotated
from wei.modules.rest_module import RESTModule
from wei.types.step_types import StepResponse, StepSucceeded
from wei.utils import extract_version

rest_module = RESTModule(
    name="platecrane_node",
    version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
    description="A node to control the Hudson PlateCrane robot",
    model="Hudson PlateCrane EX",
)

rest_module.arg_parser.add_argument("--device", type=str, default="/dev/ttyUSB0")

rest_module.state.platecrane = None


@rest_module.startup()
def platecrane_startup(state: State):
    """Handles initializing the platecrane driver."""
    state.platecrane = None
    state.platecrane = PlateCrane(host_path=state.device)
    print("PLATECRANE online")


@rest_module.action()
def transfer(
    state: State,
    source: Annotated[
        Union[List[float], str], "The workcell location to grab the plate from"
    ],
    target: Annotated[
        Union[List[float], str], "The workcell location to place the plate at"
    ],
    plate_type: Annotated[str, "The type of plate being manipulated"] = "96_well",
    height_offset: Annotated[
        int, "Amount to adjust the vertical grip point on the plate, in mm"
    ] = 0,
    has_lid: Annotated[
        bool, "Whether or not the plate currently has a lid on it"
    ] = False,
) -> StepResponse:
    """This action picks up a plate from one location and transfers is to another."""
    platecrane: PlateCrane = state.platecrane
    platecrane.transfer(
        source,
        target,
        plate_type=plate_type,
        height_offset=int(height_offset),
        has_lid=has_lid,
    )
    return StepSucceeded()


@rest_module.action()
def remove_lid(
    state: State,
    source: Annotated[
        Union[List[float], str], "The workcell location to grab the lib from"
    ],
    target: Annotated[
        Union[List[float], str], "The workcell location to place the lid at"
    ],
    plate_type: Annotated[str, "The type of plate the lid is on"] = "96_well",
    height_offset: Annotated[
        int, "Amount to adjust the vertical grip point on the plate, in mm"
    ] = 0,
):
    """This action picks up a plate lid from a plate and transfers is to another location."""
    platecrane: PlateCrane = state.platecrane
    platecrane.remove_lid(
        source=source,
        target=target,
        plate_type=plate_type,
        height_offset=height_offset,
    )
    return StepSucceeded()


@rest_module.action()
def replace_lid(
    state: State,
    source: Annotated[
        Union[List[float], str], "The workcell location to grab the lib from"
    ],
    target: Annotated[
        Union[List[float], str], "The workcell location to place the lid at"
    ],
    plate_type: Annotated[str, "The type of plate the lid is on"] = "96_well",
    height_offset: Annotated[
        int, "Amount to adjust the vertical grip point on the plate, in mm"
    ] = 0,
):
    """This action picks up a plate lid from a location and places it on a plate."""
    platecrane: PlateCrane = state.platecrane
    platecrane.replace_lid(
        source=source,
        target=target,
        plate_type=plate_type,
        height_offset=height_offset,
    )
    return StepSucceeded()


@rest_module.action()
def move_safe(
    state: State,
):
    """This action moves the arm to a safe location (the location named "Safe")."""
    platecrane: PlateCrane = state.platecrane
    platecrane.move_location("Safe")
    return StepSucceeded()


@rest_module.action()
def set_speed(
    state: State,
    speed: Annotated[int, "The speed at which the arm moves (as a percentage)."],
):
    """This action sets the speed at which the plate crane arm moves (as a percentage)"""
    platecrane: PlateCrane = state.platecrane
    platecrane.set_speed(speed=speed)
    return StepSucceeded()


if __name__ == "__main__":
    rest_module.start()
