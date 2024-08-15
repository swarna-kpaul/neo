#from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from neo.environment.envtemplate import *
import neo.components.programgraph as pg
from neo.config.utilities import *
import ast
import traceback

def solver(env):
    stm = env.STM
    ltm = env.LTM
    relevantextactions = ltm.get(query = env.environment["description"]+" "+env.environment["prior axioms"], memorytype ="externalactions", cutoffscore =0.2, top_k=5)
    relevantextactions = {i[1]["id"]: i[1]["data"] for i in relevantextactions}
    stm.set("relevantactions",relevantextactions)
    while True:
        #actionplan,relevantnodeid,programdesc = generateplan(env )
        relevantnodes = env.STM.get("relevantnodes")
        if relevantnodes:
            if relevantnodes[0][1] > SOLVEDVALUE:
                terminalnode = relevantnodes[0][0]
                code = "terminalnode = "+str(terminalnode)
                execcode(code,env,terminalnode)
            else:
                action,terminalnode = generatecode(env)
        else:
            action,terminalnode = generatecode(env)
        #output,stm,return_status = execcode(action["program"],action["desc"],env,relevantnodeid) 
        input("press a key to continue")             
        feedback = critique(env,terminalnode)
        input("press a key to continue")
        output  = belieflearner(env)
        #env.reset()
        


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
    query = "Objective: \n"+environment["objective"]+"\n Partial plan to meet the objective: \n"+ programdesc
    memory = env.LTM.get(query, memorytype = "semantic", cutoffscore = 0.2 ,top_k=5)
    
    beliefaxioms = "\n".join([i[1]["data"] for i in memory])
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
    objective = env.environment["objective"]  
    axioms = env.environment["prior axioms" ]    
    relevantnodeid, programdesc = pg.getprogramto_extend(env,objective+"\n"+axioms)
    if not relevantnodeid:
        relevantnodeid = env.initnode
        programdesc = "Initializes the program with initial node"
    
    ################ fetch learnings #########################################
    query = "Objective: \n"+objective+"\n Partial plan to meet the objective: \n"+ programdesc
    memory = env.LTM.get(query, memorytype = "semantic", cutoffscore = 0.2 ,top_k=5)
    learnings = "\n".join([i[1]["data"] for i in memory])
    env.STM.set("relevantbeliefs", learnings)
    axioms += "\n"+learnings
    ######## fetch relevant actions
    relevantfunctions = env.STM.get("relevantactions") #env.LTM.get(objective+"\n"+axioms,"externalactions",top_k=5)
    relevantfunctionstext = "\n".join([k+" -> "+v for k,v in relevantfunctions.items()])
    relevantfunctionstext +=  "\n".join([k+" -> "+v for k,v in env.primitives.items()])                       
    
    while True:
        input("press a key to continue... ")
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
            
            ############ validate code #######################
            
            ############ excute code ###########
            input("press a key to continue... ")
            output,terminalnode,return_status = execcode("\n".join(output["program"]),env,relevantnodeid)
            if return_status != 0:
                codeerror = output
                print("CODERROR: ", codeerror)
                continue
            break
        except Exception as e:
            print("Error ACTORPROMPT output:",output)
            codeerror = str(e)
            pass
        
    print("ACTORPROMPT output:",output)
    print("ACTOR Code:","\n".join(output["program"]))
    return "\n".join(output["program"]), relevantnodeid


def execcode(code,env,relevantnodeid):
    output = None
    return_status = 0
    error = None
    print("exec code", code)
    #code += updatenodedescription(nodedesc)
    try:
# Create an empty namespace (dictionary) for the exec function
        env.STM.set("envtrace",[]) ######## reset envtrace
        return_status,terminalnode,output = env.act(code,relevantnodeid)
    except Exception as e:
        output = traceback.format_exc()
        return_status = 1
    if  return_status != 1:
        pg.updateproceduremem(env,terminalnode)
        envtrace,_ = pg.fetchenvtrace(env,terminalnode,[],[])
        env.STM.set("envtrace",envtrace)
        print ("ACTION EXECUTION OUTPUT", output,return_status)    
    return (output,terminalnode,return_status)
 
###################### update failure status

###############################################
    
def critique (env,terminalnode):
    currentenvironment = env.environment
    currentenvironment_text = "objective: "+currentenvironment["objective"]+"   \n  "+"axioms: "+ currentenvironment["prior axioms"]+" \n "+env.STM.get("relevantbeliefs")
    progdesc,_ = pg.getprogramdesc(env.graph, terminalnode, programdesc = [],nodestraversed = [])
    
    currentperception = "\n".join([str(i) for i in env.STM.get("envtrace")])
    
    messages = CRITIQUEPROMPT.format(beliefenvironment = str(currentenvironment_text), \
                    actionplan = "\n".join(progdesc), \
                    perception = currentperception)
    print("CRITIQUEPROMPT:",messages)
    output = llm_gpt4o.predict(messages)
    print("CRITIQUEPROMPT output:",output)
    #output = ast.literal_eval(output)
    output = extractdictfromtext(output)
    
    env.STM.set("critique", output)
    
    env.graph["nodes"][terminalnode]["R"] = output["feedback"] ## set the reward
    pg.updatevalue(env,terminalnode)
    
    return output
    
    
def belieflearner(env):
    EnvTrace = env.STM.get("envtrace")
    EnvTrace_text = "\n".join([str(i) for i in EnvTrace])
    critique = env.STM.get("critique")["reason"]
    currentenvironment = env.environment
    currentenvironmenttext = "  objective:"+ currentenvironment['objective']+"\n prior axioms: \n  "+ str(currentenvironment["prior axioms"])
    ###################### fetch learnings ################
    memory = env.LTM.get(query = EnvTrace_text, memorytype = "semantic", cutoffscore = 0.4, top_k = 10)
    learningstext = "\n".join([ i[1]["data"] for i in memory])
    memoryid = [ i[1]["id"] for i in memory]
    ###################### delete memory to be updated
    for id in memoryid:
        env.LTM.delete(id,"semantic")
    ######################################################################   
    messages = LEARNERPROMPT.format(environment = currentenvironmenttext,
                    learnings = learningstext,
                    EnvTrace = EnvTrace_text,
                    critique = critique)
        #print(messages)
    print("LEARNERPROMPT:",messages)
    output = llm_gpt4o.predict(messages)
    print("LEARNERPROMPT output:",output)
    output = extractdictfromtext(output)
    learnings = output["learnings"]
    #currentenvironment["env"]["belief axioms"] = beliefaxioms
    for learning in learnings:
        env.LTM.set(text = learning, data = learning, memorytype = "semantic")

    return output