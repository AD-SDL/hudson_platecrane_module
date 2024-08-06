#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path

from fastapi.datastructures import State
from platecrane_driver.sciclops_driver import SCICLOPS
from typing_extensions import Annotated
from wei.modules.rest_module import RESTModule
from wei.types.module_types import ModuleStatus
from wei.types.step_types import StepResponse
from wei.utils import extract_version

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
    print("Hello, World!")
    try:
        state.sciclops = SCICLOPS()
        print(state._state)
    except Exception as error_msg:
        state.status = ModuleStatus.ERROR
        print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))

    else:
        print("SCICLOPS online")
    state.status = ModuleStatus.IDLE

@rest_module.action(name="status")
def status(state: State):
    """Action that forces the sciclops to check its status."""
    sciclops: SCICLOPS = state.sciclops
    sciclops.get_status()
    return StepResponse.step_succeeded(action_msg="Succesfully got status")

@rest_module.action()
def home(state: State):
    """Homes the sciclops"""
    state.sciclops.home()
    return StepResponse.step_succeeded()


@rest_module.action(name="get_plate")
def get_plate(
    state: State,
    pos: Annotated[int, "Stack to get plate from"],
    lid: Annotated[bool, "Whether plate has a lid or not"] = False,
    trash: Annotated[bool, "Whether to use the trash"] = False,
):
    """Get a plate from a stack position and move it to transfer point (or trash)"""
    state.sciclops.get_plate(pos, lid, trash)
    return StepResponse.step_succeeded()


rest_module.start()
