#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path

from fastapi.datastructures import State
from platecrane_driver.sciclops_driver import SCICLOPS
from typing_extensions import Annotated
from wei.modules.rest_module import RESTModule
from wei.types.module_types import ModuleStatus
from wei.types.step_types import ActionRequest, StepResponse, StepStatus
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

    try:
        state.sciclops = SCICLOPS()
        print(state._state)
    except Exception as error_msg:
        state.status = ModuleStatus.ERROR
        print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))

    else:
        print("SCICLOPS online")
    state.status = ModuleStatus.IDLE
    yield
    pass


@rest_module.action(name="status", description="force sciclops to check its status")
def status(state: State, action: ActionRequest):
    return StepResponse(StepStatus.SUCCEEDED, state.sciclops.status())


@rest_module.action(name="home", description="force sciclops to check its status")
def home(state: State, action: ActionRequest):
    state.sciclops.home()
    return StepResponse(StepStatus.SUCCEEDED, "robot homed")


@rest_module.action(name="get_plate", description="force sciclops to check its status")
def get_plate(
    state: State,
    action: ActionRequest,
    pos: Annotated[int, "Stack to get plate from"],
    lid: Annotated[bool, "Whether plate has a lid or not"] = False,
    trash: Annotated[bool, "Whether to use the trash"] = False,
):
    print(state._state)
    state.sciclops.get_plate(pos, lid, trash)
    return StepResponse(StepStatus.SUCCEEDED, "robot homed")


rest_module.start()
