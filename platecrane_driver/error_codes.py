"""Defines exceptions for error codes returned by the plate crane controller."""
from __future__ import annotations


class SerialError(Exception):
    """
    Error during serial communication.
    Corresponds to the responses E0 to E5.
    """

    @staticmethod
    def from_response(response: str) -> SerialError:
        """Create a SerialError from a response string."""
        error_map = {
            "E0": RelayError,
            "E1": CommandError,
            "E2": ProgramError,
            "E3": HardwareError,
            "E4": WriteProtectedError,
            "E5": BaseUnitError,
        }
        if response in error_map:
            return error_map[response]()
        return SerialError(f"Unexpected response: '{response}'")


class RelayError(SerialError):
    """Undefined timer, counter, data memory. Check if requested unit is valid. Corresponds to the response E0."""

    def __init__(self):
        """Create a new RelayError."""
        super().__init__(
            "Undefined timer, counter, data memory. Check if requested unit is valid."
        )


class CommandError(SerialError):
    """Invalid Command. Corresponds to the response E1."""

    def __init__(self):
        """Create a new CommandError."""
        super().__init__(
            "Invalid command. Check if communication is opened by CR, check command sent to controller, "
            "check for interruptions during string transmission."
        )


class ProgramError(SerialError):
    """Firmware issues. Corresponds to the response E2."""

    def __init__(self):
        """Create a new ProgramError."""
        super().__init__("Firmware lost, reprogram controller")


class HardwareError(SerialError):
    """Hardware faults. Corresponds to the response E3."""

    def __init__(self):
        """Create a new HardwareError."""
        super().__init__(
            "Controller hardware error, turn controller ON/OFF, controller is faulty and has to be replaced."
        )


class WriteProtectedError(SerialError):
    """Write protected error. Corresponds to the response E4."""

    def __init__(self):
        """Create a new WriteProtectedError."""
        super().__init__("Unauthorized access")


class BaseUnitError(SerialError):
    """Base unit error. Corresponds to the response E5."""

    def __init__(self):
        """Create a new BaseUnitError."""
        super().__init__("Unauthorized access")


class ErrorResponse(Exception):
    """Error during command execution. Corresponds to the data at address DM200."""

    @staticmethod
    def from_error_code(error_code: int) -> ErrorResponse:
        """Create an ErrorResponse from an integer error code."""
        error_code = int(
            hex(error_code)[-2:], base=16
        )  # convert to hex, take two last digits, parse as hex
        messages = {
            0x01: "General time out; Operation took longer than 15 Minutes",
            0x02: "General time out; Time out after previous time out; Operation longer than 5 Minutes",
            0x03: "Init time out; Initialization has taken too long",
            0x04: "Carousel miss count; Number of cassette positions during init wrong",
            0x07: "Gate OPEN time out",
            0x08: "Gate CLOSE time out",
            0x09: "Lift travel exceeds maximum value",
            0x0A: "Wrong Cassette; DM0 > DM29; Cassette number exceeds maximum cassette",
            0x0B: "Lift overflow; travel path exceeds maximum allowed path",
            0x0C: "Wrong Level; DM5 > DM25; Level does exceed the maximum available levels",
            0x0D: "Plate trace Error; Plate was not loaded/unloaded as expected from/to shovel",
            0x0E: "Init time out; System was not able to initialize",
            0x10: "Turn in Turn Init Sensor or not in safe position; Possible step loss",
            0x12: "Carousel Init time out",
            0x13: "Shovel OUT time out; shovel could not be extended",
            0x14: "Shovel IN time out; Shovel could not be retracted",
        }
        if error_code not in messages:
            return ErrorResponse(f"Unknown error code: {error_code}")
        return ErrorResponse(messages[error_code])
