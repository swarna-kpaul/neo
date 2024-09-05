from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.bootstrapactions import ALLACTIONS, initworldbootfunctions,EXTACTIONS,primitives
from neo.config.memory import *
import neo.components.programgraph as pg
node_attributes_object.updateattrib({"R":0.0000001,"V":0.0000001,"EXPF":0.58,"N":1,"desc":""}) # R -> reward, V -> value, EXPF -> exploration factor
############ initialize environment



class bootstrapenv():
    def __init__(self, objective, shortdescription = "", examples = "", prioraxioms ="", stm = stm, ltm = ltm):
        self.STM =stm
        self.LTM = ltm
        self.environment = {"description": shortdescription + objective, "objective": objective, "prior axioms": prioraxioms, "current state": self.getstate(), "examples": examples, "actionset": []}
        
         
    #def initializeenv(self,EXTACTIONS,primitives,initworldbootfunctions,ALLACTIONS ):
        for k,v in EXTACTIONS.items():
             self.LTM.set(text=v,data=v,recordid=k,memorytype="externalactions")
        self.primitives = primitives
        self.graph = creategraph('programgraph')
        init_world = worldclass(initworldbootfunctions)
        self.initnode = createnode(self.graph,'iW',init_world)
        self.graph["nodes"][self.initnode]["desc"] = "Initializes the program with initial node"
         #self.skillgraph = creategraph('bootenv') 
         #self.initnode = createnode(self.skillgraph,'iW',init_world)
        self.environment["actionset"] = list(ALLACTIONS.keys())
        return
    
    def reset(self):
        self.rootstate = True
        self.totalreward = 0
        self.toberesetflag = False
        
    def getstate(self):
        ############### derive current state from stm and ltm delta
        state = stm.get("state")#stm.get("currentenv")['env']["belief axioms"] +"\n"+stm.get("envtrace")

        return state
        
    def getfeedback(self,terminalnode):
        envtrace,_ = pg.fetchenvtrace(self,terminalnode)
        return envtrace
        
    def act(self,actiontext,relevantnodeid=1):
        return pg.execprogram(self,relevantnodeid, actiontext)
        
        
       
    def checkgoal(self):
        return
        
        
env = bootstrapenv(objective = "You should take text input from the user. The user may ask question or provide instructions or ask to solve a task. You may need to answer questions, follow instructions and solve tasks based on users input. At the end ask for user feedback.", prioraxioms= "You can use the getanswer function to generate specific structured answer for a question on a context",shortdescription = "Carry out user commands")