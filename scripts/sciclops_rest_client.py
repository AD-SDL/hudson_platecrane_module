#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleStatus,
    StepResponse,
    StepStatus,
)
from wei.helpers import extract_version

from platecrane_driver.sciclops_driver import SCICLOPS

global sciclops, state

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sciclops, state
    """Initial run function for the app, parses the workcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""

    try:
        sciclops = SCICLOPS()

    except Exception as error_msg:
        state = "SCICLOPS CONNECTION ERROR"
        print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))

    else:
        print("SCICLOPS online")
    state = "IDLE"
    yield
    pass


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/state")
def get_state():
    global sealer, state
    return JSONResponse(content={"State": state})


@app.get("/description")
async def description():
    global state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
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
                        description="The lid of the plate", 
                        type="str", 
                        required=False
                    ), 
                    ModuleActionArg(
                        name="trash",
                        description="Move plate to trash", 
                        type="str",
                        required=False
                    )                    
                ],
            ), 
            ModuleAction(
                name="status",
                description="This action retrieves the current status information for the sciclops as extra information."
            ), 
            ModuleAction(
                name="home", 
                description="Resets sclicops robot to default home position."
            )
        ],
        resource_pools=[],
    )
    return JSONResponse(content=about.model_dump(mode="json"))


@app.post("/action")
def do_action(action_handle: str, action_vars):
    global state, sciclops
    response = {"action_response": "", "action_msg": "", "action_log": ""}
    if state == "SCICLOPS CONNECTION ERROR":
        message = "Connection error, cannot accept a job!"
        response["action_response"] = "failed"
        response["action_msg"] = message
        return response
    if state == "BUSY":
        return response

    state = "BUSY"

    if action_handle == "status":
        try:
            sciclops.get_status()
        except Exception as err:
            response["action_response"] = "failed"
            response["action_msg"] = "Get status failed. Error:" + err
        else:
            response["action_response"] = "succeeded"
            response["action_msg"] = "Get status successfully completed"

        state = "IDLE"
        return response

    elif action_handle == "home":
        try:
            sciclops.home()
        except Exception as err:
            response["action_response"] = "failed"
            response["action_msg"] = "Homing failed. Error:" + err
        else:
            response["action_response"] = "succeeded"
            response["action_msg"] = "Homing successfully completed"

        state = "IDLE"
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
            response["action_response"] = "failed"
            response["action_msg"] = "Get plate failed. Error:" + err
        else:
            response["action_response"] = "succeeded"
            response["action_msg"] = "Get plate successfully completed"

        state = "IDLE"

        return response

    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: status, home, get_plate"
        response["action_response"] = "failed"
        response["action_msg"] = msg
        state = "ERROR"
        return response


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Hostname that the REST API will be accessible on")
    parser.add_argument("--port", type=int, default=2002)
    args = parser.parse_args()
    uvicorn.run(
        "sciclops_rest_client:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
