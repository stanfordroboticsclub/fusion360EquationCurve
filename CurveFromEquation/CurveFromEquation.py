#Author - Michal Adamkiewicz
#Email  - mikadam@stanford.edu
#License - GNU GPL v3
#Description - Plot parametric function as sketch

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

defaultCurveName = 'Equation Curve'
defaultCurveFunctionX = '50*cos(t)'
defaultCurveFunctionY = '50*sin(t)'
defaultCurveFunctionZ = 't'

defaultTStart = '0'
defaultTEnd   = '2*pi'
defaultTStep  = '0.1'

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
    #yields last one to ensure closed curves
    yield y

class Curve:
    def __init__(self):
        self.curveName = defaultCurveName
        self.xFunction = defaultCurveFunctionX
        self.yFunction = defaultCurveFunctionY
        self.zFunction = defaultCurveFunctionZ

        self.tStart = defaultTStart
        self.tEnd = defaultTEnd
        self.tStep = defaultTStep

    def buildCurve(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        unitsMgr = design.unitsManager

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane

        aeval = Interpreter()
        aeval.symtable['pi'] = math.pi

        points = adsk.core.ObjectCollection.create()

        try:
            for time in frange(aeval(self.tStart), aeval(self.tEnd), aeval(self.tStep)):
                aeval.symtable['t'] = time
                x = unitsMgr.convert(aeval(self.xFunction), unitsMgr.defaultLengthUnits, "internalUnits")
                y = unitsMgr.convert(aeval(self.yFunction), unitsMgr.defaultLengthUnits, "internalUnits")
                z = unitsMgr.convert(aeval(self.zFunction), unitsMgr.defaultLengthUnits, "internalUnits")

                point = adsk.core.Point3D.create(x,y,z)
                points.add(point)
        except:
            print('something wrong')

        newComp.name = self.curveName
        sketch = newComp.sketches.add(newComp.xYConstructionPlane)
        sketch.name = self.curveName 

        try:
                sketch.sketchCurves.sketchFittedSplines.add(points)
                # sketch.sketchCurves.sketchLines.addByTwoPoints(vertices[(i+1) %6], vertices[i])
        except:
            print('something wrong')




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
                    'Create sketch curve from parametric equation')

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

