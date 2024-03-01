# platecrane_driver

A python-based driver and rest API for controlling the sciclops and Hudson Platecrane instruments.

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

## Installation and Usage

### Python

You'll need `libusb` installed (on debian-based linux: `sudo apt install libusb-1.0-0-dev`)

```bash
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment on Linux or macOS
source .venv/bin/activate

# Alternatively, activate the virtual environment on Windows
# .venv\Scripts\activate

# Install the module and dependencies in the venv
pip install -e .

# Run the REST node for the Hudson Platecrane
python src/platecrane_rest_node.py --host 0.0.0.0 --port 2000

# Run the REST node for the Hudson Sciclops
python src/sciclops_rest_node.py --host 0.0.0.0 --port 2000
```

### Docker

1. Install Docker for your platform of choice.
2. Run `make init` to create the `.env` file, or copy `example.env` to `.env`
3. Open the `.env` file and ensure that all values are set and correct.
    1. Check that the `USER_ID` and `GROUP_ID` are correct, as these ensure correct file permissions (in most cases, they should match your user's UID and GID)
    2. Check that the `WEI_DATA_DIR` and `REDIS_DIR` directories exist and have the appropriate permissions
    3. The `DEVICE` variable can be used to determine which USB serial device is used by the module

```bash
# Build and run just the module
docker compose up --build

# Run the module, but detach so you can keep working in the same terminal
docker compose up --build -d

# Run the module alongside a simple workcell (for testing)
docker compose -f wei.compose.yaml up --build -d
```

## Installation

```
git clone https://github.com/AD-SDL/hudson_platecrane_module
cd hudson_platecrane_module
python setup.py install
```
