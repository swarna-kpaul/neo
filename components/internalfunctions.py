from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.envtemplate import env
import neo.components.programgraph as pg
from neo.config.utilities import *
import ast
import traceback

def solver(env):
    stm = env.STM
    ltm = env.LTM
    relevantextactions = ltm.get(query = env.environment["description"]+" "+env.environment["prior axioms"], memorytype ="externalactions", top_k=5)
    relevantextactions = {i[1]["id"]: i[1]["data"] for i in relevantextactions}
    stm.set("relevantactions",relevantextactions)
    while True:
        for i in range(K):
            #actionplan,relevantnodeid,programdesc = generateplan(env )
            action,relevantnodeid = generatecode(env)
            output,stm,return_status = execcode(action["program"],action["desc"],env,relevantnodeid)
            while return_status != 0:
                action = generatecode(actionplan, relevantnodeid,programdesc,env, error = output)
                output,terminalnode,return_status = execcode(action["program"],action["desc"],env,relevantnodeid)
            extfeedback = env.getfeedback(terminalnode)    
            feedback = critique(stm,actionplan,extfeedback)
            #updateltmtrace(stm)
            #updatestatespace(stm, env.rootstate)
        #output,stm,ltm = belieflearner(stm,ltm)
        env.reset()
        


def generateplan(env, explore = False ):
    environment = env.environment
    
    relatedactionlist = env.STM.get("relevantactions")
    relatedactionlist = [ "moduleid : " +k+"; description : "+ v for k,v in relatedactionlist.items()]
    ######## fetch relevant node
    relevantnodeid, programdesc = pg.getprogramto_extend(env,environment["objective"]+environment["prior axioms"])
    ######## fetch envtrace
    if relevantnodeid:
        envtrace = pg.fetchenvtrace(env,relevantnodeid)
    else:
        envtrace = ""
        relevantnodeid = env.initnode
    #envtrace = env.STM.get("envtrace")
    #critique = env.STM.get("critique")
    #additionalinstructions,preactionppath = getinstructionfromSP(STM)#STM.get("additionalinstructions")
    beliefaxioms = "\n".join(env.STM.get("relevantbeliefs"))
    actionplanexamples = environment["examples"]
    #if  item == "explore":
    #    currentenvironment["objective"] = currentenvironment["exploreobjective"]
        #self.env.totalexplore += 1
    environmenttext = "    objective: \n" + environment["objective"] +"\n\n"+" prior axioms: \n"+environment["prior axioms"]+"\n\n"+ "     belief axioms:\n"+beliefaxioms+"\n\n"
    if envtrace:
       envtrace_text = "\n".join(["action: "+i["action"]+"; observation: "+i["observation"] for i in envtrace])
    else:
       envtrace_text = ""
    errorfeedback = ""#self.stm.get("errorfeedback")
    trial = 0
    while True:
    ###### try until correct plan is generated
        if errorfeedback != "":
            errorfeedbacktext = "Here are some action plans with feedback. Make sure to generate a valid new action plan. \n "+errorfeedback
        else:
            errorfeedbacktext = ""
        messages = ACTPLANPROMPT.format(beliefenvironment = environmenttext, \
                    programdescription = programdesc, \
                    envtrace = envtrace_text, \
                    relatedactions = '\n'.join(relatedactionlist), \
                    actionplanexamples = actionplanexamples,\
                    userpromptprefix = useractionplanmeetobjective, \
                    errorfeedback = errorfeedback)
        print("ACTPLANPROMPT:",messages)
        output = llm_gpt4o.predict(messages)
        
        print("ACTPLANPROMPT output:",output)
        try:
            output = ast.literal_eval(output)
        except Exception  as e:
            #errorfeedback = "Here is the last actionplan generated. "+ output+ "\n But this action plan has the following error. Modify the plan to remove the error.\n"+str(e)
            print(traceback.format_exc())
            input("Press any key to continue...")
            continue
        
        input("Press any key to continue...")

        break

    return output,relevantnodeid,programdesc
    
    
def generatecode(env, codeerror=""):

   
    axioms = env.environment["prior axioms" ]+"\n"+env.environment["belief axioms"]
    objective = env.environment["objective"]    
    
    ######## fetch relevant node
    relevantnodeid, programdesc = pg.getprogramto_extend(env,objective+"\n"+axioms)
    ######## fetch envtrace
    if not relevantnodeid:
        relevantnodeid = env.initnode
        programdesc = "Initializes the program with initial node"
    #actionplantext = "\n".join(actionplan["actionplan"]) if isinstance(actionplan["actionplan"], list) else str(actionplan["actionplan"])
    relevantfunctions = env.LTM.get(objective+"\n"+axioms,"externalactions",top_k=5)
    relevantfunctionstext = "\n".join([i[1]["id"]+"->"+i[1]["data"] for i in relevantfunctions])
    relevantfunctionstext +=  "\n".join([k+" -> "+v for k,v in env.primitives.items()])                       
     #["objective"]
    
    #ACPtrace = STM.get("ACPtrace")
    #prevactionplan = ACPtrace[-1]["actionplan"]["actionplan"] if ACPtrace else ""
    
    while True:
        messages = ACTORPROMPT.format(functions = relevantfunctionstext, \
                    axioms = axioms, \
                    programdescription = programdesc,\
                    terminalnode = relevantnodeid, \
                    initialnode = env.initnode, \
                    terminalnodedescription = env.graph["nodes"][relevantnodeid]["desc"], \
                    objective = objective, \
                    error = codeerror)
        print("ACTORPROMPT:",messages)
        output = llm_gpt4o.predict(messages)
        
        print(output)
        try:
            output = extractdictfromtext(output)
            break
        except Exception as e:
            print("Error ACTORPROMPT output:",output)
            codeerror = str(e)
            pass
        
    print("ACTORPROMPT output:",output)
    print("ACTOR Code:",output["program"])
    return output, relevantnodeid


def execcode(code,nodedesc,env,relevantnodeid):
    output = None
    return_status = None
    error = None
    print("exec code", code)
    code += updatenodedescription(nodedesc)
    try:
# Create an empty namespace (dictionary) for the exec function
        terminalnode = env.act(code,relevantnodeid)
        pg.updateproceduremem(env,terminalnode)
        pg.updatevalue(env,terminalnode)
    except world_exception as e:
        return_status = 0
    except Exception as e:
        output = traceback.format_exc()
        return_status = 1
    
    print ("ACTION EXECUTION OUTPUT", output,return_status)    
    return (output,terminalnode,return_status)
 
def updatenodedescription(progdesc): 
    codetext = ""
    for nodeid,desc in progdesc.items():
        codetext +="\n"+"pg.setval_graph('desc','"+desc+"',graph,"+nodeid+",'N')"
    return codetext

    
def critique (env,currentactionplan,currentperception):
    currentenvironment = env.environment
    messages = CRITIQUEPROMPT.format(beliefenvironment = str(currentenvironment), \
                    actionplan = currentactionplan, \
                    perception = currentperception)
    print("CRITIQUEPROMPT:",messages)
    output = llm_gpt4o.predict(messages)
    print("CRITIQUEPROMPT output:",output)
    output = ast.literal_eval(output)
    
    env.STM.set("critique", output)
    return output
    
    
def belieflearner(env):
    EnvTrace = env.STM.get("ltmenvtrace")
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
    messages = LEARNERPROMPT.format(relatedenvironments = str(relatedenvironments),
                    beliefenvironment = str(currentbelief),
                    EnvTrace = EnvTrace_text)
        #print(messages)
    print("LEARNERPROMPT:",messages)
    output = llm_gpt4o.predict(messages)
    print("LEARNERPROMPT output:",output)
    beliefaxioms = ast.literal_eval(output)["beliefaxioms"]
    currentenvironment["env"]["belief axioms"] = beliefaxioms
    env.STM.set("currentenv",{'id': currentenvironment['id'], 'env':currentenvironment["env"]})
    currentenvironment["env"]['type'] = "environments"
    ltmdata = [{'id': currentenvironment['id'], 'values': currentenvironment["env"]['description'], 'metadata': currentenvironment["env"] }]
    #self.ltm.set(data = ltmdata, namespace = "environments")
    env.STM.set("ltmenvtrace",[])
    return output,STM,LTM