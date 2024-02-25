from config.configurations import *
from solverfunctions import *
from models.buildstatespacemodel import *
import config.utilities as utilities
from environment.problemenvs import *
import random
import string
K=3

env = scienv()

def solver(env):
    stm = STM()
    ltm = LTM()
    statespacemodel = envmodel()
    stm.set("currentenv", {"id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),"env": env.environment})
    stm.set("SPmodel", statespacemodel)
    stm.set("currentstate",env.getstate())
    while True:
        for i in range(K):
            actionplan = generateplan(stm, ltm )
            code = generatecode(actionplan,'',stm, ltm)
            output,stm,return_status = execcode(code,env,stm)
            while return_status != 0:
                code = generatecode(actionplan, utilities.CODEERRORPROMPT.format(str(code), output),stm, ltm)
                output,stm,return_status = execcode(code,env,stm)
            extfeedback = env.getfeedback()    
            feedback = critique(stm,actionplan,extfeedback)
            updatestatespace(stm)
        stm,ltm = ltmlearner(stm,ltm)
        
        
#solver(env)