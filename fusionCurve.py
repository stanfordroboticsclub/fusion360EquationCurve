#Author-Michal Adamkiewicz
#Description-Plot function as sketch

import adsk.core, adsk.fusion, traceback
import math


#import system modules
import os, sys 

#get the path of add-in
my_addin_path = os.path.dirname(os.path.realpath(__file__)) 
print(my_addin_path)

#add the path to the searchable path collection
if not my_addin_path in sys.path:
   sys.path.append(my_addin_path) 


from asteval.asteval import Interpreter

defaultCurveName = 'Curve'
defaultCurveFunctionX = 'cos(t)'
defaultCurveFunctionY = 'sin(t)'
defaultCurveFunctionZ = 't'

defaultTStart = '0'
defaultTEnd   = '2*pi'
defaultTStep  = '0.1'

# defaultBodyDiameter = 0.5
# defaultHeadHeight = 0.3125
# defaultBodyLength = 2.0
# defaultCutAngle = 30.0 * (math.pi / 180)
# defaultChamferDistance = 0.03845
# defaultFilletRadius = 0.02994

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None

def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

class CurveCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            curve = Curve()
            for input in inputs:
                if input.id == 'curveName':
                    curve.curveName = input.value
                if input.id == 'curveFunctionX':
                    curve.xFunction = input.value
                if input.id == 'curveFunctionY':
                    curve.yFunction = input.value
                if input.id == 'curveFunctionZ':
                    curve.zFunction = input.value
                if input.id == 'tStart':
                    curve.tStart = input.value
                if input.id == 'tEnd':
                    curve.tEnd = input.value
                if input.id == 'tStep':
                    curve.tStep = input.value

            curve.buildCurve();
            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CurveCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CurveCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = CurveCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = CurveCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = CurveCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            #define the inputs
            inputs = cmd.commandInputs
            inputs.addStringValueInput('curveName', 'Sketch Name', defaultCurveName)
            inputs.addStringValueInput('curveFunctionX', 'Function x(t)', defaultCurveFunctionX)
            inputs.addStringValueInput('curveFunctionY', 'Function y(t)', defaultCurveFunctionY)
            inputs.addStringValueInput('curveFunctionZ', 'Function z(t)', defaultCurveFunctionZ)

            inputs.addStringValueInput('tStart', 't start', defaultTStart)
            inputs.addStringValueInput('tEnd',   't stop', defaultTEnd)
            inputs.addStringValueInput('tStep',  't step', defaultTStep)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def frange(x, y, jump=1.0):
    '''Range for floats.'''
    i = 0.0
    x = float(x)  # Prevent yielding integers.
    x0 = x
    epsilon = jump / 2.0
    yield x  # yield always first value
    while x + epsilon < y:
        i += 1.0
        x = x0 + i * jump
        yield x

class Curve:
    def __init__(self):
        self._curveName = defaultCurveName
        self._xFunction = defaultCurveFunctionX
        self._yFunction = defaultCurveFunctionY
        self._zFunction = defaultCurveFunctionZ

        self._tStart = defaultTStart
        self._tEnd = defaultTEnd
        self._tStep = defaultTStep

    #properties
    @property
    def curveName(self):
        return self._curveName
    @curveName.setter
    def curveName(self, value):
        self._curveName = value

    @property
    def xFunction(self):
        return self._xFunction
    @xFunction.setter
    def xFunction(self, value):
        self._xFunction = value

    @property
    def yFunction(self):
        return self._yFunction
    @yFunction.setter
    def yFunction(self, value):
        self._yFunction = value

    @property
    def zFunction(self):
        return self._zFunction
    @zFunction.setter
    def zFunction(self, value):
        self._zFunction = value

    @property
    def tStart(self):
        return self._tStart
    @tStart.setter
    def tStart(self, value):
        self._tStart = value

    @property
    def tEnd(self):
        return self._tEnd
    @tEnd.setter
    def tEnd(self, value):
        self._tEnd = value

    @property
    def tStep(self):
        return self._tStep
    @tStep.setter
    def tStep(self, value):
        self._tStep = value

    def buildCurve(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane

        aeval = Interpreter()
        aeval.symtable['pi'] = math.pi

        points = adsk.core.ObjectCollection.create()

        try:
            for time in frange(aeval(self.tStart), aeval(self.tEnd), aeval(self.tStep)):
                aeval.symtable['t'] = time
                point = adsk.core.Point3D.create(aeval(self.xFunction),
                                                 aeval(self.yFunction),
                                                 aeval(self.zFunction))
                points.add(point)
        except:
            print('something wrong')

        # product = app.activeProduct
        # design = adsk.fusion.Design.cast(product)
        # root = design.rootComponent
        # sketch = root.sketches.add(root.xYConstructionPlane)

        sketch = newComp.sketches.add(newComp.xYConstructionPlane)
        sketch.sketchCurves.sketchFittedSplines.add(points)
            # sketch.sketchCurves.sketchLines.addByTwoPoints(vertices[(i+1) %6], vertices[i])



def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        commandDefinitions = ui.commandDefinitions
        #check the command exists or not
        cmdDef = commandDefinitions.itemById('Equation Curve')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('Equation Curve',
                    'Create curve from equation',
                    'Create sketch curve from parametric equation',
                    './resources') # relative resource file path is specified

        onCommandCreated = CurveCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

