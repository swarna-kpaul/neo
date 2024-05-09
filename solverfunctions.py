from config.configurations import *
from config.prompts import *
from langchain.prompts.prompt import PromptTemplate
from config import utilities
import traceback
from environment.problemenvs import *
from models.buildstatespacemodel import *
import random
import string
K=1

CONTEXTCODE = "import environment.context as context"
import ast
import pickle

gamma = 0.8
CUMULATIVEREWARDTHRESHOLD = 5
EPISODELEN = 0
MAXPLANCRITUQUETRIAL = 5
MAXRELATEDACTIONSET =3


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
            action = generatecode(actionplan,'',stm, ltm)
            output,stm,return_status = execcode(action["fullactioncode"],env,stm)
            while return_status != 0:
                action = generatecode(actionplan, utilities.CODEERRORPROMPT.format(code = str(action["fullactioncode"]), error = output),stm, ltm)
                output,stm,return_status = execcode(action["fullactioncode"],env,stm)
            extfeedback = env.getfeedback()    
            feedback,stm = critique(stm,actionplan,extfeedback)
            updateltmtrace(stm)
            updatestatespace(stm, env.rootstate)
        output,stm,ltm = belieflearner(stm,ltm)
        env.reset()

def execcode(code,env,stm):
    output = None
    return_status = None
    error = None
    print("exec code", code)
    try:
# Create an empty namespace (dictionary) for the exec function
        exec_namespace = {"env": env,"stm":stm}
        #print("Executing Code: ", code)
        exec(str(code),exec_namespace)
        output = exec_namespace.get("result", None)
        stm = exec_namespace.get("stm", None)        
        return_status = 0
    except world_exception as e:
        return_status = 0
    except Exception as e:
        output = traceback.format_exc()
        return_status = 1
    print ("ACTION EXECUTION OUTPUT", output,return_status)    
    return (output,stm,return_status)


def updateltmtrace(stm):
    envtrace = stm.get("envtrace")
    ltmenvtrace = stm.get("ltmenvtrace")
    ltmenvtrace += envtrace
    stm.set("ltmenvtrace", ltmenvtrace)

def updatestatespace(stm,isrootstate):
    spmodel = stm.get("SPmodel")
    spmodel.rootstate = isrootstate
    print("envtrace",stm.get("envtrace"))
    spmodel.parseacpt_trace(stm.get("envtrace"),stm.get("currentstate"))
    spmodel.updatevalue()
    stm.set("envtrace",[])
    

def getinstructionfromSP(stm):
    spmodel = stm.get("SPmodel")
    prompt,actionpath,avoidactions,explore,ucbfactor = spmodel.getplandetails(stm.get("currentstate"))
    return (prompt,actionpath)


def generateplan(STM, LTM, explore = False ):
    currentenvironment = STM.get("currentenv")['env']
    envtrace = STM.get("envtrace")
    critique = STM.get("critique")
    additionalinstructions,preactionppath = getinstructionfromSP(STM)#STM.get("additionalinstructions")
    beliefaxioms = "\n".join(currentenvironment["belief axioms"])
    actionplanexamples = currentenvironment["examples"]
    #if  item == "explore":
    #    currentenvironment["objective"] = currentenvironment["exploreobjective"]
        #self.env.totalexplore += 1
    if envtrace:
       envtrace_text = "\n".join(["action: "+i["action"]+"; observation: "+i["observation"] for i in envtrace])
    else:
       envtrace_text = ""
    if additionalinstructions :
        currentenvironmenttext = "    objective: \n" + currentenvironment["objective"] +"\n\n"+" prior axioms: \n"+currentenvironment["prior axioms"]+"\n\n"+ "     belief axioms:\n"+beliefaxioms+"\n\n"+"    current state:\n"+ currentenvironment["current state"]+"\n\n"+additionalinstructions
    else:
        currentenvironmenttext = "    objective: \n" + currentenvironment["objective"] +"\n\n"+" prior axioms: \n"+currentenvironment["prior axioms"]+"\n\n"+ "     belief axioms:\n"+beliefaxioms+"\n\n"
       
    relatedactionset = LTM.get(currentenvironment["description"]+currentenvironment["objective"]+currentenvironment["prior axioms"], namespace = "actions",k = MAXRELATEDACTIONSET)
    relatedactionlist = []
    for action in relatedactionset:
        actiondict = { "moduleid" : action["id"],
                        "description": action["metadata"]["description"],
                        "name": action["metadata"]["name"],
                        "input parameter" : action["metadata"]["input parameter"],
                        "output" : action["metadata"]["output"]
                     }
        relatedactionlist.append(str(actiondict))
    errorfeedback = ""#self.stm.get("errorfeedback")
    trial = 0
    while True:
    ###### try until correct plan is generated
        if errorfeedback != "":
            errorfeedbacktext = "Here are some action plans with feedback. Make sure to generate a valid new action plan. \n "+errorfeedback
        else:
            errorfeedbacktext = ""
        messages = utilities.ACTPLANPROMPT.format(beliefenvironment = currentenvironmenttext, \
                    envtrace = envtrace_text, \
                    relatedactions = '\n'.join(relatedactionlist), \
                    actionplanexamples = actionplanexamples,\
                    userpromptprefix = useractionplanmeetobjective, \
                    errorfeedback = errorfeedback)
        print("ACTPLANPROMPT:",messages)
        output = utilities.llm_gpt4_turbo.predict(messages)
        
        print("ACTPLANPROMPT output:",output)
        try:
            output = ast.literal_eval(output)
        except Exception  as e:
            #errorfeedback = "Here is the last actionplan generated. "+ output+ "\n But this action plan has the following error. Modify the plan to remove the error.\n"+str(e)
            print(traceback.format_exc())
            input("Press any key to continue...")
            continue
        
        input("Press any key to continue...")
        ########## check if related actions contain valid module ids 
        moduleids = [action["id"] for action in relatedactionset]
        isvalidids = set([True if id in moduleids else False for id in output["requiredactions"]])
        if False in isvalidids:
            errorfeedback += "\nAction plan: "+ str(output)+ "\n Feedback: the requirements have invalid moduleids. Modify the actionplan to put correct moduleids from stored function modules"
            continue      
        ############ check if actionplan satisfies all constraints
        #isvalid,reason = self.actplancritique(str(output))            
        #if not isvalid and trial < MAXPLANCRITUQUETRIAL:
        #    errorfeedback += "\nAction plan: "+ str(output)+ "\n Feedback: But it might be invalid due to "+reason
        #    trial += 1
        #    continue
        break
    if preactionppath:
        output["actionplan"] = preactionppath + ".\n"+output["actionplan"]
    #self.stm.set(errorfeedback,"errorfeedback")
    return output
    


def generatecode(actionplan, codeerror="", STM, LTM):
    relatedactionsets = {}
    actionids = list(set(actionplan["requiredactions"]))
    actionset = LTM.fetch(actionids, namespace = "actions")
    
    for actionid in actionids:
        relatedactionsets[actionid] = actionset[actionid]["metadata"]
                
    actionplantext = "\n".join(actionplan["actionplan"]) if isinstance(actionplan["actionplan"], list) else str(actionplan["actionplan"])
    #actionset = self.ltm.get(actionplantext, namespace = "actions",k = 1)
    #if actionset:
    #    for action in actionset:
    #        actionid = action["id"]
    #        relatedactionsets[actionid] = action["metadata"]
    #relatedactionsets = [i["metadata"] for i in relatedactionsets]
    relatedactiontext = ""
    for id,relatedaction in relatedactionsets.items():
        relatedactiontext += "    Action description: "+ relatedaction["description"] +"\n" \
                             "    Input parameter: "+ relatedaction["input parameter"] +"\n" \
                             "    Output: "+ relatedaction["output"] +"\n" \
                             "    Requirements: "+ relatedaction["requirements"] +"\n" \
                             "    Code: "+ relatedaction["code"]+"\n\n"
    #relatedactiontext = "\n   ".join(relatedactionsets)
    #objective = self.env.actorobjective
    beliefenvironment = STM.get("currentenv")['env'] #["objective"]
    #ACPtrace = STM.get("ACPtrace")
    #prevactionplan = ACPtrace[-1]["actionplan"]["actionplan"] if ACPtrace else ""
    messages = utilities.ACTORPROMPT.format(beliefenvironment = beliefenvironment, \
                    actions = relatedactiontext, \
                    actionplan = actionplantext, \
                    error = codeerror)
    print("ACTORPROMPT:",messages)
    while True:
        output = utilities.llm_model.predict(messages)
        try:
            output = ast.literal_eval(output)
            break
        except:
            print("Error ACTORPROMPT output:",output)
            pass
        
    print("ACTORPROMPT output:",output)
    output["requirements"] = '\n\n'.join([relatedaction["requirements"]+"\n\n"+relatedaction["code"] for id,relatedaction in relatedactionsets.items()]) 
    if output['functioncall'] != "":
        output["fullactioncode"] = output['requirements']+"\n\n"+output['code'] + "\n\nresult="+output['functioncall']
    else:
        output["fullactioncode"] = output['requirements']+"\n\n"+output['code']
    print("ACTOR Code:",output["fullactioncode"])
    return output
    
def critique (STM,currentactionplan,currentperception):
    currentenvironment = STM.get("currentenv")['env']
    #envobjective = currentenvironment["objective"]
    #beliefaxioms = currentenvironment["beliefaxioms"]
    #critique = self.stm.get("critique")
    #ACPtrace = self.stm.get("ACPtrace")
    #actionplan = ACPtrace[-1]["actionplan"]["actionplan"]
    #perception = ACPtrace[-1]["perception"]
    messages = utilities.CRITIQUEPROMPT.format(beliefenvironment = str(currentenvironment), \
                    actionplan = currentactionplan, \
                    perception = currentperception)
    print("CRITIQUEPROMPT:",messages)
    output = utilities.llm_model.predict(messages)
    print("CRITIQUEPROMPT output:",output)
    output = ast.literal_eval(output)
    
    STM.set("critique", output)
    return output,STM


######################### long term learner functions ############################
def storeactionasskill(self,action,overwrite=False):
    actionset = self.ltm.get(action["description"], namespace = "actions", k = 1)
    actionid = actionset[0]["id"] if actionset else '0'
    score = actionset[0]["score"] if actionset else 0
    actionset = actionset[0]["metadata"] if actionset else actionset
    if actionset["actiontype"] == "fixed":
        overwrite = False
    newflag = False
    if score > 0.95: ### the descriptions are almost same thus the purpose might be almost same
        id = actionid
    elif actionset:
        messages = self.CODEEQUIVALENCEPROMPT.format(code1 = action["code"], code2 = actionset["code"])
        print("CODEEQUIVALENCEPROMPT:",messages)
        output = llm_defn_model.predict(messages)
        print("CODEEQUIVALENCEPROMPT output:",output)
        if output == "True":
        ######### update old code
            id = actionid
            #return 
        else:
            id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            newflag = True
    else:
        id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        newflag = True
    action['type'] = "actions"
    ltmdata = [{'id': str(id), 'values': action['description'], 'metadata': action }]
    if overwrite or newflag:
        self.ltm.set(data = ltmdata, namespace = "actions")
        
def belieflearner(STM,LTM):
    EnvTrace = STM.get("ltmenvtrace")
    #critique = self.stm.get("critique")
    currentenvironment = STM.get("currentenv")
    currentbelief = "  objective:"+ currentenvironment['env']['objective']+"\n  belief axioms:"+ str(currentenvironment['env']["belief axioms"])
    #ACPtrace_text = "\n".join([ "    Action plan: "+ i["actionplan"]["actionplan"]+"\n    Environment response: "+ i["perception"] for i in ACPtrace])
    EnvTrace_text = "\n".join([str(i) for i in EnvTrace])
    relatedenvironments = LTM.get(str(currentenvironment['env']), namespace = "environments")
    if relatedenvironments:
        relatedenvironments = [ "    Environment "+str(i)+":\n    objective: "+str(env["metadata"]["objective"])+"\n   belief axioms:"+ str(env["metadata"]["belief axioms"]) for i,env in enumerate(relatedenvironments) if env["id"] != currentenvironment['id'] ] 
        relatedenvironments = ["\n".join(relatedenvironments)]
    else:
        relatedenvironments = ""
    messages = utilities.LEARNERPROMPT.format(relatedenvironments = str(relatedenvironments),
                    beliefenvironment = str(currentbelief),
                    EnvTrace = EnvTrace_text)
        #print(messages)
    print("LEARNERPROMPT:",messages)
    output = utilities.llm_gpt4_turbo.predict(messages)
    print("LEARNERPROMPT output:",output)
    beliefaxioms = ast.literal_eval(output)["beliefaxioms"]
    currentenvironment["env"]["belief axioms"] = beliefaxioms
    STM.set("currentenv",{'id': currentenvironment['id'], 'env':currentenvironment["env"]})
    currentenvironment["env"]['type'] = "environments"
    ltmdata = [{'id': currentenvironment['id'], 'values': currentenvironment["env"]['description'], 'metadata': currentenvironment["env"] }]
    #self.ltm.set(data = ltmdata, namespace = "environments")
    STM.set("ltmenvtrace",[])
    return output,STM,LTM
