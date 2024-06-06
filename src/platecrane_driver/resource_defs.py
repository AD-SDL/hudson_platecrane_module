from resource_types import Location, PlateResource
#from platecrane_driver.resource_types import Location, PlateResource

# Locations accessible by the PlateCrane EX
locations = {
    "Safe": Location(name="Safe", joint_angles=[182220, 2500, 460, -308], location_type="nest", safe_approach_height=0),
    "Stack1": Location(name="Stack1", joint_angles=[164672, -32623, 472, 5389], location_type="stack", safe_approach_height=0),
    "Stack2": Location(name="Stack2", joint_angles=[182220, -32623, 460, 5420], location_type="stack", safe_approach_height=0),
    "Stack3": Location(name="Stack3", joint_angles=[199708, -32623, 514, 5484], location_type="stack", safe_approach_height=0),
    "Stack4": Location(name="Stack4", joint_angles=[217401, -32623, 546, 5473], location_type="stack", safe_approach_height=0),
    "Stack5": Location(name="Stack5", joint_angles=[235104, -32623, 532, 5453], location_type="stack", safe_approach_height=0),
    "LidNest1": Location(name="LidNest1", joint_angles=[168355, -31500, 484, -306], location_type="nest", safe_approach_height=0),
    "LidNest2": Location(name="LidNest2", joint_angles=[199805, -31500, 484, -306], location_type="nest", safe_approach_height=0),
    "LidNest3": Location(name="LidNest3", joint_angles=[231449, -31500, 484, -306], location_type="nest", safe_approach_height=0),
    "Solo.Position1": Location(name="Solo.Position1", joint_angles=[36703, -27797, -1000, 3630], location_type="nest", safe_approach_height=0),
    "Solo.Position2": Location(name="Solo.Position2", joint_angles=[53182, -27797, -413, 834], location_type="nest", safe_approach_height=0),
    "Hidex.Nest": Location(name="Hidex.Nest", joint_angles=[102327, -30499, -5855, 2363], location_type="nest", safe_approach_height=0),
    "Liconic.Nest": Location(name="Liconic.Nest", joint_angles=[79498, -28067, -6710, 4099], location_type="nest", safe_approach_height=0),
    "Sealer.Nest": Location(name="Sealer.Nest", joint_angles=[117468, 1220, -4748, 4550], location_type="nest", safe_approach_height=0),
    "Peeler.Nest": Location(name="Peeler.Nest", joint_angles=[292611, -30758, -4469, 4257], location_type="nest", safe_approach_height=0),
}


# Dimensions of labware used on the BIO_Workcell
plate_definitions = {
    "flat_bottom_96well": PlateResource(plate_height = 14, grip_height=3, plate_height_with_lid=16, lid_height=10, lid_grip_height=4, lid_removal_grip_height=12),
    "tip_box_180uL": PlateResource(plate_height = 0, grip_height=0, plate_height_with_lid=0, lid_height=0, lid_grip_height=0, lid_removal_grip_height=0),
    "pcr_96well": PlateResource(plate_height = 0, grip_height=0, plate_height_with_lid=0, lid_height=0, lid_grip_height=0, lid_removal_grip_height=0),
}
