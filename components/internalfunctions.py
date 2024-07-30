from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.envtemplate import env


def solver(env):
    stm = env.stm
    ltm = env.ltm
    while True:
        for i in range(K):
            actionplan = generateplan(env )
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
        


def generateplan(env, explore = False ):
    environment = env.environment
    envtrace = env.STM.get("envtrace")
    critique = env.STM.get("critique")
    additionalinstructions,preactionppath = getinstructionfromSP(STM)#STM.get("additionalinstructions")
    beliefaxioms = env.STM.get("relevantbeliefs")
    actionplanexamples = environment["examples"]
    #if  item == "explore":
    #    currentenvironment["objective"] = currentenvironment["exploreobjective"]
        #self.env.totalexplore += 1
    environmenttext = "    objective: \n" + environment["objective"] +"\n\n"+" prior axioms: \n"+environment["prior axioms"]+"\n\n"+ "     belief axioms:\n"+beliefaxioms+"\n\n"+"    current state:\n"+ env.STM.get("state")
    if envtrace:
       envtrace_text = "\n".join(["action: "+i["action"]+"; observation: "+i["observation"] for i in envtrace])
    else:
       envtrace_text = ""
    if additionalinstructions :
        environmenttext += "\n\n"+additionalinstructions
    errorfeedback = ""#self.stm.get("errorfeedback")
    trial = 0
    while True:
    ###### try until correct plan is generated
        if errorfeedback != "":
            errorfeedbacktext = "Here are some action plans with feedback. Make sure to generate a valid new action plan. \n "+errorfeedback
        else:
            errorfeedbacktext = ""
        messages = utilities.ACTPLANPROMPT.format(beliefenvironment = environmenttext, \
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

        break

    return output
    
    
def generatecode(actionplan, codeerror="", env):
                 
    actionplantext = "\n".join(actionplan["actionplan"]) if isinstance(actionplan["actionplan"], list) else str(actionplan["actionplan"])
    relevantactions = env.STM.get("relevantactions")
    relevantactionstext = ""
    for action,actiontext in relevantactions.items():
        relatedactiontext += "    "+action+ " -> "+ actiontext +"\n" 
                            
    objective = env.environment["objective"] #["objective"]
    #ACPtrace = STM.get("ACPtrace")
    #prevactionplan = ACPtrace[-1]["actionplan"]["actionplan"] if ACPtrace else ""
    messages = utilities.ACTORPROMPT.format(beliefenvironment = objective, \
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
    print("ACTOR Code:",output["fullactioncode"])
    return output 


def execcode(code,env):
    output = None
    return_status = None
    error = None
    print("exec code", code)
    try:
# Create an empty namespace (dictionary) for the exec function
        for codeline in code:
            env.act(codeline)
    except world_exception as e:
        return_status = 0
    except Exception as e:
        output = traceback.format_exc()
        return_status = 1
    print ("ACTION EXECUTION OUTPUT", output,return_status)    
    return (output,stm,return_status)
    
    
def critique (env,currentactionplan,currentperception):
    currentenvironment = env.environment
    messages = utilities.CRITIQUEPROMPT.format(beliefenvironment = str(currentenvironment), \
                    actionplan = currentactionplan, \
                    perception = currentperception)
    print("CRITIQUEPROMPT:",messages)
    output = utilities.llm_model.predict(messages)
    print("CRITIQUEPROMPT output:",output)
    output = ast.literal_eval(output)
    
    env.STM.set("critique", output)
    return output,STM
    
    
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
    messages = utilities.LEARNERPROMPT.format(relatedenvironments = str(relatedenvironments),
                    beliefenvironment = str(currentbelief),
                    EnvTrace = EnvTrace_text)
        #print(messages)
    print("LEARNERPROMPT:",messages)
    output = utilities.llm_gpt4_turbo.predict(messages)
    print("LEARNERPROMPT output:",output)
    beliefaxioms = ast.literal_eval(output)["beliefaxioms"]
    currentenvironment["env"]["belief axioms"] = beliefaxioms
    env.STM.set("currentenv",{'id': currentenvironment['id'], 'env':currentenvironment["env"]})
    currentenvironment["env"]['type'] = "environments"
    ltmdata = [{'id': currentenvironment['id'], 'values': currentenvironment["env"]['description'], 'metadata': currentenvironment["env"] }]
    #self.ltm.set(data = ltmdata, namespace = "environments")
    env.STM.set("ltmenvtrace",[])
    return output,STM,LTM