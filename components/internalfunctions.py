import neo.components.programgraph as pg
from neo.config.utilities import *
import ast
import traceback
import uuid
import pickle
from itertools import chain
SOLVEDVALUE = 0.80
MAXERRORRETRYCOUNT = 2



def rootsolver(env,task = "",storeenvfile=None,loadenvfile= None):
    if loadenvfile != None:
        with open(loadenvfile,'rb') as file:
            env = pickle.load(file)
            pg.current_node_label_obj.set_node_label(max(list(env.graph["nodes"].keys()))+1)
            for terminalnode in list(env.graph["terminalnodes"].keys()):
                pg.resetdata(env.graph,terminalnode)
    env.environment["objective"] = {"task":task,"subtasks":[]}
    ######
    
    if env.inprogresssubtasks: ### solving subtasks in progress
        subtasks = pickle.loads(pickle.dumps(env.inprogresssubtasks,-1))
    else:
        ############# check for solved tasks 
        objsummary = summarize(". ".join(env.environment["objective"]["subtasks"])+" "+env.environment["objective"]["task"]+"\n"+env.environment["prior axioms" ])
        terminalnode = getsolvedtasks(env,objsummary)
        if terminalnode:
            return terminalnode
        subtasks = subtaskbreaker(env,task)
        env.inprogresssubtasks = pickle.loads(pickle.dumps(subtasks,-1))
        
    rootobjective = env.environment["objective"]
    for subtask in subtasks:
        x = env.inprogresssubtasks.pop(0)
        env.environment["objective"] = subtask#["desc"]
        env.STM.set("resetdataflag",False)
        terminalnode = solver(env,storeenvfile)
        if storeenvfile != None:
            with open(storeenvfile,"wb") as file:
                pickle.dump(env, file)
    objsummary = summarize(rootobjective["task"] +"\n" +env.environment["prior axioms"])
    env.LTM.set(text = objsummary, data = {"task": objsummary, "terminalnode": terminalnode}, recordid=str(uuid.uuid4()), memorytype = "solvedtasks")
    env.environment["objective"]["task"] = rootobjective["task"]
    env.environment["objective"]["subtasks"] =  []#[subtask["task"] for id,subtask in subtasks.items()]
    if len(subtasks) > 1:
       print("Finally solving root task:",rootobjective["task"])
       env.STM.set("resetdataflag",True)
       terminalnode = solver(env,storeenvfile,tries=3)
       if terminalnode:
           print("END ROOTSOLVER")
           if storeenvfile != None:
               with open(storeenvfile,"wb") as file:
                   pickle.dump(env, file)
           return terminalnode

def interactwithuser(env,role="You are a arithmetic problem solver"):
    while True:
        inputtext = input("Enter your task: ")
        env.environment["prior axioms"] = role
        rootsolver(env,inputtext)


def getsolvedtasks(env,objsummary):
    #objsummary = env.STM.get("summaryobjective")
    memory = env.LTM.get(objsummary, memorytype = "solvedtasks", cutoffscore = 0.7 ,top_k=1)
    if memory:
        ########## check for exact similarity
        obj2 = memory[0][1]["data"]["task"]
        existingrecordid = memory[0][1]["id"]
        systemmessage = textsimilaritysystemtemplate
        usermessage = textsimilarityusertemplate.format(text1 = objsummary, text2 = obj2)
        while True:
            try:
                output = chatpredict(systemmessage,usermessage)
                output = extractdictfromtext(output)
                break
            except Exception as e:
                print("Error : ",traceback.format_exc())
            #codeerror = str(e)
                pass
        if output["result"]: 
        ############ objectives are same
            terminalnode = memory[0][1]["data"]["terminalnode"]
            code = "solved = True"
            print("Similar task fetched from list of already solved tasks...")
           
            output,terminalnode,return_status = execcode(code,env,terminalnode)
            if return_status == 0:
                reward = critique(env,terminalnode)
                if reward > SOLVEDVALUE:
                    if memory[0][0] < 0.8:
                    ######### for low similarity create new solved task
                        env.LTM.set(text = objsummary, data = {"task": objsummary, "terminalnode": terminalnode}, recordid=str(uuid.uuid4()), memorytype = "solvedtasks")                
                    print("Task "+env.environment["objective"]["task"]+" SOLVED")
                    return terminalnode
                else:
                    ############################ udate summary as it was unable to solve this task
                    systemmessage = updatesolvedtaskdescriptiontemplate.format(description = obj2, \
                                      feedback = env.STM.get("critique")["reason"] 
                                    )
                    usermessage ="AI:"
                    print("ACTORPROMPT system:",systemmessage)
                    print("ACTORPROMPT user:",usermessage)
                    output = chatpredict(systemmessage,usermessage)
                    env.LTM.set(text = output, data = {"task": output, "terminalnode": terminalnode}, recordid=existingrecordid, memorytype = "solvedtasks")
    return False

        

def solver(env,storeenvfile=None,tries = 1000000):
    stm = env.STM
    ltm = env.LTM
    env.STM.set("critique", {"feedback":0,"reason":""})
    objsummary = summarize(". ".join(env.environment["objective"]["subtasks"])+" "+env.environment["objective"]["task"]+"\n"+env.environment["prior axioms" ])
    env.STM.set("summaryobjective",objsummary)
    ### get solved tasks
    terminalnode = getsolvedtasks(env,objsummary)
    if terminalnode:
        return terminalnode
    ############ Task not  solved            
    
    for trie in range(tries):
        print("Solving task:",env.environment["objective"]["task"])
        output,terminalnode = generatecode(env)          
        reward = critique(env,terminalnode)
        input("press a key to continue")
        output  = belieflearner(env)
        if storeenvfile != None:
            with open(storeenvfile,"wb") as file:
                pickle.dump(env, file)
        if reward > SOLVEDVALUE:
            print("Task "+env.environment["objective"]["task"]+" SOLVED")
            ##### add to solved task
            data = {"task": objsummary, "terminalnode": terminalnode}
            env.LTM.set(text = objsummary, data = data, recordid=str(uuid.uuid4()), memorytype = "solvedtasks")
            return terminalnode
        #env.reset()
    return 0
        


def flatten_list(list_of_lists):
    return list(chain.from_iterable(list_of_lists))
    
def subtaskbreaker(env,task):
    feedback = ""
    print("Breaking into Subtasks..")
    relevantextactions = env.LTM.get(query = task+"\n", memorytype ="externalactions", cutoffscore =0.1, top_k=7)
    relevantextactions = {i[1]["id"]: i[1]["data"] for i in relevantextactions}
    while True:
        axioms = env.environment["prior axioms" ]   
        systemmessage = subtasksystemtemplate.format(axioms = axioms, functions = str(relevantextactions))
        usermessage = subtaskusertemplate.format(task = task+"\n"+feedback)
        output = chatpredict(systemmessage,usermessage)
        output = extractdictfromtext(output)
        subtasks = pickle.loads(pickle.dumps(output,-1))
        for id, subtask in output.items():
            subtasks[id] ={"task": subtask["task"], "subtasks": flatten_list([subtasks[i]["subtasks"] + [subtasks[i]["task"]] for i in subtask["dependencies"]])}
        subtasks = [ v for k,v in subtasks.items()]
        
        print("subtasks: \n","\n".join([subtask["task"] for subtask in subtasks]))
        feedback = input("Provide inputs on substasks. If everything is good then don't write anything and just press enter. ")
        if feedback == "":
            break
    
    
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
    relevantextactions = env.LTM.get(query = env.environment["objective"]["task"]+"\n", memorytype ="externalactions", cutoffscore =0.1, top_k=7)
    relevantextactions = {i[1]["id"]: i[1]["data"] for i in relevantextactions}
    env.STM.set("relevantactions",relevantextactions)
    
    
    relevantnodeid, programdesc,helpernodesdesc = pg.getprogramto_extend(env, env.STM.get("summaryobjective"), objective["subtasks"])#summarize(objective+"\n"+axioms))
    #relevantnodeid = env.STM.get("relevantnodes")[0][0]
    #programdesc = 
    if not relevantnodeid:
        relevantnodeid = env.initnode
        programdesc = "Initializes the program with initial node; node id -> 1"
    
    ######## fetch relevant actions
    relevantfunctions = env.STM.get("relevantactions") #env.LTM.get(objective+"\n"+axioms,"externalactions",top_k=5)
    relevantfunctionstext = "\n".join([k+" -> "+v for k,v in relevantfunctions.items()])
    relevantfunctionstext +="\n"+"\n".join([k+" -> "+v for k,v in env.primitives.items()])                       
    
    retrycount = 0
    while True:
        #input("press a key to continue... ")
        print("Generating code...")
        if retrycount > MAXERRORRETRYCOUNT:
            #codeerror = ""
            retrycount = 0
            return "Unable to generate solution for this goal. Try redefining the goal. Here is the latest error "+codeerror, 1
        subtaskpromptprefix = "Following are the dependent subtasks already completed: \n"
        objectiveprefix = "Now complete the following objective:\n"
        systemmessage = actortsystemtemplate.format(functions = relevantfunctionstext, \
                    axioms = axioms, \
                    learnings = learnings, \
                    programdescription = programdesc,\
                    helpernodes = helpernodesdesc, \
                    terminalnode = relevantnodeid, \
                    initialnode = env.initnode, 
                    #terminalnodedescription = env.graph["nodes"][relevantnodeid]["desc"], \
                    )
        usermessage = actorusertemplate.format(objective = objectiveprefix+objective["task"], \
                    subtasks = subtaskpromptprefix+'. '.join(objective["subtasks"]), \
                    error = codeerror)
        print("ACTORPROMPT system:",systemmessage)
        print("ACTORPROMPT user:",usermessage)
        output = chatpredict(systemmessage,usermessage)
        if len(output)<50:
            print("output",output)
        try:
            codeerror = ""
            output = extractdictfromtext(output)
            print("Generated code:","\n".join(output["program"]))
            ############ validate code #######################
            
            ############ excute code ###########
            input("press a key to continue... ")
            print("Executing code...")
            output,terminalnode,return_status = execcode("\n".join(output["program"]),env,relevantnodeid)
            if return_status != 0:
                codeerror = output
                print("CODERROR: ", codeerror)
                print ("Correcting code...")
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
    #print("Executing code: ", code)
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
        #print ("ACTION EXECUTION OUTPUT", output,return_status)    
    return (output,terminalnode,return_status)
 
###################### update failure status

###############################################
    
def critique (env,terminalnode):
    envfeedback = env.getfeedback()#input("Your feedback if any: ") 
    currentenvironment = env.environment
    currentenvironment_text = "objective: "+currentenvironment["objective"]["task"]+"   \n  "+"axioms: "+ currentenvironment["prior axioms"]+" \n "+env.STM.get("relevantbeliefs")
    progdesc,_ = pg.getprogramdesc(env.graph, terminalnode, programdesc = [],nodestraversed = [])
    progdesc = [desc for desc,idx in progdesc]
    currentperception = "\n".join([str(i) for i in env.STM.get("envtrace")])
    
    if env.graph["nodes"][terminalnode]["obs"] != None:
        if len(str(env.graph["nodes"][terminalnode]["obs"])) >100:
            currentperception += "\n"+"Final output: "+str(env.graph["nodes"][terminalnode]["obs"])[0:100]
        else:
            currentperception += "\n"+"Final output: "+str(env.graph["nodes"][terminalnode]["obs"])
    else:
        if len(str(env.graph["nodes"][terminalnode]["dat"])) >100:
            currentperception += "\n"+"Final output: "+str(env.graph["nodes"][terminalnode]["dat"])[0:100]
        else:
            currentperception += "\n"+"Final output: "+str(env.graph["nodes"][terminalnode]["dat"])
    
    if envfeedback != "":
        envfeedback = "User feedback: "+envfeedback
        currentperception += "\n"+envfeedback.upper()+"\n GIVE MOST IMPORTANCE ON USER FEEDBACK. \n" 
    
    message = critiquesystemtemplate.format(beliefenvironment = str(currentenvironment_text), \
                    actionplan = "\n".join(progdesc), \
                    perception = currentperception)
    #print("CRITIQUEPROMPT:",messages)
    print("Running critique...")
    output = chatpredict(message)
    
    #output = ast.literal_eval(output)
    output = extractdictfromtext(output)
    print("CRITIQUE output:",output)
    env.STM.set("critique", output)
    
    if env.graph["nodes"][terminalnode]["R"] == 0.0000001:
        env.graph["nodes"][terminalnode]["R"] = output["feedback"] ## set the reward
    else:
        env.graph["nodes"][terminalnode]["R"] = env.graph["nodes"][terminalnode]["R"]+ output["feedback"]
    pg.updatevalue(env,terminalnode)
    
    return output["feedback"]
    
    
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
    systemmessage = learnersystemtemplate.format(environment = currentenvironmenttext,
                    learnings = learningstext)
    usermessage = learnerusertemplate.format(EnvTrace = EnvTrace_text,
                    critique = critique)
        #print(messages)
    #print("LEARNERPROMPT:",messages)
    print("Generating Learnings..")
    output = chatpredict(systemmessage,usermessage)
    
    output = extractdictfromtext(output)
    learnings = output["learnings"]
    print("Generated learnings:","\n".join(learnings))
    #currentenvironment["env"]["belief axioms"] = beliefaxioms
    for learning in learnings:
        text = "objective: "+env.STM.get("summaryobjective")+"\n learning: "+learning
        env.LTM.set(text = text, data = learning, recordid=str(uuid.uuid4()), memorytype = "semantic")
    env.STM.set("envtrace",[]) ######## reset envtrace
    input("press any key to continue...")
    return output