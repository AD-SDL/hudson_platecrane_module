# from resource_types import Location, PlateResource  # through driver
from platecrane_driver.resource_types import Location, PlateResource  # through WEI

# Locations accessible by the PlateCrane EX. [R (base), Z (vertical axis), P (gripper rotation), Y (arm extension)]
locations = {
    "Safe": Location(name="Safe", joint_angles=[182220, 2500, 460, -308], location_type="nest", safe_approach_height=0),
    "Stack1": Location(name="Stack1", joint_angles=[164672, -32703, 472, 5389], location_type="stack", safe_approach_height=0),
    "Stack2": Location(name="Stack2", joint_angles=[182220, -32703, 460, 5420], location_type="stack", safe_approach_height=0),
    "Stack3": Location(name="Stack3", joint_angles=[199708, -32703, 514, 5484], location_type="stack", safe_approach_height=0),
    "Stack4": Location(name="Stack4", joint_angles=[217401, -32703, 546, 5473], location_type="stack", safe_approach_height=0),
    "Stack5": Location(name="Stack5", joint_angles=[235104, -32703, 532, 5453], location_type="stack", safe_approach_height=0),
    "LidNest1": Location(name="LidNest1", joint_angles=[168355, -31800, 484, -306], location_type="nest", safe_approach_height=0),
    "LidNest2": Location(name="LidNest2", joint_angles=[199805, -31800, 484, -306], location_type="nest", safe_approach_height=0),
    "LidNest3": Location(name="LidNest3", joint_angles=[231449, -31800, 484, -306], location_type="nest", safe_approach_height=0),
    "Solo.Position1": Location(name="Solo.Position1", joint_angles=[36703, -27951, -1000, 3630], location_type="nest", safe_approach_height=0),
    "Solo.Position2": Location(name="Solo.Position2", joint_angles=[53182, -27951, -413, 834], location_type="nest", safe_approach_height=0),
    "Hidex.Nest": Location(name="Hidex.Nest", joint_angles=[102327, -31090, -5840, 2389], location_type="nest", safe_approach_height=-27033),
    "Sealer.Nest": Location(name="Sealer.Nest", joint_angles=[117412, 920, -4766, 4514], location_type="nest", safe_approach_height=0), 
    "Peeler.Nest": Location(name="Peeler.Nest", joint_angles=[292635, -31008, -4521, 4235], location_type="nest", safe_approach_height=0),
    "Liconic.Nest": Location(name="Liconic.Nest", joint_angles=[265563, -19800, -5413, 4978], location_type="nest", safe_approach_height=0),
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
