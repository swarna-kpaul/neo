from config.configurations import *
from solverfunctions import *
from models.buildstatespacemodel import *
import config.utilities as utilities
from environment.problemenvs import *
import random
import string
K=1

env = scienv()

class bootstrapenv():
    def __init__(self,):
         self.predescription = ""
         self.objective = ""
         self.examples = ""
         self.prioraxioms = """
         """
         self.environment = {"description": predescription + objective, "objective": objective, "prior axioms": prioraxioms, "belief axioms": "", "current state": self.getstate(), "examples": self.examples}
        return
    
     def reset(self):
        self.rootstate = True
        self.totalreward = 0
        self.toberesetflag = False
        
    def getstate(self):
        ############### derive current state from stm and ltm delta
        
        
        
        return
        
    def getfeedback(self):
        
        return
        
    def act(self,actiontext):
        try:
            exec_namespace = {}
            exec(actiontext,exec_namespace)
            result = exec_namespace.get("result", None)
        except Exception as e:
            raise world_exception("invalid action")
        return result
        
        
    def getpossibleactions(self):
        return
        
        
    def checkgoal(self):
        return
#solver(env)


###############################################
actions = [{"name": "Generate plan",
"description": "generates plan for solving a problem environment and takes the short term memory (STM) and long term memory(LTM) objects as arguments. Returns the plan in plain text",
"function": "generateplan(STM, LTM)"
},
{"name": "Generate code",
"description": "generates python code for an action plan for solving a problem environment. takes action plan, code error (if any for the previous generated code), the short term memory (STM) and long term memory(LTM) objects as arguments. Returns the executable python code in plain text",
"function": "generatecode(actionplan, codeerror, STM, LTM)"
},
{"name": "Belief learner",
"description": "Updates belief about the environment based on the outputs of the action taken. takes the short term memory (STM) and long term memory(LTM) objects as arguments. Returns learnt beliefs in plain text",
"function": "belieflearner(STM,LTM)"
},
# {"name": "Store action skill",
# "description": "Stores learnt action code that solves or nearly solves a problem environment, in long term memory. takes the short term memory (STM) and long term memory(LTM) objects as arguments. Returns learnt beliefs in plain text",
# "function": "belieflearner(STM,LTM)"
# }
{"name": "Belief learner",
"description": "Updates belief about the environment based on the outputs of the action taken. takes the short term memory (STM) and long term memory(LTM) objects as arguments. Returns learnt beliefs in plain text",
"function": "belieflearner(STM,LTM)"
}
]