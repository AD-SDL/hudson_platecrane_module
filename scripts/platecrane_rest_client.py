#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from platecrane_driver.platecrane_driver import PlateCrane

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
    state = "IDLE"
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
    response = {"action_response": "", "action_msg": "", "action_log": ""}
    if state == "SCICLOPS CONNECTION ERROR":
        message = "Connection error, cannot accept a job!"
        response["action_response"] = -1
        response["action_msg"] = message
        return response
    if state == "BUSY":
        return response

    state = "BUSY"

    if action_handle == "status":
        try:
            platecrane.get_status()
        except Exception as err:
            response["action_response"] = -1
            response["action_msg"] = "Get status failed. Error:" + err
        else:
            response["action_response"] = 0
            response["action_msg"] = "Get status successfully completed"

        state = "IDLE"
        return response

    elif action_handle == "home":
        try:
            platecrane.home()
        except Exception as err:
            response["action_response"] = -1
            response["action_msg"] = "Homing failed. Error:" + err
        else:
            response["action_response"] = 0
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
            platecrane.get_plate(pos, lid, trash)
        except Exception as err:
            response["action_response"] = -1
            response["action_msg"] = "Get plate failed. Error:" + err
        else:
            response["action_response"] = 0
            response["action_msg"] = "Get plate successfully completed"

        state = "IDLE"

        return response

    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: status, home, get_plate"
        response["action_response"] = -1
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
        "platecrane_rest_client:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
