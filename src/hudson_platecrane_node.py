"""A REST Node Module for the Hudson PlateCrane EX robot.

This module provides a MADSci Node-compliant REST API for controlling the Hudson PlateCrane EX robot.
It includes actions for transferring plates, removing lids, and
placing lids.
"""

from typing import Optional

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

    @action()
    def transfer() -> None:
        """Transfers a plate from one location to another."""

    @action()
    def remove_lid() -> None:
        """Removes a lid from a plate."""

    @action()
    def place_lid() -> None:
        """Places a lid on a plate."""

    @action()
    def home() -> None:
        """Moves the PlateCrane to the home position."""

    @action()
    def move() -> None:
        """Moves the PlateCrane to a specified position."""
