import os
import FreeCAD as App

from freecad.planetary_gears import ICONPATH
from freecad.planetary_gears.gears import PlanetaryGearSet


class PlanetaryGearCalculatorCmd:
    def GetResources(self):
        return {
                "MenuText": "New planetary gearset",
                "ToolTip": "Create a new planetary gearset",
                "Pixmap": os.path.join(ICONPATH, "Gear.svg")
        }

    def IsActive(self):
        if App.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        # container of the gearset
        gearset = App.ActiveDocument.addObject("App::Part", "GearSet")

        # parameters of the gears (what controls the gearset)
        gear_properties_name = "gear_parameters"
        gear_properties = gearset.newObject("App::FeaturePython", gear_properties_name)

        # Center of the gearset
        lcs0 = gearset.newObject("PartDesign::CoordinateSystem", "Center")
        lcs0.Support = [(gearset.Origin.OriginFeatures[0], "")]
        lcs0.MapMode = "ObjectXY"
        lcs0.MapReversed = False
        PlanetaryGearSet(gear_properties, gearset)

        App.ActiveDocument.recompute()
