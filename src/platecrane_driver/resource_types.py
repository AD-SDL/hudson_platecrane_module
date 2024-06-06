from typing import List, Optional
from pydantic import BaseModel

class Location(BaseModel):
    
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
        """Converts plate measurements in mm to PlateCrane EX motor steps on the z-axis  """
        steps_per_mm = 80.5
        steps = (plate_measurement_in_mm * steps_per_mm).round()
        return steps

