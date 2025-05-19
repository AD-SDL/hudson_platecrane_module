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
        joint_angles=[164681, -32703, 472, 5544],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack2": PlateCraneLocation(
        name="Stack2",
        joint_angles=[182220, -32703, 460, 5420],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack3": PlateCraneLocation(
        name="Stack3",
        joint_angles=[199708, -32703, 514, 5484],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack4": PlateCraneLocation(  # After vibration table
        name="Stack4",
        joint_angles=[216802, -32703, 412, 5504],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack5": PlateCraneLocation(  # After vibration table
        name="Stack5",
        joint_angles=[234356, -32703, 460, 5479],
        location_type="stack",
        safe_approach_height=0,
    ),
    "LidNest1": PlateCraneLocation(  # After vibration table
        name="LidNest1",
        joint_angles=[168355, -32100, 484, -306],
        location_type="nest",
        safe_approach_height=0,
    ),
    "LidNest2": PlateCraneLocation(
        name="LidNest2",
        joint_angles=[199805, -31800, 484, -306],
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
        joint_angles=[36703, -27951, -1000, 3630],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position2": PlateCraneLocation(  # After vibration table
        name="Solo.Position2",
        joint_angles=[57798, -27200, -260, 2481],
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
        joint_angles=[102688, -31390, -5923, 2400],
        location_type="nest",
        safe_approach_height=-27033,
    ),
    "Sealer.Nest": PlateCraneLocation(  # After vibration table
        name="Sealer.Nest",
        joint_angles=[119812, -1445, -4688, 4132],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Peeler.Nest": PlateCraneLocation(  # After vibration table
        name="Peeler.Nest",
        joint_angles=[302711, -30000, -4123, 2272],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Liconic.Nest": PlateCraneLocation(  # After vibration table
        name="Liconic.Nest",
        joint_angles=[267370, -24426, -5328, 1673],
        location_type="nest",
        safe_approach_height=0,
    ),
}

# Dimensions of labware used on the BIO_Workcells
plate_definitions = {
    "flat_bottom_96well": PlateResource(
        plate_height=14,
        grip_height=3,
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
}
