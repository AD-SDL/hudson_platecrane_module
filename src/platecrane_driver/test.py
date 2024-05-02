"""TESTS"""
if __name__ == "__main__":
    import platecrane_driver

    """
    Runs given function.
    """
    s = platecrane_driver.PlateCrane("/dev/ttyUSB2")
    # s.initialize()
    # s.home()
    stack4 = "Stack4"
    stack5 = "Stack5"
    solo6 = "Solo.Position6"
    solo4 = "Solo.Position4"
    solo3 = "Solo.Position3"
    target_loc = "HidexNest2"
    lidnest3 = "LidNest3"
    sealer = "SealerNest"
    # s.move_location("Safe")

    # s.move_location("Stack4")
    # s.move_single_axis("Z", "Safe", delay_time=1)  # move all the way up in z height

    # print(s.get_location_list())

    # s.transfer("Stack4","Solo.Position1",source_type="stack",target_type="stack",height_offset=800)  # test from stack to solo pos 1
    # s.transfer("Stack4","Solo.Position1",source_type="stack",target_type="stack")   # Stack 4 to SOLO 1

    # s.transfer("Solo.Position1","Stack5",source_type="stack",target_type="stack")   # SOLO 1 --> Stack 5

    # s.transfer("Stack5","Solo.Position1",source_type="stack",target_type="stack")   # Stack 4 to SOLO 1

    ###
    # s.transfer("Solo.Position1","Stack3",source_type="stack",target_type="stack")

    # s.transfer("Stack2","PeelerNest",source_type="stack",target_type="stack")

    # s.transfer("PeelerNest","Stack2",source_type="stack",target_type="stack")

    # s.transfer("Stack2","LidNest1",source_type="stack",target_type="stack")
    # s.transfer("Stack1","LidNest1",source_type="stack",target_type="stack")
    # s.transfer("LidNest1","Solo.Position1",source_type="stack",target_type="stack")
    # s.transfer("Solo.Position1","PeelerNest", source_type="stack", target_type="stack")
    # s.transfer("PeelerNest","Stack1",source_type="stack",target_type="stack")

    # s.transfer("Solo.Position1","Hidex.Nest",source_type="stack",target_type="module")

    # s.transfer("LidNest2","LidNest3",source_type="stack",target_type="stack")

    # s.transfer("LidNest3". "Solo.Position2", source_type="stack", target_type="stack")
    # s.transfer("PeelerNest","Stack2",source_type="stack",target_type="stack")

    # s.transfer("PeelerNest","Stack2",source_type="stack",target_type="stack")

    ###
    # s.transfer("Solo.Position1","Hidex.Nest",source_type="stack",target_type="module", height_offset=700)   # SOLO 1 to Hidex

    # s.transfer("Hidex.Nest","Solo.Position1",source_type="module",target_type="module")   # Stack 4 to SOLO 1

    ### Hidex Recalibration

    # print(s.get_position())

    # s.set_location("Safe", 195399, 2646, 0, 0)

    s.transfer(
        "Hidex.Nest",
        "Sealer.Nest",
        source_type="module",
        target_type="stack",
        height_offset=650,
    )

    print(s.get_location_list())


# old sealer nest 28:SealerNest, 210256, -1050, 491, 5730


# ----------------------------------------------------------------------------------------------------------------------------------------


# s.pick_stack_plate("Stack1")
# a = s.get_position()
# s.set_location("LidNest3",R=231449,Z=-31500,P=484,Y=-306)

# s.set_location("Hidex.Nest",R=a[0],Z=a[1],P=a[2],Y=a[3])
# s.place_module_plate("Hidex.Nest")
# s.move_single_axis("Z","Hidex.Nest")
# s.transfer("Hidex.Nest","Solo.Position1",source_type="module",target_type="stack",height_offset=800)
# s.transfer("Stack1", "PeelerNest",source_type="stack",target_type="stack")

# s.place_module_plate()
# s.get_location_list()

# s.move_joints_neutral()
# s.move_single_axis("R", "Safe", delay_time=1)
# s.set_location("Safe",R=195399,Z=0,P=0,Y=0)
# s.set_location("LidNest2",R=131719,Z=-31001,P=-5890,Y=-315)
# s.transfer(source="LidNest1",target="LidNest2",source_type="stack",target_type="stack", plate_type="96_well")

# s.transfer(source="LidNest2",target="LidNest3",source_type="stack",target_type="stack", plate_type="96_well")
# s.transfer("Stack1","Stack1")
# s.free_joints()
# s.lock_joints()

# s.set_location("LidNest3",R=99817,Z=-31001,P=-5890,Y=-315)

# s.get_location_joint_values("HidexNest2")
# s.set_location("HidexNest2", R=210015,Z=-30400,P=490,Y=2323)

# s.transfer(stack5, solo4, source_type = "stack", target_type = "module", plate_type = "96_deep_well")
# s.transfer(solo4, stack5, source_type = "module", target_type = "stack", plate_type = "96_deep_well")

# s.remove_lid(source = "LidNest1", target="LidNest2", plate_type="96_well")
# s.transfer("Stack4", solo3, source_type = "stack", target_type = "stack", plate_type = "tip_box_lid_off")
# s.remove_lid(source = solo6, target="LidNest3", plate_type="tip_box_lid_on")
# s.replace_lid(source = "LidNest3", target = solo6, plate_type = "tip_box_lid_on")
# s.replace_lid(source = "LidNest2", target = solo4, plate_type = "96_well")
# s.transfer(solo4, stack5, source_type = "module", target_type = "stack", plate_type = "96_well")
# s.transfer(solo6, "Stack2", source_type = "module", target_type = "stack", plate_type = "tip_box_lid_on")


#    Crash error outputs 21(R axis),14(z axis), 02 Wrong location name. 1400 (Z axis hits the plate), 00 success
# TODO: Need a response handler function. Unkown error messages T1, ATS, TU these are about connection issues (multiple access?)
# TODO: Slow the arm before hitting the plate in pick_stack_plate
# TODO: Create a plate detect function within pick stack plate function
# TODO: Maybe write another pick stack funtion to remove the plate detect movement
