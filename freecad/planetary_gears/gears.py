from math import cos
from math import sin
from math import pi
import FreeCAD as App
import FreeCADGui as Gui

from freecad.gears.commands import CreateInvoluteGear
from freecad.gears.commands import CreateInternalInvoluteGear


class PlanetaryGearSet:

    def __init__(self, obj, gearset):
        self.gearset = gearset

        self.gears_group = self.gearset.newObject("App::DocumentObjectGroup", "Gears")
        self.planet_gears_links = []

        self.planet_gear_name = ""
        # only used when creating the gears
        self.sun_gear_name = ""
        self.ring_gear_name = ""

        self.add_gearset_properties(obj)
        self.add_ring_properties(obj)
        self.add_sun_properties(obj)
        self.add_planet_properties(obj)
        self.add_ratio_properties(obj)
        self.add_computed_properties(obj)

        obj.ring_teeth = 53
        obj.sun_teeth = 17
        obj.solve_for = "planet"
        obj.module = 1
        obj.planet_number = 5
        obj.pressure_angle = 20
        obj.height = 5
        obj.driving = "sun"
        obj.driven = "planet carrier"

        self.solve_for_planet(obj)
        self.update_computed(obj)

        # Creating the actual gears
        self.create_ring_gear(obj)
        self.create_sun_gear(obj)
        self.create_planet_gear(obj)
        self.add_gear_expressions(obj)

        obj.Proxy = self

    def add_gearset_properties(self, obj):
        obj.addProperty("App::PropertyEnumeration", "solve_for", "gearset_properties", "Choose between: planet, sun, ring")
        obj.solve_for = ["planet", "sun", "ring"]
        obj.addProperty("App::PropertyAngle", "beta", "gearset_properties")
        obj.addProperty("App::PropertyBool", "double_helix", "gearset_properties")
        obj.addProperty("App::PropertyFloat", "module", "gearset_properties")
        obj.addProperty("App::PropertyAngle", "pressure_angle", "gearset_properties")
        obj.addProperty("App::PropertyInteger", "planet_number", "gearset_properties")
        obj.addProperty("App::PropertyFloat", "height", "gearset_properties")

    def add_ring_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "ring_teeth", "ring_properties")
        obj.addProperty("App::PropertyAngle", "ring_angle", "ring_properties")

    def add_sun_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "sun_teeth", "sun_properties")
        obj.addProperty("App::PropertyAngle", "sun_angle", "sun_properties")
        obj.addProperty("App::PropertyFloat", "sun_clearance", "sun_properties", "Decrease the gear size by this amount.")

    def add_planet_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "planet_teeth", "planet_properties")
        obj.addProperty("App::PropertyFloat", "planet_clearance", "planet_properties", "Decrease the gear size by this amount.")

    def add_ratio_properties(self, obj):
        obj.addProperty("App::PropertyEnumeration", "driving", "ratio_properties", "The input gear.")
        obj.driving = ["sun", "ring", "planet carrier"]
        obj.addProperty("App::PropertyEnumeration", "driven", "ratio_properties", "The output gear. The third piece will be stationary.")
        obj.driven = ["sun", "ring", "planet carrier"]
        obj.addProperty("App::PropertyFloat", "ratio", "ratio_properties", "The output ratio.")
        obj.setEditorMode("ratio", 1)

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "sun_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "ring_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "planet_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "planetCenterDistance", "computed", "", 4)
        obj.addProperty("App::PropertyAngle", "theta", "computed", "", 4)
        obj.addProperty("App::PropertyAngle", "sun_angle_0", "computed", "", 4)

    def create_ring_gear(self, obj):
        ring_gear_body = self.gears_group.newObject("PartDesign::Body", "ring_gear")
        ring_gear_body.Visibility = False
        ring_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", ring_gear_body)
        ring_gear = CreateInternalInvoluteGear.create()
        self.ring_gear_name = ring_gear.Name

        # now add the link object which is shown in the "assembly" of the gearset
        ring_gear_link = self.gearset.newObject("App::Link", "ring")
        ring_gear_link.setLink(ring_gear_body)
        expression = f"<<{obj.Name}>>.ring_angle"
        ring_gear_link.setExpression("Placement.Rotation.Yaw", expression)
        expression = f"-<<{ring_gear.Name}>>.height/2"
        ring_gear_link.setExpression("Placement.Base.z", expression)

    def create_sun_gear(self, obj):
        sun_gear_body = self.gears_group.newObject("PartDesign::Body", "sun_gear")
        sun_gear_body.Visibility = False
        sun_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", sun_gear_body)
        sun_gear = CreateInvoluteGear.create()
        sun_gear.teeth = obj.sun_teeth
        sun_gear.module = obj.module
        self.sun_gear_name = sun_gear.Name

        # link sun gear
        sun_gear_link = self.gearset.newObject("App::Link", "sun")
        sun_gear_link.setLink(sun_gear_body)
        expression = f"<<{obj.Name}>>.sun_angle + <<{obj.Name}>>.sun_angle_0"
        sun_gear_link.setExpression("Placement.Rotation.Yaw", expression)
        expression = f"-<<{sun_gear.Name}>>.height/2"
        sun_gear_link.setExpression("Placement.Base.z", expression)

    def create_planet_gear(self, obj):
        planet_gear_body = self.gears_group.newObject("PartDesign::Body", "planet_gear")
        planet_gear_body.Visibility = False
        planet_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", planet_gear_body)
        planet_gear = CreateInvoluteGear.create()
        planet_gear.teeth = obj.planet_teeth
        planet_gear.module = obj.module
        self.planet_gears_links = []
        self.planet_gear_name = planet_gear.Name

        for i in range(1, obj.planet_number + 1):
            self.create_planet_link(obj, i)

    def create_planet_link(self, obj, i):
        planet_gear = App.ActiveDocument.getObject(self.planet_gear_name)
        planet_gear_body = App.ActiveDocument.getObject("planet_gear")
        planet_link = self.gearset.newObject("App::Link", f"planet{str(i)}")
        planet_link.setLink(planet_gear_body)
        expression = f"<<{obj.Name}>>.planet_{i}_position_x"
        planet_link.setExpression("Placement.Base.x", expression)
        expression = f"<<{obj.Name}>>.planet_{i}_position_y"
        planet_link.setExpression("Placement.Base.y", expression)
        expression = f"<<{obj.Name}>>.planet_{i}_position_angle"
        planet_link.setExpression("Placement.Rotation.Yaw", expression)
        expression = f"-<<{planet_gear.Name}>>.height/2"
        planet_link.setExpression("Placement.Base.z", expression)
        self.planet_gears_links.append(planet_link)

    def add_gear_expressions(self, obj):
        parameters = [
            "beta",
            "double_helix",
            "pressure_angle",
            "height"
        ]

        ring_gear = App.ActiveDocument.getObject(self.ring_gear_name)
        sun_gear = App.ActiveDocument.getObject(self.sun_gear_name)
        planet_gear = App.ActiveDocument.getObject(self.planet_gear_name)

        expression = f"<<{obj.Name}>>.ring_teeth"
        ring_gear.setExpression("teeth", expression)
        expression = f"<<{obj.Name}>>.sun_teeth"
        sun_gear.setExpression("teeth", expression)
        expression = f"<<{obj.Name}>>.planet_teeth"
        planet_gear.setExpression("teeth", expression)

        # Apply clearances.
        expression = f"<<{obj.Name}>>.module"
        ring_gear.setExpression("module", expression)
        expression = f"<<{obj.Name}>>.module * (1 - <<{obj.Name}>>.sun_clearance)"
        sun_gear.setExpression("module", expression)
        expression = f"<<{obj.Name}>>.module * (1 - <<{obj.Name}>>.planet_clearance)"
        planet_gear.setExpression("module", expression)

        for param in parameters:
            expression = f"<<{obj.Name}>>.{param}"
            ring_gear.setExpression(param, expression)
            sun_gear.setExpression(param, expression)
            planet_gear.setExpression(param, expression)

        # sun beta has to be negative
        expression = f"-<<{obj.Name}>>.beta"
        sun_gear.setExpression("beta", expression)

    def check_valid_teeth(self, obj):
        # Check the equal spacing condition
        k = (obj.sun_teeth + obj.ring_teeth) / obj.planet_number
        if k.is_integer() is False:
            App.Console.PrintWarning("This configuration doesn't allow equally spaced planets.\n")

    def solve_for_planet(self, obj):
        obj.setEditorMode("planet_teeth", 1)
        obj.setEditorMode("sun_teeth", 0)
        obj.setEditorMode("ring_teeth", 0)
        planet_teeth = (obj.ring_teeth - obj.sun_teeth)/2

        # Check the center distance condition
        if planet_teeth.is_integer() is False:
            App.Console.PrintWarning("This configuration of sun and ring gears is not allowed.\n")
        else:
            obj.planet_teeth = int(planet_teeth)

    def solve_for_sun(self, obj):
        obj.setEditorMode("planet_teeth", 0)
        obj.setEditorMode("sun_teeth", 1)
        obj.setEditorMode("ring_teeth", 0)

        obj.sun_teeth = obj.ring_teeth - 2*obj.planet_teeth

    def solve_for_ring(self, obj):
        obj.setEditorMode("planet_teeth", 0)
        obj.setEditorMode("sun_teeth", 0)
        obj.setEditorMode("ring_teeth", 1)

        obj.ring_teeth = obj.sun_teeth + 2*obj.planet_teeth

    def update_gears_teeth(self, obj):
        if obj.solve_for == "planet":
            self.solve_for_planet(obj)
        elif obj.solve_for == "sun":
            self.solve_for_sun(obj)
        elif obj.solve_for == "ring":
            self.solve_for_ring(obj)
        self.check_valid_teeth(obj)

    def update_computed(self, obj):
        obj.ring_dw = obj.module * obj.ring_teeth
        obj.sun_dw = obj.module * obj.sun_teeth
        obj.planet_dw = obj.module * obj.planet_teeth

        obj.planetCenterDistance = (obj.planet_dw + obj.sun_dw)/2

        # it's easier to adjust the sun rotation if it doesn't mesh when
        # the gars at initial position
        # return
        if obj.planet_teeth % 2 == 0:
            # need to rotate the sun gear one tooth to the next root
            obj.sun_angle_0 = 360 / (2 * obj.sun_teeth)
        else:
            obj.sun_angle_0 = 0

        # Rotation angle of the first planet gear with respect to x-axis
        obj.theta = (obj.ring_angle*obj.ring_teeth + obj.sun_angle*obj.sun_teeth) / (obj.ring_teeth + obj.sun_teeth)

        # Calculate gear ratio.
        if obj.driving == obj.driven:
            App.Console.PrintWarning("Driving and driven gears must be different.\n")

        driving = 1
        driven = 1
        planet_carrier = obj.ring_teeth + obj.sun_teeth
        if obj.driving == "sun":
            driving = obj.sun_teeth
        elif obj.driving == "ring":
            driving = obj.ring_teeth
        elif obj.driving == "planet carrier":
            driving = planet_carrier

        if obj.driven == "sun":
            driven = obj.sun_teeth
        elif obj.driven == "ring":
            driven = obj.ring_teeth
        elif obj.driven == "planet carrier":
            driven = planet_carrier

        obj.ratio = driven / driving

    def update_planets_placements(self, obj):
        planet_n = obj.planet_number
        properties = [k for k in obj.PropertiesList if "position" in k]

        for i in range(1, planet_n + 1):
            prop_names = [
                f"planet_{i}_position_x",
                f"planet_{i}_position_y",
                f"planet_{i}_position_angle",
            ]
            # put the calculated position parameters in the "computed" group
            for prop_name in prop_names:
                if not hasattr(obj, prop_name):
                    obj.addProperty("App::PropertyFloat", prop_name, "computed", "", 4)
                if prop_name in properties:
                    j = properties.index(prop_name)
                    del properties[j]

            # update planet position factors to try to put all the planets
            # around the sun

            # angle with respect to the x-axis formed by the placement of this
            # planet
            planet_angle_offset = 2*pi/planet_n * (i-1)
            angle = pi/180*obj.theta.Value + planet_angle_offset

            val = obj.planetCenterDistance * cos(angle)
            setattr(obj, f"planet_{i}_position_x", val)
            val = obj.planetCenterDistance * sin(angle)
            setattr(obj, f"planet_{i}_position_y", val)

            # need to adjust the planet rotation on its own axis in order to no
            # cause any interference problems
            # this method works on all cases I tried but I am not sure if it is
            # right
            val = -obj.sun_dw*obj.sun_angle.Value / (2*obj.planet_dw)
            setattr(obj, f"planet_{i}_position_angle", val)

        for prop in properties:
            obj.removeProperty(prop)

    def adjust_planet_number(self, fp):
        planet_n = fp.planet_number
        current_planets_n = len(self.planet_gears_links)

        if current_planets_n > planet_n:
            for i in range(planet_n, current_planets_n):
                planet_link = self.planet_gears_links.pop()
                App.ActiveDocument.removeObject(planet_link.Name)

        elif len(self.planet_gears_links) < planet_n:
            for i in range(current_planets_n+1, planet_n+1):
                self.create_planet_link(fp, i)

    def execute(self, fp):
        self.update_gears_teeth(fp)
        self.update_computed(fp)
        self.update_planets_placements(fp)

    def onChanged(self, fp, prop):
        if prop == "planet_number":
            self.adjust_planet_number(fp)

    def __getstate__(self):
        return (self.gearset.Name, len(self.planet_gears_links),
                self.planet_gear_name)

    def __setstate__(self, state):
        self.gearset = App.ActiveDocument.getObject(state[0])
        self.planet_gears_links = [ self.gearset.getObject(f"planet{str(i)}") for i in range(1, state[1] + 1) ]
        self.planet_gear_name = state[2]
