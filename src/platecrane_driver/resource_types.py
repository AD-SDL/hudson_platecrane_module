"""This module contains the Pydantic models for the PlateCrane resource types"""

from typing import List, Optional

from pydantic import BaseModel


class Location(BaseModel):
    """A location accessible by the PlateCrane EX"""

    name: str
    """Internal name of the location"""
    joint_angles: List[int]
    """List of 4 joint angles (unit: integer stepper values)"""
    location_type: str
    """Type of location, either stack or nest. This will be used to determine gripper path for interactions with the location"""
    safe_approach_height: Optional[int] = None
    """A safe height (unit: integer stepper value for Z axis) from which
    to extend the arm when approaching this location."""


class PlateResource(BaseModel):
    """A plate resource that can be manipulated by the PlateCrane EX"""

    # Plate Properties

    plate_height: float
    """The height measured from the bottom of the plate to the top"""
    grip_height: float
    """The height at which to grip the plate, measured from the bottom of the plate"""
    plate_height_with_lid: Optional[float] = None
    """The height of the plate when lidded, measured from the bottom of the plate to the top of the lid.
    Only required if the resource supports lids"""

    # Lid Properties

    lid_height: Optional[float] = None
    """The height of the lid alone, measured from the bottom of the lid to the top of the lid"""
    lid_grip_height: Optional[float] = None
    """The height at which to grip the lid itself, measured from the bottom of the lid"""
    lid_removal_grip_height: Optional[float] = None
    """The height at which to grip the lid when removing it, measured from the bottom of the lidded plate"""

    def convert_to_steps(plate_measurement_in_mm: float) -> int:
        """Converts plate measurements in mm to PlateCrane EX motor steps on the z-axis"""
        steps_per_mm = 80.5
        steps = int(plate_measurement_in_mm * steps_per_mm)
        return steps

class Labware(BaseModel):
    """
    A labware resource that can be manipulated by the SCICLOPS

    All heights are measured from the bottom of the labware, in mm.
    """

    name: str
    """The name of the type of labware, used for identification"""
    height: float
    """The height of the labware in mm"""
    grip_height: float
    """The height at which the gripper should grip the labware in mm"""
    height_with_lid: float
    """The height of the labware with a lid in mm"""
    lid_removal_grip_height: float
    """The height at which the gripper should grip the lid to remove it in mm"""
    lid_height: float
    """The height of the lid in mm"""
    lid_grip_height: float
    """The height at which the gripper should grip the lid in mm"""

Falcon_96_well = Labware(
    name="Falcon 96-well microplate",
    height = 16.5,
    grip_height = 3.0,
    height_with_lid = 18.5,
    lid_removal_grip_height = 12.0,
    lid_height = 11.5,
    lid_grip_height = 5.0,
)
