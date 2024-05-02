#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from platecrane_driver.sciclops_driver import SCICLOPS
from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleStatus,
    StepResponse,
    StepStatus,
)
from wei.helpers import extract_version

global sciclops, state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, initializes the state
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    global sciclops, state

    try:
        sciclops = SCICLOPS()

    except Exception as error_msg:
        state = "SCICLOPS CONNECTION ERROR"
        print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))

    else:
        print("SCICLOPS online")
    state = ModuleStatus.IDLE
    yield
    pass


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/state")
def get_state():
    """Returns the current state of the module"""
    global sealer, state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
    """Returns the current resources available to the module"""
    global sealer
    return JSONResponse(content={"State": sealer.get_status()})


@app.get("/about")
async def about() -> JSONResponse:
    """Returns a description of the actions and resources the module supports"""
    global state
    about = ModuleAbout(
        name="Sciclops Robotic Arm",
        description="Sciclops is a robotic arm module that grabs a plate from a specific tower location.",
        interface="wei_rest_node",
        version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
        actions=[
            ModuleAction(
                name="get_plate",
                description="This action gets a plate from a specified workcell location.",
                args=[
                    ModuleActionArg(
                        name="pos",
                        description="The workcell location to grab the plate from",
                        type="str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="lid",
                        description="Removes the lid from the plate at position `pos` if True. Default is False.",
                        type="bool",
                        required=False,
                    ),
                    ModuleActionArg(
                        name="trash",
                        description="Throws the lid in the trash if True. Default is False.",
                        type="bool",
                        required=False,
                    ),
                ],
            ),
            ModuleAction(
                name="status",
                description="This action checks the status information of the sciclops and fails if there's a problem.",
                args=[],
            ),
            ModuleAction(
                name="home",
                description="Resets sciclops robot to default home position.",
                args=[],
            ),
        ],
        resource_pools=[],
    )
    return JSONResponse(content=about.model_dump(mode="json"))


@app.post("/action")
def do_action(action_handle: str, action_vars):
    """
    Runs an action on the module

    Parameters
    ----------
    action_handle : str
       The name of the action to be performed
    action_vars : str
        Any arguments necessary to run that action.
        This should be a JSON object encoded as a string.

    Returns
    -------
    response: StepResponse
       A response object containing the result of the action
    """
    global state, sciclops
    response = StepResponse()
    if state == "SCICLOPS CONNECTION ERROR":
        message = "Connection error, cannot accept a job!"
        response.action_response = StepStatus.FAILED
        response.action_log = message
        return response
    if state == ModuleStatus.BUSY:
        return response

    state = ModuleStatus.BUSY

    if action_handle == "status":
        try:
            sciclops.get_status()
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = f"Get status failed. Error: {str(err)}"
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_log = "Get status successfully completed"

        state = ModuleStatus.IDLE
        return response

    elif action_handle == "home":
        try:
            sciclops.home()
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = f"Homing failed. Error: {str(err)}"
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_log = "Homing successfully completed"

        state = ModuleStatus.IDLE
        return response

    elif action_handle == "get_plate":
        vars = json.loads(action_vars)
        print(vars)

        pos = vars.get("pos")
        lid = vars.get("lid", False)
        trash = vars.get("trash", False)

        try:
            sciclops.get_plate(pos, lid, trash)
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = f"Get plate failed. Error: {str(err)}"
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_log = "Get plate successfully completed"

        state = ModuleStatus.IDLE

        return response

    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: status, home, get_plate"
        response.action_response = StepStatus.FAILED
        response.action_msg = msg
        state = ModuleStatus.IDLE
        return response


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Hostname that the REST API will be accessible on",
    )
    parser.add_argument("--port", type=int, default=2002)
    args = parser.parse_args()
    uvicorn.run(
        "sciclops_rest_node:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
