#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from platecrane_driver.platecrane_driver import PlateCrane

from wei.core.data_classes import (
    ModuleStatus,
    StepResponse,
    StepStatus,
)

global platecrane, state

@asynccontextmanager
async def lifespan(app: FastAPI):
    global platecrane, state
    """Initial run function for the app, parses the workcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""

    try:
        platecrane = PlateCrane()

    except Exception as error_msg:
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
    global platecrane, state
    return JSONResponse(content={"State": state})


@app.get("/description")
async def description():
    global state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
    global platecrane
    return JSONResponse(content={"State": platecrane.get_status()})


@app.post("/action")
def do_action(action_handle: str, action_vars):
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

    source = action_args.get('source')
    print("Source location: " + str(source))
    target = action_args.get('target')
    print("Target location: "+ str(target))
    plate_type = action_args.get('plate_type', "96_well")
    print("Plate type: "+ str(target))

    if action_handle == 'transfer':
        print("Starting the transfer request")

        source_type = action_args.get('source_type', None)
        print("Source Type: " + str(source_type))

        target_type = action_args.get('target_type', None)
        print("Target Type: " + str(target_type))

        if not source_type or not target_type:
            print("Please provide source and target transfer types!")
            state = ModuleStatus.ERROR

        height_offset = action_args.get('height_offset', 0)
        print("Height Offset: " + str(height_offset))

        try:
            platecrane.transfer(source, target, source_type = source_type.lower(), target_type = target_type.lower(), height_offset = int(height_offset), plate_type = plate_type)
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Transfer failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Transfer successfully completed"
            state = ModuleStatus.IDLE
        print('Finished Action: ' + action_handle.upper())
        return response
    elif action_handle == "remove_lid":

        try:
            platecrane.remove_lid(source = source, target = target, plate_type = plate_type)
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Remove lid failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Remove lid successfully completed"
            state = ModuleStatus.IDLE
        print('Finished Action: ' + action_handle.upper())
        return response
    elif action_handle == "replace_lid":
        try:
            platecrane.replace_lid(source = source, target = target, plate_type = plate_type)
        except Exception as err:
            response.action_response = StepStatus.FAILED
            response.action_log = "Replace lid failed. Error:" + str(err)
            print(str(err))
            state = ModuleStatus.ERROR
        else:
            response.action_response = StepStatus.SUCCEEDED
            response.action_msg = "Replace lid  successfully completed"
            state = ModuleStatus.IDLE
        print('Finished Action: ' + action_handle.upper())
        return response
    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: status, home, get_plate"
        response.action_response = StepStatus.FAILED
        response.action_log = msg
        state = ModuleStatus.ERROR
        return response


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Hostname that the REST API will be accessible on")
    parser.add_argument("--port", type=int, default=2002)
    args = parser.parse_args()
    uvicorn.run(
        "platecrane_rest_node:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
