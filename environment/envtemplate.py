from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.bootstrapactions import ALLACTIONS, initworldbootfunctions


class bootstrapenv():
    def __init__(self, objective, shortdescription = "", examples = "", prioraxioms ="", stm = STM, ltm = LTM, actionset = list(ALLACTIONS.keys())):
         self.STM =stm
         self.LTM = ltm
         init_world = worldclass(initworldbootfunctions)
         self.skillgraph = creategraph('bootenv') 
         self.initnode = createnode(self.skillgraph,'iW',init_world)
         self.environment = {"description": shortdescription + objective, "objective": objective, "prior axioms": prioraxioms, "belief axioms": "", "current state": self.getstate(), "examples": self.examples, "actionset": actionset}
        return
    
     def reset(self):
        self.rootstate = True
        self.totalreward = 0
        self.toberesetflag = False
        
    def getstate(self):
        ############### derive current state from stm and ltm delta
        state = stm.get("state")#stm.get("currentenv")['env']["belief axioms"] +"\n"+stm.get("envtrace")

        return state
        
    def getfeedback(self):
        state = stm.get("critique")
        return
        
    def act(self,actiontext):
        try:
            exec_namespace = {}
            exec(actiontext,exec_namespace)
            result = exec_namespace.get("result", None)
        except Exception as e:
            raise world_exception("invalid action")
        return result
        
       
    def checkgoal(self):
        return
        
        
env = bootstrapenv(objective = "You should take text input from the user. The user may ask question or provide instructions or ask to solve a task. You need to answer questions, follow instructions and solve tasks", shortdescription = "Carry out user commands")