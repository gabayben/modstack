from enum import Enum

from modstack.typing import Serializable

Point = tuple[float, float]
Points = tuple[Point, ...]

class Orientation(Enum):
    SCREEN = (1, -1) # Origin in top left, y increases in the down direction
    CARTESIAN = (1, 1) # Origin in bottom left, y increases in upward direction

class CoordinateSystem(Serializable):
    """
    A finite coordinate plane with given width and height.
    """

    orientation: Orientation

class RelativeSpace(CoordinateSystem):
    """
    Relative coordinate system where x and y are on a scale from 0 to 1.
    """

    orientation: Orientation = Orientation.CARTESIAN

class PointSpace(CoordinateSystem):
    """
    Coordinate system representing a point space, such as a pdf. The origin is at the bottom left.
    """

    orientation: Orientation = Orientation.CARTESIAN

class PixelSpace(CoordinateSystem):
    """
    Coordinate system representing a pixel space, such as an image. The origin is at the top left.
    """

    orientation: Orientation = Orientation.SCREEN