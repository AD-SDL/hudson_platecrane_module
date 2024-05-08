#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import json
import traceback
from argparse import ArgumentParser, Namespace
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from platecrane_driver.platecrane_driver import PlateCrane
from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleStatus,
    StepResponse,
    StepStatus,
)
from wei.helpers import extract_version

global platecrane, state


def parse_args() -> Namespace:
    """Argument parser"""
    parser = ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Hostname that the REST API will be accessible on",
    )
    parser.add_argument("--port", type=int, default=2002)
    parser.add_argument("--device", type=str, default="/dev/ttyUSB0")
    return parser.parse_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the workcell argument
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    global platecrane, state

    args = parse_args()

    try:
        platecrane = PlateCrane(host_path=args.device)

    except Exception as error_msg:
        traceback.print_exc()
        state = "PLATECRANE CONNECTION ERROR"
        print("------- PlateCrane Error message: " + str(error_msg) + (" -------"))

    else:
        print("PLATECRANE online")
    state = ModuleStatus.IDLE
    yield
    pass


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/state")
def get_state():
    """Returns the current state of the platecrane"""
    global platecrane, state
    return JSONResponse(content={"State": state})


@app.get("/about")
async def about():
    """Returns a description of the actions and resources the module supports"""
    global state
    about = ModuleAbout(
        name="Hudson Platecrane",
        description="Platecrane is a robotic arm module that can pick up and move plates between locations.",
        interface="wei_rest_node",
        version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
        actions=[
            ModuleAction(
                name="transfer",
                description="This action picks up a plate from one location and transfers it to another.",
                args=[
                    ModuleActionArg(
                        name="source",
                        description="The workcell location to grab the plate from",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="target",
                        description="The workcell location to put the plate at",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="plate_type",
                        description="Type of plate.",
                        type="str",
                        required=False,
                        default="96_well",
                    ),
                ],
            ),
            ModuleAction(
                name="remove_lid",
                description="This action picks up a plate's lid from one location and places it at another.",
                args=[
                    ModuleActionArg(
                        name="source",
                        description="The workcell location to grab the lid from",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="target",
                        description="The workcell location to put the lid",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="plate_type",
                        description="Type of plate.",
                        type="str",
                        required=False,
                        default="96_well",
                    ),
                ],
            ),
            ModuleAction(
                name="replace_lid",
                description="This action picks up an unattached plate lid and places it on a plate.",
                args=[
                    ModuleActionArg(
                        name="source",
                        description="The workcell location to grab the lid from",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="target",
                        description="The workcell location to put the lid",
                        type="List[float], str",
                        required=True,
                    ),
                    ModuleActionArg(
                        name="plate_type",
                        description="Type of plate.",
                        type="str",
                        required=False,
                        default="96_well",
                    ),
                ],
            ),
            ModuleAction(
                name="move_safe",
                description="This action moves the arm to a safe location.",
                args=[],
            ),
        ],
        resource_pools=[],
    )
    return JSONResponse(content=about.model_dump(mode="json"))


@app.get("/resources")
async def resources():
    """Returns the current resources available to the module"""
    global platecrane
    return JSONResponse(content={"State": platecrane.get_status()})


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
    global state, platecrane
    response = StepResponse()
    if state == "PLATECRANE CONNECTION ERROR":
        message = "Connection error, cannot accept a job!"
        response.action_response = StepStatus.FAILED
        response.action_log = message
        return response
    if state == ModuleStatus.ERROR:
        return response

    action_args = json.loads(action_vars)

    state = ModuleStatus.BUSY

    source = action_args.get("source")
    print("Source location: " + str(source))
    target = action_args.get("target")
    print("Target location: " + str(target))
    plate_type = action_args.get("plate_type", "96_well")
    print("Plate type: " + str(target))
    height_offset = action_args.get("height_offset", 0)
    print("Height Offset: " + str(height_offset))

    if action_handle == "transfer":
        print("Starting the transfer request")

        source_type = action_args.get("source_type", None)
        print("Source Type: " + str(source_type))

        target_type = action_args.get("target_type", None)
        print("Target Type: " + str(target_type))

        if not source_type or not target_type:
            print("Please provide source and target transfer types!")
            state = ModuleStatus.ERROR

        try:
            platecrane.transfer(
                source,
                target,
                source_type=source_type.lower(),
                target_type=target_type.lower(),
                height_offset=int(height_offset),
                plate_type=plate_type,
            )
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Transfer failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Transfer successfully completed"
            state = ModuleStatus.IDLE
        print("Finished Action: " + action_handle.upper())
        return response

    elif action_handle == "remove_lid":
        try:
            platecrane.remove_lid(
                source=source,
                target=target,
                plate_type=plate_type,
                height_offset=height_offset,
            )
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Remove lid failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Remove lid successfully completed"
            state = ModuleStatus.IDLE
        print("Finished Action: " + action_handle.upper())
        return response

    elif action_handle == "replace_lid":
        try:
            platecrane.replace_lid(
                source=source,
                target=target,
                plate_type=plate_type,
                height_offset=height_offset,
            )
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Replace lid failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Replace lid successfully completed"
            state = ModuleStatus.IDLE
        print("Finished Action: " + action_handle.upper())
        return response

    elif action_handle == "move_safe":
        try:
            platecrane.move_location("Safe")
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Move Safe Failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Move Safe successfully completed"
            state = ModuleStatus.IDLE
        print("Finished Action: " + action_handle.upper())
        return response
    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: status, home, get_plate"
        response.action_response = StepStatus.FAILED
        response.action_log = msg
        state = ModuleStatus.ERROR
        return response


if __name__ == "__main__":
    import uvicorn

    args = parse_args()

    uvicorn.run(
        "platecrane_rest_node:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
