"""Resource definitions for the platecrane in BIO 350."""

from platecrane_driver.resource_types import PlateResource, SciClopsLocation

# Locations accessible by the PlateCrane EX. [R (base), Z (vertical axis), P (gripper rotation), Y (arm extension)]

# Locations accessible by the SciClops. [Z (vertical axis), P (gripper rotation), Y (arm extension)]

# NOTE: THIS IS NOT THE SAME ORDER AS THE PLATE CRANE!

# NOTE: Running get location in the SciClops won't return the values in the right order!

locations = {
    "Safe": SciClopsLocation(
        name="Safe",
        joint_angles={"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955},
        location_type="nest",
        safe_approach_height=0,
    ),
    "Stack1": SciClopsLocation(
        name="Stack1",
        joint_angles={"Z": -397.1688, "R": 137.1106, "Y": 173.0127, "P": 9.6875},
        location_type="stack",
        safe_approach_height=0,
    ),
    "Stack2": SciClopsLocation(
        name="Stack2",
        joint_angles={"Z": -397.2875, "R": 154.9712, "Y": 172.5352, "P": 9.6875},
        location_type="stack",
        safe_approach_height=0,
    ),
    "LidNest1": SciClopsLocation(
        name="LidNest1",
        joint_angles={"Z": -386.8563, "R": 173.1300, "Y": 26.1751, "P": 10.3409},
        location_type="nest",
        safe_approach_height=0,
    ),
    "Home": SciClopsLocation(
        name="Home",
        joint_angles={"Z": -1.0188, "R": 0.0, "Y": 0.0, "P": -0.0284},
        location_type="stack",
        safe_approach_height=0,
    ),
}


# OLD PLATE DEFINITIONS
# # Dictionary for plate information
# locations = {
#     "stack1": {
#         "pos": {"Z": -397.1688, "R": 137.1106, "Y": 173.0127, "P": 9.6875},
#         "type": "stack",
#     },
#     "stack2": {
#         "pos": {"Z": -397.2875, "R": 154.9712, "Y": 172.5352, "P": 9.6875},
#         "type": "stack",
#     },
#     "stack3": {
#         "pos": {"Z": -397.3563, "R": 173.0506, "Y": 172.7398, "P": 9.6875},
#         "type": "stack",
#     },
#     "stack4": {
#         "pos": {"Z": -396.1000, "R": 191.1141, "Y": 172.4918, "P": 9.6875},
#         "type": "stack",
#     },
#     "stack5": {
#         "pos": {"Z": -394.4875, "R": 209.0771, "Y": 172.5104, "P": 9.6875},
#         "type": "stack",
#     },
#     "lidnest1": {  # Z:-381.0938, R:173.1300, Y:26.1751, P:10.3409
#         # "pos": {"Z": -388.8563, "R": 172.8812, "Y": 26.9317, "P": 10.3409},
#         "pos": {"Z": -386.8563, "R": 173.1300, "Y": 26.1751, "P": 10.3409},
#         "type": "nest",
#     },
#     "lidnest2": {  # Z:-379.2313, R:205.2971, Y:26.4480, P:10.2841
#         # "pos": {"Z": -388.4625, "R": 205.2900, "Y": 26.8139, "P": 10.2841},
#         "pos": {"Z": -386.8563, "R": 205.2971, "Y": 26.4480, "P": 10.2841},
#         "type": "nest",
#     },
#     "exchange": {
#         "pos": {"Z": -416.8438, "R": 299.8747, "Y": 153.6526, "P": 21.5057},
#         "type": "nest",
#     },
#     "neutral": {
#         "pos": {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955},
#         "type": "point",
#     },
# }

# locations = {
#     "Safe": PlateCraneLocation(
#         name="Safe",
#         joint_angles=[182220, 2500, 460, -308],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Stack1": PlateCraneLocation(  # After vibration table
#         name="Stack1",
#         joint_angles=[164713, -32703, 450, 5472],
#         location_type="stack",
#         safe_approach_height=0,
#     ),
#     "Stack2": PlateCraneLocation(
#         name="Stack2",
#         joint_angles=[182201, -32703, 486, 5445],
#         location_type="stack",
#         safe_approach_height=0,
#     ),
#     "Stack3": PlateCraneLocation(
#         name="Stack3",
#         joint_angles=[199696, -32703, 486, 5445],
#         location_type="stack",
#         safe_approach_height=0,
#     ),
#     "Stack4": PlateCraneLocation(  # After vibration table
#         name="Stack4",
#         joint_angles=[217301, -32703, 486, 5445],
#         location_type="stack",
#         safe_approach_height=0,
#     ),
#     "Stack5": PlateCraneLocation(  # After vibration table
#         name="Stack5",
#         joint_angles=[235004, -32703, 486, 5445],
#         location_type="stack",
#         safe_approach_height=0,
#     ),
#     "LidNest1": PlateCraneLocation(  # After vibration table
#         name="LidNest1",
#         joint_angles=[168367, -31725, 470, -329],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "LidNest2": PlateCraneLocation(
#         name="LidNest2",
#         joint_angles=[199862, -31725, 462, -328],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "LidNest3": PlateCraneLocation(
#         name="LidNest3",
#         joint_angles=[231449, -31800, 484, -306],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Solo.Position1": PlateCraneLocation(
#         name="Solo.Position1",
#         joint_angles=[41665, -27455, -830, 5046],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Solo.Position2": PlateCraneLocation(  # After vibration table
#         name="Solo.Position2",
#         joint_angles=[57372, -27457, -233, 2613],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Solo.Position2AfterPeeler": PlateCraneLocation(  # no longer needed
#         name="Solo.Position2",
#         joint_angles=[53225, -27960, -431, 855],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Hidex.Nest": PlateCraneLocation(  # After vibration table
#         name="Hidex.Nest",
#         joint_angles=[102406, -31090, -5901, 2373],
#         location_type="nest",
#         safe_approach_height=-27033,
#     ),
#     "Sealer.Nest": PlateCraneLocation(  # After vibration table
#         name="Sealer.Nest",
#         joint_angles=[118212, -998, -4758, 4071],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Sealer.DeepWell.Nest": PlateCraneLocation(  # After vibration table
#         name="Sealer.DeepWell.Nest",
#         joint_angles=[118212, -2498, -4758, 4071],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Peeler.Nest": PlateCraneLocation(  # After vibration table
#         name="Peeler.Nest",
#         joint_angles=[302738, -30340, -4142, 2351],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
#     "Liconic.Nest": PlateCraneLocation(  # After vibration table
#         name="Liconic.Nest",
#         joint_angles=[267724, -24666, -5357, 1591],
#         location_type="nest",
#         safe_approach_height=0,
#     ),
# }

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
        plate_height=40,
        grip_height=30,
        plate_height_with_lid=46,
        lid_height=9,
        lid_grip_height=4,
        lid_removal_grip_height=42,
    ),
}
