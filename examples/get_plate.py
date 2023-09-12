#!/usr/bin/env python3

'''
Example user imput to execute get_plate function in Hudson driver from message
'''

# import the SCICLOPS class from the hudson driver
from sciclops_driver import SCICLOPS

# example commands recieved by sciclops node
command = 'Get Plate 1'
var = {'location': 'tower1',
    'remove_lid': False,
    'trash': False
}

'''
OR
'''

command = 'Get Plate 1 Remove Lid'
var = {'location': 'tower1',
    'remove_lid': True,
    'trash': False
}

'''
OR
'''

command = 'Get Plate 1 Remove Lid Trash'
var = {'location': 'tower1',
    'remove_lid': True,
    'trash': True
}

# start instance of SCICLOPS class
sciclops = SCICLOPS()

# execute get plate function
sciclops.get_plate(location=var['location'], remove_lid=var['remove_lid'], trash=var['trash'])
