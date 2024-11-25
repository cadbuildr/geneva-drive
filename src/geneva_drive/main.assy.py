# %%
import math
from foundation import (
    show,
    Sketch,
    Part,
    Assembly,
    Extrusion,
    Circle,
    Point,
    Line,
    Polygon,
    Lathe,
    RoundedCornerRectangle,
    TFHelper,
    Axis,
)

BASE_WIDTH = 50
BASE_LENGTH = 100
PIN_DISTANCE = BASE_LENGTH * 0.5
PIN_DIAMETER = 4
DISK_DIAMETER = 2 * PIN_DISTANCE / math.sqrt(2) + PIN_DIAMETER
SLIDING_CIRCLE_DIAMETER = DISK_DIAMETER * 0.8
BEARING_HEIGHT = 6
BEARING_DIAMETER = 19
BEARING_INNER_DIAMETER = 6
PLATE_THICKNESS = 2

PIN_HEIGHT = 8
LIP_HEIGHT = 2

DISK_TOLERANCE = 0.5
BEARING_PLATE_OFFSET = 3

# HEIGHT CALCULATION
CIRCLES_PART_HEIGHT = PLATE_THICKNESS + LIP_HEIGHT + BEARING_PLATE_OFFSET
CROSS_PART_HEIGHT = CIRCLES_PART_HEIGHT + PLATE_THICKNESS


class BallBearing626D(Part):
    # Key dimensions of the 626D ball bearing
    OUTER_DIAMETER = BEARING_DIAMETER  # mm
    INNER_DIAMETER = BEARING_INNER_DIAMETER  # mm
    HEIGHT = BEARING_HEIGHT  # mm

    def __init__(self):
        # Create the outer cylinder
        self.create_outer_cylinder()
        # Cut the inner hole
        self.create_inner_hole()
        self.paint("grey")

    def create_outer_cylinder(self):
        # Sketch on the XY plane
        sketch = Sketch(self.xy())
        # Create a circle with the outer diameter
        outer_circle = Circle(center=sketch.origin, radius=self.OUTER_DIAMETER / 2)
        # Extrude the circle to create a cylinder
        extrusion = Extrusion(outer_circle, self.HEIGHT)
        self.add_operation(extrusion)

    def create_inner_hole(self):
        # Sketch on the XY plane
        sketch = Sketch(self.xy())
        # Create a circle with the inner diameter
        inner_circle = Circle(center=sketch.origin, radius=self.INNER_DIAMETER / 2)
        # Extrude the circle to remove material, creating the hole
        hole_extrusion = Extrusion(inner_circle, self.HEIGHT, cut=True)
        self.add_operation(hole_extrusion)


class RoundedRectangularPlateWithPins(Part):
    # Key dimensions
    WIDTH = BASE_WIDTH  # mm
    LENGTH = BASE_LENGTH  # mm
    PIN_DIAMETER = 6  # mm  # TODO match with bore of ball bearing
    LIP_DIAMETER = 8  # mm
    LIP_HEIGHT = LIP_HEIGHT  # mm
    PIN_HEIGHT = 6  # mm
    PIN_DISTANCE = PIN_DISTANCE  # mm
    FILLET_RADIUS = 5  # mm
    PLATE_THICKNESS = PLATE_THICKNESS  # mm

    def __init__(self):
        super().__init__()
        self.create_plate()
        self.create_pins()
        self.paint("plywood")

    def create_plate(self):
        # Create the rectangular plate with rounded corners by using RoundedCornerRectangle
        sketch = Sketch(self.xy())
        center_point = sketch.origin
        plate = RoundedCornerRectangle.from_center_and_sides(
            center_point, self.LENGTH, self.WIDTH, self.FILLET_RADIUS
        )
        extrusion = Extrusion(
            plate, self.PLATE_THICKNESS
        )  # Extrude plate to 5 mm thickness
        self.add_operation(extrusion)

    def create_pins(self):
        # Create the two holes for the bearings by cutting extrusions
        # plane = self.pf.get_parallel_plane(self.xy(), self.PLATE_THICKNESS)
        sketch = Sketch(self.xy())

        # Calculate positions of the two holes
        pin1_center = Point(sketch, -self.PIN_DISTANCE / 2, 0)
        pin2_center = Point(sketch, self.PIN_DISTANCE / 2, 0)

        # Add the first pin lip
        circle1 = Circle(pin1_center, self.LIP_DIAMETER / 2)
        pin1 = Extrusion(
            circle1, start=self.PLATE_THICKNESS, end=CIRCLES_PART_HEIGHT, cut=False
        )  # Cutting through the plate
        self.add_operation(pin1)
        # Add the first pin
        pin_circle = Circle(pin1_center, self.PIN_DIAMETER / 2)
        pin = Extrusion(
            pin_circle,
            start=CIRCLES_PART_HEIGHT - BEARING_PLATE_OFFSET,
            end=CIRCLES_PART_HEIGHT + BEARING_HEIGHT - BEARING_PLATE_OFFSET,
            cut=False,
        )
        self.add_operation(pin)

        # Add the second pin lip
        circle2 = Circle(pin2_center, self.LIP_DIAMETER / 2)
        pin2 = Extrusion(
            circle2, start=self.PLATE_THICKNESS, end=CROSS_PART_HEIGHT, cut=False
        )  # Cutting through the plate
        self.add_operation(pin2)

        # Add the second pin
        pin_circle = Circle(pin2_center, self.PIN_DIAMETER / 2)
        pin = Extrusion(
            pin_circle,
            start=CROSS_PART_HEIGHT - BEARING_PLATE_OFFSET,
            end=CROSS_PART_HEIGHT + BEARING_HEIGHT - BEARING_PLATE_OFFSET,
            cut=False,
        )
        self.add_operation(pin)


class PlateWithBearingsAssembly(Assembly):
    def __init__(self):
        super().__init__()
        self.create_plate_with_bearings()

    def create_plate_with_bearings(self):
        # Create the plate
        plate = RoundedRectangularPlateWithPins()
        self.LIP_HEIGHT = plate.LIP_HEIGHT
        self.add_component(plate)  # Add to assembly without any transform (origin)

        # Create the first bearing and position it at the first hole
        bearing1 = BallBearing626D()
        bearing1_tf = TFHelper()
        bearing1_tf.translate_x(-PIN_DISTANCE / 2)
        bearing1_tf.translate_z(CIRCLES_PART_HEIGHT - BEARING_PLATE_OFFSET)
        self.add_component(bearing1, bearing1_tf.get_tf())  # Add first bearing

        # Create the second bearing and position it at the second hole
        bearing2 = BallBearing626D()
        bearing2_tf = TFHelper()
        bearing2_tf.translate_x(PIN_DISTANCE / 2)
        bearing2_tf.translate_z(CROSS_PART_HEIGHT - BEARING_PLATE_OFFSET)
        self.add_component(bearing2, bearing2_tf.get_tf())  # Add second bearing


class GenevaDiskAndHoles(Part):

    PART_THICKNESS = 5
    STEP_HEIGHT = PART_THICKNESS / 2
    DISK_DIAMETER = DISK_DIAMETER  # mm
    TOP_CIRCLE_DIAMETER = SLIDING_CIRCLE_DIAMETER
    CUT_DIAMETER = SLIDING_CIRCLE_DIAMETER
    CUT_OFFSET = PIN_DISTANCE
    LIP_HEIGHT = LIP_HEIGHT

    def __init__(self):
        super().__init__()
        self.create_disk()
        self.add_circle_cut()
        self.add_turning_pin()
        self.add_sliding_pin()
        self.paint("beige")

    def create_disk(self):
        """Profile then using lathe"""

        sketch = Sketch(self.yz())
        pen = sketch.pencil

        pen.line_to(0, BEARING_HEIGHT - BEARING_PLATE_OFFSET)
        pen.line(BEARING_DIAMETER / 2, 0)
        pen.line(0, -BEARING_HEIGHT + BEARING_PLATE_OFFSET)
        pen.line_to(self.DISK_DIAMETER / 2, pen.y)
        pen.line(0, self.STEP_HEIGHT)
        pen.line_to((self.TOP_CIRCLE_DIAMETER - DISK_TOLERANCE) / 2, pen.y)
        pen.line(0, self.STEP_HEIGHT)
        pen.line_to(0, pen.y)

        shape = pen.close()
        axis = Axis(Line(sketch.origin, Point(sketch, 0, 1)))
        lathe = Lathe(shape, axis)

        self.add_operation(lathe)

    def add_circle_cut(self):
        plane = self.pf.get_parallel_plane(self.xy(), self.STEP_HEIGHT)
        cut_sketch = Sketch(plane)
        shape = Circle(Point(cut_sketch, 0, self.CUT_OFFSET), self.CUT_DIAMETER / 2)
        cut_extrusion = Extrusion(shape, self.STEP_HEIGHT + self.LIP_HEIGHT, cut=True)
        self.add_operation(cut_extrusion)

    def add_turning_pin(self):
        plane = self.pf.get_parallel_plane(self.xy(), 2 * self.STEP_HEIGHT)
        sketch = Sketch(plane)
        pin_center = Point(sketch, 0.8 * (self.TOP_CIRCLE_DIAMETER / 2), 0)
        pin_circle = Circle(pin_center, PIN_DIAMETER / 2)
        pin = Extrusion(
            pin_circle,
            start=0,
            end=PIN_HEIGHT,
            cut=False,
        )
        self.add_operation(pin)

    def add_sliding_pin(self):
        plane = self.pf.get_parallel_plane(self.xy(), self.STEP_HEIGHT)
        sketch = Sketch(plane)
        pin_center = Point(sketch, 0, PIN_DISTANCE / math.sqrt(2))
        pin_circle = Circle(pin_center, PIN_DIAMETER / 2)
        pin = Extrusion(
            pin_circle,
            start=0,
            end=PIN_HEIGHT,
            cut=False,
        )
        self.add_operation(pin)


class GenevaDriveCrossSection(Part):
    WIDTH = SLIDING_CIRCLE_DIAMETER
    CUT_OFFSET = PIN_DISTANCE
    CUT_RADIUS = SLIDING_CIRCLE_DIAMETER / 2
    SLOT_START_OFFSET = PIN_DISTANCE - DISK_DIAMETER / 2
    CENTER_SLOT_OFFSET = WIDTH / 2
    SLOT_LENGTH = (CENTER_SLOT_OFFSET - SLOT_START_OFFSET) * 2
    SLOT_WIDTH = PIN_DIAMETER + 1
    CROSS_WIDTH = 1 + BEARING_HEIGHT - BEARING_PLATE_OFFSET

    def __init__(self):
        self.add_base_circle()
        self.cut_4_circles()
        self.cut_pin_slot()
        self.cut_bearing_hole()
        self.paint("brown")

    def add_base_circle(self):
        sketch = Sketch(self.xy())
        base_circle = Circle(sketch.origin, self.WIDTH / 2)
        extrusion = Extrusion(base_circle, self.CROSS_WIDTH)
        self.add_operation(extrusion)

    def cut_4_circles(self):
        sketch = Sketch(self.xy())
        points = [
            (0, self.CUT_OFFSET),
            (0, -self.CUT_OFFSET),
            (self.CUT_OFFSET, 0),
            (-self.CUT_OFFSET, 0),
        ]
        for p in points:
            circle = Circle(Point(sketch, *p), self.CUT_RADIUS)
            cut_extrusion = Extrusion(circle, self.CROSS_WIDTH, cut=True)
            self.add_operation(cut_extrusion)

    def cut_pin_slot(self):
        sketch = Sketch(self.xy())
        for i in range(4):
            orientation = i * math.pi / 2 + math.pi / 4
            px = math.cos(orientation) * self.CENTER_SLOT_OFFSET
            py = math.sin(orientation) * self.CENTER_SLOT_OFFSET

            dx_len = math.cos(orientation) * self.SLOT_LENGTH / 2
            dy_len = math.sin(orientation) * self.SLOT_LENGTH / 2
            dx_width = math.sin(orientation) * self.SLOT_WIDTH / 2
            dy_width = -math.cos(orientation) * self.SLOT_WIDTH / 2
            points = [
                (px - dx_len + dx_width, py - dy_len + dy_width),
                (px - dx_len - dx_width, py - dy_len - dy_width),
                (px + dx_len - dx_width, py + dy_len - dy_width),
                (px + dx_len + dx_width, py + dy_len + dy_width),
            ]

            lines = [
                Line(Point(sketch, *p1), Point(sketch, *p2))
                for p1, p2 in zip(points, points[1:])
            ]

            # slot_shape = RoundedCornerPolygon(lines, 2)
            slot_shape = Polygon(lines)
            slot_extrusion = Extrusion(slot_shape, self.CROSS_WIDTH, cut=True)
            self.add_operation(slot_extrusion)

    def cut_bearing_hole(self):
        sketch = Sketch(self.xy())
        bearing_hole = Circle(sketch.origin, BEARING_DIAMETER / 2)
        bearing_extrusion = Extrusion(bearing_hole, self.CROSS_WIDTH - 1, cut=True)
        self.add_operation(bearing_extrusion)


class GenevaDrive(Assembly):
    def __init__(self):
        super().__init__()
        self.add_plate_with_bearings()
        self.add_geneva_disk_and_holes()
        self.add_geneva_drive_cross_section()

    def add_plate_with_bearings(self):
        plate = PlateWithBearingsAssembly()
        self.add_component(plate)

    def add_geneva_disk_and_holes(self):
        disk = GenevaDiskAndHoles()
        disk_tf = TFHelper()
        disk_tf.translate_z(CIRCLES_PART_HEIGHT)
        disk_tf.translate_x(-PIN_DISTANCE / 2)
        self.add_component(disk, disk_tf.get_tf())

    def add_geneva_drive_cross_section(self):
        cross_section = GenevaDriveCrossSection()
        cross_section_tf = TFHelper()
        cross_section_tf.translate_z(CROSS_PART_HEIGHT)
        cross_section_tf.translate_x(PIN_DISTANCE / 2)
        self.add_component(cross_section, cross_section_tf.get_tf())


if __name__ == "__main__":
    show(GenevaDrive())

# %%
