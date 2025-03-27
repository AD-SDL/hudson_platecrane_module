"""Resource definitions for the platecrane in BIO 350."""

# from resource_types import Location, PlateResource  # through driver

from platecrane_driver.resource_types import Location, PlateResource  # through WEI

# Locations accessible by the PlateCrane EX. [R (base), Z (vertical axis), P (gripper rotation), Y (arm extension)]
locations = {
    "Safe": Location(
        name="Safe",
        joint_angles=[182220, 2500, 460, -308],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Stack1": Location(
        name="Stack1",
        joint_angles=[164672, -32703, 472, 5389],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack2": Location(
        name="Stack2",
        joint_angles=[182220, -32703, 460, 5420],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack3": Location(
        name="Stack3",
        joint_angles=[199708, -32703, 514, 5484],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack4": Location(
        name="Stack4",
        joint_angles=[217401, -32703, 546, 5473],
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack5": Location(
        name="Stack5",
        joint_angles=[235104, -32703, 532, 5453],
        location_type="stack",
        safe_approach_height=0,
    ),
    "LidNest1": Location(  # AFTER VIBRATION TABLE
        name="LidNest1",
        joint_angles=[168355, -32100, 484, -306],
        location_type="nest",
        safe_approach_height=0,
    ),
    "LidNest2": Location(
        name="LidNest2",
        joint_angles=[199805, -31800, 484, -306],
        location_type="nest",
        safe_approach_height=0,
    ),
    "LidNest3": Location(
        name="LidNest3",
        joint_angles=[231449, -31800, 484, -306],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position1": Location(
        name="Solo.Position1",
        joint_angles=[36703, -27951, -1000, 3630],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position2": Location(  # AFTER VIBRATION TABLE
        name="Solo.Position2",
        joint_angles=[57798, -27200, -260, 2481],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Solo.Position2AfterPeeler": Location(  # before vibration table
        name="Solo.Position2",
        joint_angles=[53225, -27960, -431, 855],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Hidex.Nest": Location(  # AFTER VIBRATION TABLE
        name="Hidex.Nest",
        joint_angles=[102917, -31090, -5923, 2356],
        location_type="nest",
        safe_approach_height=-27033,
    ),
    "Sealer.Nest": Location(  # AFTER VIBRATION TABLE
        name="Sealer.Nest",
        joint_angles=[119812, -1445, -4688, 4132],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Peeler.Nest": Location(  # AFTER VIBRATION Table
        name="Peeler.Nest",
        joint_angles=[302711, -30000, -4123, 2272],
        location_type="nest",
        safe_approach_height=0,
    ),
    "Liconic.Nest": Location(  # AFTER VIBRATION TABLE
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
