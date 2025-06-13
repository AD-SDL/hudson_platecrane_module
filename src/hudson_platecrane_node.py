"""A REST Node Module for the Hudson PlateCrane EX robot.

This module provides a MADSci Node-compliant REST API for controlling the Hudson PlateCrane EX robot.
It includes actions for transferring plates, removing lids, and
placing lids.
"""

from typing import Annotated, Optional

from madsci.client.resource_client import ResourceClient
from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.auth_types import OwnershipInfo
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from pydantic.fields import Field

from platecrane_driver.platecrane_driver import PlateCrane


class PlateCraneConfig(RestNodeConfig):
    """Configuration for the PlateCrane REST Node."""

    device: str = "/dev/ttyUSB0"
    """A device path for the serial port to connect to the PlateCrane robot."""
    baud_rate: int = 9600
    """The baud rate for the serial connection to the PlateCrane robot."""
    default_speed: int = 100
    """The default speed for the PlateCrane robot arm to move, as a percentage."""
    travel_height: int = Field(
        description="The travel height (Z value) for the PlateCrane robot arm to move to between transfers, in motor steps.",
    )


class PlateCraneNode(RestNode):
    """A REST MADSci Node for controlling the Hudson PlateCrane robot."""

    platecrane: Optional[PlateCrane] = None
    """The PlateCrane driver instance."""
    config_model = PlateCraneConfig
    """The configuration model for the PlateCrane REST Node."""
    config: PlateCraneConfig
    """The configuration for the PlateCrane REST Node."""

    def startup_handler(self) -> None:
        """Handles initializing the PlateCrane driver at node startup."""
        self.platecrane = PlateCrane(
            device_path=self.config.device, baud_rate=self.config.baud_rate
        )
        self.platecrane.initialize_platecrane()
        if self.config.resource_server_url:
            self.resource_client = ResourceClient(
                resource_server_url=self.config.resource_server_url,
                event_client=self.logger,
                ownership_info=OwnershipInfo(node_id=self.node_definition.node_id),
            )

    @action()
    def transfer(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        has_lid: Annotated[bool, "Does the plate have a lid?"] = False,
        source_grip_height_in_steps: Annotated[
            int, "Source grip height in motor steps"
        ] = 0,
        target_grip_height_in_steps: Annotated[
            int, "Target grip height in motor steps"
        ] = 0,
        incremental_lift: Annotated[bool, "Incremental lift during transfer"] = False,
    ) -> ActionResult:
        """Transfers a plate from one location to another."""
        self.platecrane.transfer(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            source_grip_height_in_steps=source_grip_height_in_steps,
            target_grip_height_in_steps=target_grip_height_in_steps,
            incremental_lift=incremental_lift,
        )

        return ActionSucceeded()

    @action()
    def remove_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. '96-well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
    ) -> ActionResult:
        """Removes a lid from a plate."""
        self.platecrane.remove_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )
        return ActionSucceeded()

    @action()
    def replace_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[str, "Type of plate, e.g. '96-well'"],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
    ) -> ActionResult:
        """Removes a lid from a plate."""
        self.platecrane.replace_lid(
            source=source,
            target=target,
            plate_type=plate_type,
            height_offset=height_offset,
        )
        return ActionSucceeded()

    @action()
    def home(self) -> ActionResult:
        """Moves the PlateCrane to the home position."""
        self.platecrane.home()
        return ActionSucceeded()

    @action()
    def move(self, target: LocationArgument) -> ActionResult:
        """Moves the PlateCrane to a specified position."""
        self.platecrane.move_joint_angles(
            r=target.location["R"],
            z=target.location["Z"],
            p=target.location["P"],
            y=target.location["Y"],
        )
