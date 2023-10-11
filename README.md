# platecrane_driver

A standalone python-based driver for controlling the sciclops and platecrane instruments.

## Installation

```
git clone https://github.com/AD-SDL/hudson_platecrane_module
cd hudson_platecrane_module
python setup.py install
```
## Description

A repository for the Hudson Plate Stacker (Sciclops).

This package guides a user to remotely control the sciclops.

Sciclops is the main object for removing microplates from the stackers and placing them on the exchange platform.

Sciclops has 4 controllable axes and a gripper.
<p>&nbsp;</p>
        Z: Vertical axis <br>
        R: Base turning axis <br>
        Y: Extension axis <br>
        P: Gripper turning axis

<p>&nbsp;</p>

## Current Features
* Sciclops initialization
* Movements (move to preset points. ex: Neutral, Stack 1, etc.)
* Precise movements (move to certain point or certain distance)
