from types import Location, PlateResource


safe = Location(name="Safe", joint_angles=[182220, 2500, 460, -308], safe_approach_height=0)
stack1 = Location(name="Stack1", joint_angles=[164672, -32623, 472, 5389], safe_approach_height=0)
stack2 = Location(name="Stack2", joint_angles=[182220, -32623, 460, 5420], safe_approach_height=0)
# stack_source_loc = Location(name="Stack_source_loc", joint_angles=[])
# target_loc = Location(name="target_loc", joint_angles=[])
stack3 = Location(name="Stack3", joint_angles=[199708, -32623, 514, 5484], safe_approach_height=0)
stack4 = Location(name="Stack4", joint_angles=[217401, -32623, 546, 5473], safe_approach_height=0)
stack5 = Location(name="Stack5", joint_angles=[235104, -32623, 532, 5453], safe_approach_height=0)
lidnest1 = Location(name="LidNest1", joint_angles=[168355, -31500, 484, -306], safe_approach_height=0)
lidnest2 = Location(name="LidNest2", joint_angles=[199805, -31500, 484, -306], safe_approach_height=0)
lidnest3 = Location(name="LidNest3", joint_angles=[231449, -31500, 484, -306], safe_approach_height=0)
solo_position_1 = Location(name="Solo.Position1", joint_angles=[36703, -27797, -1000, 3630], safe_approach_height=0)
solo_position_2 = Location(name="Solo.Position2", joint_angles=[53182, -27797, -413, 834], safe_approach_height=0)
solo_position_3 = Location(name="Solo.Position3", joint_angles=[20085, -27000, -8850, 5236], safe_approach_height=0)
solo_position_4 = Location(name="Solo.Position4", joint_angles=[21612, -27209, -8787, 239], safe_approach_height=0)
solo_position_6 = Location(name="Solo.Position6", joint_angles=[48425, -27211, -7818, 2793], safe_approach_height=0)
hidex = Location(name="Hidex.Nest", joint_angles=[102327, -30499, -5855, 2363], safe_approach_height=0)
hidex_safe = Location(name="HidexSafe", joint_angles=[209959, -2500, 490, -262], safe_approach_height=0)
liconic = Location(name="Liconic.Nest", joint_angles=[79498, -28067, -6710, 4099], safe_approach_height=0)
sealer = Location(name="Sealer.Nest", joint_angles=[117468, 1220, -4748, 4550], safe_approach_height=0)
peeler = Location(name="Peeler.Nest", joint_angles=[292611, -30758, -4469, 4257], safe_approach_height=0)



plate96 = PlateResource(plate_height = 0, grip_height=0, plate_height_with_lid=0, lid_height=0, lid_grip_height=0, lid_removal_grip_height=0)
tipbox = PlateResource(plate_height = 0, grip_height=0, plate_height_with_lid=0, lid_height=0, lid_grip_height=0, lid_removal_grip_height=0)
platepcr = PlateResource(plate_height = 0, grip_height=0, plate_height_with_lid=0, lid_height=0, lid_grip_height=0, lid_removal_grip_height=0)
