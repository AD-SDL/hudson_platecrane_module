"""Resource definitions for the platecrane in BIO 350."""

from platecrane_driver.resource_types import PlateCraneLocation, PlateResource

# Locations accessible by the PlateCrane EX. [R (base), Z (vertical axis), P (gripper rotation), Y (arm extension)]

locations = {
    "Safe": PlateCraneLocation(
        name="Safe",
        joint_angles=[182220, 2500, 460, -308],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Stack1": PlateCraneLocation(  # After vibration table
        name="Stack1",
        joint_angles=[164713, -32703, 450, 5472],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack2": PlateCraneLocation(
        name="Stack2",
        joint_angles=[182201, -32703, 486, 5445],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack3": PlateCraneLocation(
        name="Stack3",
        joint_angles=[199696, -32703, 486, 5445],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack4": PlateCraneLocation(  # After vibration table
        name="Stack4",
        joint_angles=[217301, -32703, 486, 5445],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack5": PlateCraneLocation(  # After vibration table
        name="Stack5",
        joint_angles=[235004, -32703, 486, 5445],
        location_type="stack",
        safe_approach_height=0,
    ),
    "LidNest1": PlateCraneLocation(  # After vibration table
        name="LidNest1",
        joint_angles=[168367, -31725, 470, -329],
        location_type="nest",
        safe_approach_height=0,
    ),
    "LidNest2": PlateCraneLocation(
        name="LidNest2",
        joint_angles=[199862, -31725, 462, -328],
        location_type="nest",
        safe_approach_height=0,
    ),
    "LidNest3": PlateCraneLocation(
        name="LidNest3",
        joint_angles=[231449, -31800, 484, -306],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position1": PlateCraneLocation(
        name="Solo.Position1",
        joint_angles=[41665, -27455, -830, 5046],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position2": PlateCraneLocation(  # After vibration table
        name="Solo.Position2",
        joint_angles=[57372, -27457, -233, 2613],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position2AfterPeeler": PlateCraneLocation(  # no longer needed
        name="Solo.Position2",
        joint_angles=[53225, -27960, -431, 855],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Hidex.Nest": PlateCraneLocation(  # After vibration table
        name="Hidex.Nest",
        joint_angles=[102406, -31090, -5901, 2373],
        location_type="nest",
        safe_approach_height=-27033,
    ),
    "Sealer.Nest": PlateCraneLocation(  # After vibration table
        name="Sealer.Nest",
        joint_angles=[118212, -998, -4758, 4071],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Sealer.DeepWell.Nest": PlateCraneLocation(  # After vibration table
        name="Sealer.DeepWell.Nest",
        joint_angles=[118212, -2498, -4758, 4071],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Peeler.Nest": PlateCraneLocation(  # After vibration table
        name="Peeler.Nest",
        joint_angles=[302738, -30340, -4142, 2351],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Liconic.Nest": PlateCraneLocation(  # After vibration table
        name="Liconic.Nest",
        joint_angles=[267724, -24666, -5357, 1591],
        location_type="nest",
        safe_approach_height=0,
    ),
}

# Dimensions of labware used on the BIO_Workcells
plate_definitions = {
    "flat_bottom_96well": PlateResource(
        plate_height=14,
        grip_height=1,
        plate_height_with_lid=16,
        lid_height=10,
        lid_grip_height=4,
        lid_removal_grip_height=12,
    ),
    "tip_box_180uL": PlateResource(
        plate_height=0,
        grip_height=0,
        plate_height_with_lid=0,
        lid_height=0,
        lid_grip_height=0,
        lid_removal_grip_height=0,
    ),
    "pcr_96well": PlateResource(
        plate_height=0,
        grip_height=0,
        plate_height_with_lid=0,
        lid_height=0,
        lid_grip_height=0,
        lid_removal_grip_height=0,
    ),
    "deep_96well": PlateResource(
        plate_height=36,
        grip_height=30,
        plate_height_with_lid=0,
        lid_height=0,
        lid_grip_height=0,
        lid_removal_grip_height=0,
    ),
}
