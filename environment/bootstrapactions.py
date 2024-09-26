from neo.environment.externalactions import *
from neo.environment.primitives import primitives
from neo.components.internalfunctions import *
import pickle
############################################### function set to be used while creating world object for FGPM
initworldbootfunctions= extfunctionset
# initworldbootfunctions.update(internalfunctionset)



              
############# Primitives to be used in prompt ########
ALLACTIONS = pickle.loads(pickle.dumps(primitives,-1))
_EXTACTIONS = {k: v["description"]+" "+ v["input"]+" "+v["output"] for k,v in initworldbootfunctions.items()}
EXTACTIONS = {k: (v["description"],v["description"]+" "+ v["input"]+" "+v["output"]) for k,v in initworldbootfunctions.items()}
ALLACTIONS.update(_EXTACTIONS)