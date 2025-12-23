"""Small ballistics utility helpers.

Functions:
- `speed_of_sound_c(temperature_c)`: approximate speed of sound in air (m/s)
- `speed_of_sound_fps(temperature_c)`: speed of sound in feet/sec
- `is_subsonic(velocity_fps, temperature_c, margin_fps=0)`: check if velocity is below speed-of-sound minus optional margin
"""

from typing import Union


def speed_of_sound_c(temperature_c: Union[float, int]) -> float:
    """Return speed of sound in air (m/s) at given temperature.

    Uses approximation: c = 331.3 + 0.606 * T
    """
    return 331.3 + 0.606 * float(temperature_c)


def speed_of_sound_fps(temperature_c: Union[float, int]) -> float:
    """Return speed of sound in feet per second at given temperature."""
    # 1 m/s = 3.2808398950131 ft/s
    return speed_of_sound_c(temperature_c) * 3.2808398950131


def is_subsonic(
    velocity_fps: Union[float, int],
    temperature_c: Union[float, int] = 15.0,
    margin_fps: float = 0.0,
) -> bool:
    """Return True if `velocity_fps` is below speed of sound at `temperature_c` minus `margin_fps`.

    margin_fps allows adding a safety buffer (e.g., 50 fps below transonic).
    """
    sos = speed_of_sound_fps(temperature_c)
    return float(velocity_fps) <= (sos - float(margin_fps))
