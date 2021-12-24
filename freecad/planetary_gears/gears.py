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


        self.add_gearset_properties(obj)
        self.add_ring_properties(obj)
        self.add_sun_properties(obj)
        self.add_planet_properties(obj)
        self.add_computed_properties(obj)

        obj.ring_teeth = 53
        obj.sun_teeth = 17
        obj.solve_for = "planet"
        obj.module = 1
        obj.planet_number = 5
        obj.pressure_angle = 20

        self.solve_for_planet(obj)
        self.update_computed(obj)

        # Creating the actual gears
        self.create_ring_gear(obj)
        self.create_sun_gear(obj)
        self.create_planet_gear(obj)
        self.add_gear_expressions(obj)

        obj.Proxy = self

    def add_gearset_properties(self, obj):
        obj.addProperty("App::PropertyString", "solve_for", "gearset_properties", "Choose between: planet, sun, ring")
        obj.addProperty("App::PropertyAngle", "beta", "gearset_properties")
        obj.addProperty("App::PropertyBool", "double_helix", "gearset_properties")
        obj.addProperty("App::PropertyFloat", "module", "gearset_properties")
        obj.addProperty("App::PropertyAngle", "pressure_angle", "gearset_properties")
        obj.addProperty("App::PropertyInteger", "planet_number", "gearset_properties")

    def add_ring_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "ring_teeth", "ring_properties")
        obj.addProperty("App::PropertyAngle", "ring_angle", "ring_properties")

    def add_sun_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "sun_teeth", "sun_properties")
        obj.addProperty("App::PropertyAngle", "sun_angle", "sun_properties")

    def add_planet_properties(self, obj):
        obj.addProperty("App::PropertyInteger", "planet_teeth", "planet_properties")
        #for i in range(1, obj.planet_number):
            #name = f"planet_{i}_position"
            #obj.addProperty("App::PropertyInteger", name, "planet_placement")

    def add_computed_properties(self, obj):
        obj.addProperty("App::PropertyFloat", "sun_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "ring_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "planet_dw", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "planetCenterDistance", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "ringPlanetRatio", "computed", "", 4)
        obj.addProperty("App::PropertyFloat", "transmissionRatio", "computed", "", 4)
        obj.addProperty("App::PropertyAngle", "theta_0", "computed", "", 4)
        obj.addProperty("App::PropertyAngle", "theta", "computed", "", 4)

    def create_ring_gear(self, obj):
        self.ring_gear_body = self.gears_group.newObject("PartDesign::Body", "ring_gear")
        self.ring_gear_body.Visibility = False
        self.ring_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", self.ring_gear_body)
        self.ring_gear = CreateInternalInvoluteGear.create()
        # gear parameters

        # now add the link object which is shown in the "assembly" of the gearset
        self.ring_gear_link = self.gearset.newObject("App::Link", "ring")
        self.ring_gear_link.setLink(self.ring_gear_body)
        expression = f"<<{obj.Name}>>.ring_angle"
        self.ring_gear_link.setExpression("Placement.Rotation.Yaw", expression)
        expression = f"-<<{self.ring_gear.Name}>>.height/2"
        self.ring_gear_link.setExpression("Placement.Base.z", expression)

    def create_sun_gear(self, obj):
        self.sun_gear_body = self.gears_group.newObject("PartDesign::Body", "sun_gear")
        self.sun_gear_body.Visibility = False
        self.sun_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", self.sun_gear_body)
        self.sun_gear = CreateInvoluteGear.create()
        self.sun_gear.teeth = obj.sun_teeth
        self.sun_gear.module = obj.module

        # link sun gear
        self.sun_gear_link = self.gearset.newObject("App::Link", "sun")
        self.sun_gear_link.setLink(self.sun_gear_body)
        expression = f"<<{obj.Name}>>.sun_angle"
        self.sun_gear_link.setExpression("Placement.Rotation.Yaw", expression)
        expression = f"-<<{self.sun_gear.Name}>>.height/2"
        self.sun_gear_link.setExpression("Placement.Base.z", expression)

    def create_planet_gear(self, obj):
        self.planet_gear_body = self.gears_group.newObject("PartDesign::Body", "planet_gear")
        self.planet_gear_body.Visibility = False
        self.planet_gear_body.newObject("PartDesign::CoordinateSystem", "Center")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", self.planet_gear_body)
        self.planet_gear = CreateInvoluteGear.create()
        self.planet_gear.teeth = obj.planet_teeth
        self.planet_gear.module = obj.module
        self.planet_gears_links = []

        for i in range(1, obj.planet_number + 1):
            planet_link = self.gearset.newObject("App::Link", f"planet{str(i)}")
            planet_link.setLink(self.planet_gear_body)
            expression = f"<<{obj.Name}>>.planet_{i}_position_x"
            planet_link.setExpression("Placement.Base.x", expression)
            expression = f"<<{obj.Name}>>.planet_{i}_position_y"
            planet_link.setExpression("Placement.Base.y", expression)
            expression = f"<<{obj.Name}>>.planet_{i}_position_angle"
            planet_link.setExpression("Placement.Rotation.Yaw", expression)
            expression = f"-<<{self.planet_gear.Name}>>.height/2"
            planet_link.setExpression("Placement.Base.z", expression)
            self.planet_gears_links.append(planet_link)

    def add_gear_expressions(self, obj):
        parameters = [
            "module",
            "beta",
            "double_helix",
            "pressure_angle"
        ]

        expression = f"<<{obj.Name}>>.ring_teeth"
        self.ring_gear.setExpression("teeth", expression)
        expression = f"<<{obj.Name}>>.sun_teeth"
        self.sun_gear.setExpression("teeth", expression)
        expression = f"<<{obj.Name}>>.planet_teeth"
        self.planet_gear.setExpression("teeth", expression)

        for param in parameters:
            expression = f"<<{obj.Name}>>.{param}"
            self.ring_gear.setExpression(param, expression)
            self.sun_gear.setExpression(param, expression)
            self.planet_gear.setExpression(param, expression)

        # sun beta has to be negative
        expression = f"-<<{obj.Name}>>.beta"
        self.sun_gear.setExpression("beta", expression)

    def solve_for_planet(self, obj):
        obj.setEditorMode("planet_teeth", 1)
        obj.setEditorMode("sun_teeth", 0)
        obj.setEditorMode("ring_teeth", 0)
        planet_teeth = (obj.ring_teeth - obj.sun_teeth)/2

        if planet_teeth.is_integer() is False:
            App.Console.PrintMessage("This configuration of sun and ring gears is not allowed")
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

    def update_computed(self, obj):
        obj.ring_dw = obj.module * obj.ring_teeth
        obj.sun_dw = obj.module * obj.sun_teeth
        obj.planet_dw = obj.module * obj.planet_teeth

        obj.planetCenterDistance = (obj.planet_dw + obj.sun_dw)/2
        obj.ringPlanetRatio = obj.ring_teeth / obj.planet_teeth
        obj.theta_0 = 180/(obj.ring_teeth + obj.sun_teeth)*(2 - (obj.planet_teeth + 1) % 2)
        obj.transmissionRatio = obj.ring_teeth/obj.sun_teeth + 1
        obj.theta = obj.sun_angle / obj.transmissionRatio + obj.theta_0 - obj.ring_angle / obj.transmissionRatio

    def update_planets_placements(self, obj):
        planet_n = obj.planet_number
        properties = [k for k in obj.PropertiesList if "position" in k]

        theta_0 = obj.theta_0
        n = 180 / (2*theta_0*planet_n)

        for i in range(1, planet_n + 1):
            prop_names = [
                #f"planet_{i}_position",
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
            planet_pos = int(n*i)

            # update planet placement values
            angle = pi/180*(obj.theta + obj.ring_angle + 4 * obj.theta_0 * planet_pos)
            val = obj.planetCenterDistance * cos(angle)
            setattr(obj, f"planet_{i}_position_x", val)
            val = obj.planetCenterDistance * sin(angle)
            setattr(obj, f"planet_{i}_position_y", val)
            val = obj.theta * (1 - obj.ringPlanetRatio) + obj.ring_angle
            setattr(obj, f"planet_{i}_position_angle", val.Value)

        if len(self.planet_gears_links) > planet_n:
            # there are more links than needed, removed extra
            for planet_link in self.planet_gears_links[planet_n:]:
                # To avoid errors about properties not existing due to the
                # document not being fully recomputed yet we remove the
                # expressions first
                planet_link.setExpression("Placement.Base.x", None)
                planet_link.setExpression("Placement.Base.y", None)
                planet_link.setExpression("Placement.Rotation.Yaw", None)
                App.ActiveDocument.removeObject(planet_link.Name)
            self.planet_gears_links = self.planet_gears_links[:planet_n]
        elif len(self.planet_gears_links) < planet_n:
            # there are less links than needed, add extra
            for i in range(len(self.planet_gears_links) + 1, planet_n + 1):
                planet_link = self.gearset.newObject("App::Link", f"planet{str(i)}")
                planet_link.setLink(self.planet_gear_body)
                # This will set the new link gear in the correct position
                # however, it will touched and need to recompute
                val = getattr(obj, f"planet_{i}_position_x")
                planet_link.Placement.Base.x = val
                val = getattr(obj, f"planet_{i}_position_y")
                planet_link.Placement.Base.y = val
                val = getattr(obj, f"planet_{i}_position_angle")
                planet_link.Placement.Rotation.Yaw = val
                val = -self.planet_gear.height/2
                planet_link.Placement.Base.z = val

                expression = f"<<{obj.Name}>>.planet_{i}_position_x"
                planet_link.setExpression("Placement.Base.x", expression)
                expression = f"<<{obj.Name}>>.planet_{i}_position_y"
                planet_link.setExpression("Placement.Base.y", expression)
                expression = f"<<{obj.Name}>>.planet_{i}_position_angle"
                planet_link.setExpression("Placement.Rotation.Yaw", expression)
                expression = f"-<<{self.planet_gear.Name}>>.height/2"
                planet_link.setExpression("Placement.Base.z", expression)
                self.planet_gears_links.append(planet_link)

        for prop in properties:
            obj.removeProperty(prop)

    def execute(self, fp):
        self.update_gears_teeth(fp)
        self.update_computed(fp)
        self.update_planets_placements(fp)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
