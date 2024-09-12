#from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
#from neo.environment.envtemplate import *
import neo.components.programgraph as pg
from neo.config.utilities import *
import ast
import traceback
import uuid
import pickle
from itertools import chain
SOLVEDVALUE = 0.80
MAXERRORRETRYCOUNT = 2



def rootsolver(env,task = ""):
    env.environment["objective"] = {"task":task,"subtasks":[]}
    subtasks = subtaskbreaker(env,task)
    
    rootobjective = env.environment["objective"]
    print("Subtasks",subtasks)
    input()
    for subtask in subtasks:
        env.environment["objective"] = subtask#["desc"]
        solver(env)
    env.environment["objective"]["task"] = rootobjective["task"]
    env.environment["objective"]["subtasks"] =  []#[subtask["task"] for id,subtask in subtasks.items()]
    if len(subtasks) > 1:
       if solver(env,tries=3):
           print("END ROOTSOLVER")
           return

def interactwithuser(env,role="You are a arithmetic problem solver"):
    while True:
        inputtext = input("Enter your task: ")
        env.environment["prior axioms"] = role
        rootsolver(env,inputtext)

        

def solver(env,tries = 1000000):
    stm = env.STM
    ltm = env.LTM
    relevantextactions = ltm.get(query = env.environment["description"]+" "+env.environment["prior axioms"], memorytype ="externalactions", cutoffscore =0.2, top_k=5)
    relevantextactions = {i[1]["id"]: i[1]["data"] for i in relevantextactions}
    stm.set("relevantactions",relevantextactions)
    objsummary = summarize(". ".join(env.environment["objective"]["subtasks"])+" "+env.environment["objective"]["task"]+"\n"+env.environment["prior axioms" ])
    env.STM.set("summaryobjective",objsummary)
    for trie in range(tries):
        #actionplan,relevantnodeid,programdesc = generateplan(env )
        #relevantnodeid, programdesc = pg.getprogramto_extend(env,objective+"\n"+axioms)
        #env.STM.set("relevantprogramdesc", programdesc)
        #env.STM.set("relevantprogramdesc", programdesc)
        #relevantnodes = env.STM.set("relevantnodes", )
        # relevantnodes = pg.getrelevantnodes(env, env.environment["objective"] +"\n"+ env.environment["prior axioms" ])
        # if relevantnodes:
            # print("node val", env.graph["nodes"][relevantnodes[0][0]]["V"])
            # if env.graph["nodes"][relevantnodes[0][0]]["V"] > SOLVEDVALUE:
                # terminalnode = relevantnodes[0][0]
                # code = "terminalnode = "+str(terminalnode)
                # execcode(code,env,terminalnode)
                # print("SOLVED")
                # return 1
            # else:
                # output,terminalnode = generatecode(env)
        # else:
        output,terminalnode = generatecode(env)
        #output,stm,return_status = execcode(action["program"],action["desc"],env,relevantnodeid) 
        input("press a key to continue")             
        reward = critique(env,terminalnode)
        input("press a key to continue")
        output  = belieflearner(env)
        if reward > SOLVEDVALUE:
            print("SOLVED")
            return 1
        #env.reset()
    return 0
        


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

def flatten_list(list_of_lists):
    return list(chain.from_iterable(list_of_lists))
    
def subtaskbreaker(env,task):
    axioms = env.environment["prior axioms" ]   
    messages = SUBTASKPROMPT.format(axioms = axioms, task = task)
    output = llm_gpt4o.predict(messages)
    output = extractdictfromtext(output)
    subtasks = pickle.loads(pickle.dumps(output,-1))
    print("subtasks",subtasks)
    for id, subtask in output.items():
        subtasks[id] ={"task": subtask["task"], "subtasks": flatten_list([subtasks[i]["subtasks"] + [subtasks[i]["task"]] for i in subtask["dependencies"]])}
    subtasks = [ v for k,v in subtasks.items()]
    return subtasks


    
def generatecode(env, codeerror=""):
    objective = env.environment["objective"]  
    axioms = env.environment["prior axioms" ]   
    ################ fetch learnings #########################################
    query = "Objective: \n"+objective["task"]+"\n Critique recieved while solving the objective: \n"+ env.STM.get("critique")["reason"]
    memory = env.LTM.get(query, memorytype = "semantic", cutoffscore = 0.1 ,top_k=5)
    learnings = "\n".join([i[1]["data"] for i in memory])
    env.STM.set("relevantbeliefs", learnings)
    #axioms += "\n"+learnings
    
    relevantnodeid, programdesc,helpernodesdesc = pg.getprogramto_extend(env, env.STM.get("summaryobjective"), objective["subtasks"])#summarize(objective+"\n"+axioms))
    #relevantnodeid = env.STM.get("relevantnodes")[0][0]
    #programdesc = 
    if not relevantnodeid:
        relevantnodeid = env.initnode
        programdesc = "Initializes the program with initial node; node id -> 1"
    
    ######## fetch relevant actions
    relevantfunctions = env.STM.get("relevantactions") #env.LTM.get(objective+"\n"+axioms,"externalactions",top_k=5)
    relevantfunctionstext = "\n".join([k+" -> "+v for k,v in relevantfunctions.items()])
    relevantfunctionstext +=  "\n".join([k+" -> "+v for k,v in env.primitives.items()])                       
    
    retrycount = 0
    while True:
        input("press a key to continue... ")
        if retrycount > MAXERRORRETRYCOUNT:
            codeerror = ""
            retrycount = 0
        subtaskpromptprefix = "Following are the dependent subtasks already completed: \n"
        objectiveprefix = "Now complete the following objective:\n"
        messages = ACTORPROMPT.format(functions = relevantfunctionstext, \
                    axioms = axioms, \
                    learnings = learnings, \
                    programdescription = programdesc,\
                    helpernodes = helpernodesdesc, \
                    terminalnode = relevantnodeid, \
                    initialnode = env.initnode, \
                    #terminalnodedescription = env.graph["nodes"][relevantnodeid]["desc"], \
                    objective = objectiveprefix+objective["task"], \
                    subtasks = subtaskpromptprefix+'. '.join(objective["subtasks"]), \
                    error = codeerror)
        print("ACTORPROMPT:",messages)
        output = llm_gpt4o.predict(messages)
        
        print(output)
        try:
            codeerror = ""
            output = extractdictfromtext(output)
            print("ACTOR Code:","\n".join(output["program"]))
            ############ validate code #######################
            
            ############ excute code ###########
            input("press a key to continue... ")
            output,terminalnode,return_status = execcode("\n".join(output["program"]),env,relevantnodeid)
            if return_status != 0:
                codeerror = output
                print("CODERROR: ", codeerror)
                retrycount += 1
                continue
            break
        except Exception as e:
            print("Error : ",traceback.format_exc())
            #codeerror = str(e)
            pass
        
    #print("ACTORPROMPT output:",output)
    #print("ACTOR Code:","\n".join(output["program"]))
    return output, terminalnode


def execcode(code,env,relevantnodeid):
    output = None
    return_status = 0
    error = None
    print("exec code", code)
    #code += updatenodedescription(nodedesc)
    #try:
# Create an empty namespace (dictionary) for the exec function
    
    return_status,terminalnode,output = env.act(code,relevantnodeid)
   # except Exception as e:
   #     output = traceback.format_exc()
   #     print("Error output: ", output)
   #     return_status = 1
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
    currentenvironment_text = "objective: "+currentenvironment["objective"]["task"]+"   \n  "+"axioms: "+ currentenvironment["prior axioms"]+" \n "+env.STM.get("relevantbeliefs")
    progdesc,_ = pg.getprogramdesc(env.graph, terminalnode, programdesc = [],nodestraversed = [])
    progdesc = [desc for desc,idx in progdesc]
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
    
    if env.graph["nodes"][terminalnode]["R"] == 0.0000001:
        env.graph["nodes"][terminalnode]["R"] = output["feedback"] ## set the reward
    else:
        env.graph["nodes"][terminalnode]["R"] = env.graph["nodes"][terminalnode]["R"]*0.3+ output["feedback"]*0.7
    pg.updatevalue(env,terminalnode,True)
    
    return env.graph["nodes"][terminalnode]["R"]
    
    
def belieflearner(env):
    EnvTrace = env.STM.get("envtrace")
    EnvTrace_text = "\n".join([str(i) for i in EnvTrace])
    critique = env.STM.get("critique")["reason"]
    currentenvironment = env.environment
    currentenvironmenttext = "  objective:"+ currentenvironment['objective']["task"]+"\n prior axioms: \n  "+ str(currentenvironment["prior axioms"])
    ###################### fetch learnings ################
    memory = env.LTM.get(query = EnvTrace_text+'\n'+critique, memorytype = "semantic", cutoffscore = 0.4, top_k = 10)
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
        text = "objective: "+env.STM.get("summaryobjective")+"\n learning: "+learning
        env.LTM.set(text = text, data = learning, recordid=str(uuid.uuid4()), memorytype = "semantic")
    env.STM.set("envtrace",[]) ######## reset envtrace
    return output