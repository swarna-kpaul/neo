from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.bootstrapactions import *#ALLACTIONS, initworldbootfunctions,EXTACTIONS,primitives,getenvfeedback,
from neo.config.memory import *
from neo.config.utilities import summarize
import neo.components.programgraph as pg
node_attributes_object.updateattrib({"R":0.0000001,"V":0.0000001,"EXPF":0.58,"N":1,"desc":""}) # R -> reward, V -> value, EXPF -> exploration factor
############ initialize environment
import pickle


class bootstrapenv():
    def __init__(self, objective, rewriteprocmem = True, ltmprocmem = "C:/neo/data/proceduralmem.pickle",shortdescription = "", examples = "", prioraxioms ="", stm = stm, ltm = ltm):
        self.STM =stm
        self.LTM = ltm
        self.environment = {"description": shortdescription + objective, "objective": objective, "prior axioms": prioraxioms, "current state": self.getstate(), "examples": examples, "actionset": []}
        print("ltmprocmem",ltmprocmem)
        if rewriteprocmem:
            for k,v in EXTACTIONS.items():
                self.LTM.set(text=v[0],data=v[1],recordid=k,memorytype="externalactions")
            
            with open(ltmprocmem,'wb') as file:
                pickle.dump(self.LTM.memory["externalactions"],file)
        else:
            ######## load ltm
            with open(ltmprocmem,'rb') as file:
                self.LTM.memory["externalactions"] = pickle.load(file)
        self.inprogresssubtasks = []    
        self.primitives = primitives
        self.graph = creategraph('programgraph')
        init_world = worldclass(initworldbootfunctions,self)
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
        #return getenvstate(self)
        state = stm.get("state")#stm.get("currentenv")['env']["belief axioms"] +"\n"+stm.get("envtrace")

        return state
        
    def getfeedback(self):
        #envtrace,_ = pg.fetchenvtrace(self,terminalnode)
        return getenvfeedback(self)
        #return envtrace
        
    def act(self,actiontext,relevantnodeid=1):
        return pg.execprogram(self,relevantnodeid, actiontext)
        
        
       
    def checkgoal(self):
        return
        
        
