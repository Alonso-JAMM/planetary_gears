import os
import FreeCADGui as Gui
import FreeCAD as App
from freecad.planetary_gears import ICONPATH


class PlanetaryGearsWorkbench(Gui.Workbench):
    MenuText = "planetary gears"
    ToolTip = "planetary gears workbench"
    Icon = os.path.join(ICONPATH, "Gear.svg")
    toolbox = [
        "PlanetaryGearCalculatorCmd"
    ]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        from freecad.planetary_gears.commands import PlanetaryGearCalculatorCmd
        App.Console.PrintMessage("Initializing planetary gearbox workbench")
        self.appendToolbar("Gear", self.toolbox)
        self.appendMenu("Gear", self.toolbox)
        Gui.addCommand("PlanetaryGearCalculatorCmd", PlanetaryGearCalculatorCmd())

    def Activated(self):
        '''
        code which should be computed when a user switch to this workbench
        '''
        pass

    def Deactivated(self):
        '''
        code which should be computed when this workbench is deactivated
        '''
        pass


Gui.addWorkbench(PlanetaryGearsWorkbench())
