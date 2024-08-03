from neo.environment.externalactions import *
import pickle
############################################### function set to be used while creating world object for FGPM
initworldbootfunctions= extfunctionset
# initworldbootfunctions.update(internalfunctionset)


######## Primitive actions for FGPM ###############
primitives = {"iW" : """Initial node; No input parameters; Ex: createnode(graph,"iW",init_world)""",
              "K": """Constant node always return a constant value set during creation of node; It has one input argument. Ex: createnode(graph,"K",2) - This creates a node with constant value 2.""",
              "+" : "Adds two input values; ",
              "-" : "subtracts 2nd argument from first.",
              "*" : "Multiplies 2 inputs",
              "/" : "Divides 1st argument by 2nd",
              '>' : "Checks if 1st argument is greater than 2nd",
              "&" : "logical AND between 2 input ",
              "|" : "logical OR between 2 inputs",
              "!" : "logical NOT of 1 input",
              "lp" : "2 inputs. executes parent node in 1st argument for k times, where k is value of 2nd argument",
              "=" : "checks equality between 2 input arguments.",
              "if" : "It has 3 input arguments. The 1st argument should be boolean. If 1st argument is true then the parent node in its 1nd argument is executed else the 3rd."
              }
              
############# Primitives to be used in prompt ########
ALLACTIONS = pickle.loads(pickle.dumps(primitives,-1))
_extactions = {k: v["description"]+" "+ v["input"]+" "+v["output"] for k,v in initworldbootfunctions.items()}
ALLACTIONS.update(_extactions)