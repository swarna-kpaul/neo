from config.configurations import *
from config.prompts import *
from langchain.prompts.prompt import PromptTemplate
import traceback
from environment.problemenvs import *
CONTEXTCODE = "import environment.context as context"
import ast
import pickle

gamma = 0.8
CUMULATIVEREWARDTHRESHOLD = 5
EPISODELEN = 3
MAXPLANCRITUQUETRIAL = 10

class neo():
    def __init__ (self,environment, stmloadfile, stmstoragefile, STMsize = 10):
    
        self.ltm = LTM() 
        self.stmsize = STMsize
        self.stmstoragefile = stmstoragefile
        if stmloadfile != None:
            with open(stmloadfile, 'rb') as f:
                self.stm,actiontrace,observation,reward,totalreward = pickle.load(f)
            self.env.state = self.stm.get("currentenv")["env"]["state"]
            ############# execute action trace
            for action in actiontrace:
                self.env.problemenv.traceact(action)
            self.env.problemenv.observation = observation
            self.env.problemenv.reward = reward
            self.env.problemenv.totalreward = totalreward
            
        else:
            self.stm = STM()
            self.env = environment
            id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.stm.set({'id': id, 'env': environment.bootstrapbeliefenvironment},"currentenv")
        self.SEARCHERPROMPT = PromptTemplate(input_variables=SEARCHERPROMPTINPUTVARIABLES, template=searchertemplate)
        self.ACTORPROMPT = PromptTemplate(input_variables=ACTORPROMPTINPUTVARIABLES, template=actortemplate)
        self.ACTPLANPROMPT = PromptTemplate(input_variables=ACTPLANPROMPTINPUTVARIABLES, template=actionplantemplate)
        self.CRITIQUEPROMPT = PromptTemplate(input_variables=CRITIQUEPROMPTINPUTVARIABLES, template=critiquetemplate)
        self.CODEEQUIVALENCEPROMPT = PromptTemplate(input_variables=CODEEQUIVALENCEVARIABLES, template=codequivalencetemplate)
        self.PLANEQUIVALENCEPROMPT = PromptTemplate(input_variables=PLANEQVVARIABLES, template=planequivalencetemplate)
        self.ACTPLANCRITIQUEPROMPT = PromptTemplate(input_variables=ACTPLANCRITIQUEINPUTVARIABLES, template=actionplancritiquetemplate)
    
    def searcher (self):
        EnvTrace = self.stm.get("EnvTrace")
        #critique = self.stm.get("critique")
        currentenvironment = self.stm.get("currentenv")["env"]
        currentbelief = {"belief axioms": currentenvironment["belief axioms"]}
        #ACPtrace_text = "\n".join([ "    Action plan: "+ i["actionplan"]["actionplan"]+"\n    Environment response: "+ i["perception"] for i in ACPtrace])
        EnvTrace_text = "\n".join([str(i) for i in EnvTrace])
        relatedenvironments = self.ltm.get(str(currentenvironment), namespace = "environments")
        if relatedenvironments:
            relatedenvironments = [ "    Environment "+str(i)+":\n"+str(env["metadata"]) for i,env in enumerate(relatedenvironments) if env["id"] != currentenvironment['id'] ] 
            relatedenvironments = ["\n".join(relatedenvironments)]
        else:
            relatedenvironments = ""
        messages = self.SEARCHERPROMPT.format(relatedenvironments = str(relatedenvironments),
                        beliefenvironment = currentbelief,
                        EnvTrace = EnvTrace_text)
            #print(messages)
        print("SEARCHERPROMPT:",messages)
        output = llm_model.predict(messages)
        print("SEARCHERPROMPT output:",output)
        output = ast.literal_eval(output)
        self.stm.set({'id': currentenvironment['id'], 'env':output},"currentenv")
        output['type'] = "environments"
        ltmdata = [{'id': currentenvironment['id'], 'values': output['description'], 'metadata': output }]
        self.ltm.set(data = ltmdata, namespace = "environments")
        return output
    
    def actplancritique(self, actionplan):
        currentenvironmentaxioms = self.stm.get("currentenv")['env']["prior axioms"]+"\n"+self.stm.get("currentenv")['env']["belief axioms"]+"\n"+self.stm.get("currentenv")['env']["current state"]
        objective = self.stm.get("currentenv")['env']['objective']
        messages = self.ACTPLANCRITIQUEPROMPT.format(axioms = currentenvironmentaxioms, actplan = actionplan)
        print("ACTPLAN CRITIQUE:", messages)
        while True:
            output = llm_model.predict(messages)
            try:
                output = ast.literal_eval(output)
                print ("ACTPLANCRITIQUE output:", output)
                if output["feedback"] == "valid":
                   return True,""
                else:
                   return False, output["reason"]
            except Exception  as e:
                #errorfeedback = "Here is the last actionplan generated. "+ output+ "\n But this action plan has the following error. Modify the plan to remove the error.\n"+str(e)
                print(e)
                input("Press any key to continue...")
                continue
            break
        #return output
    
    def actplan(self):
        currentenvironment = self.stm.get("currentenv")['env']
        ACPtrace = self.stm.get("ACPtrace")
        #critique = self.stm.get("critique")
        #currentperception = self.env.perception
        ACPtrace_text = "\n".join([ "    AI: "+ str(i["actionplan"])+"\n    Environment: "+ i["perception"] for i in ACPtrace])
        #objective = self.env.actplanobjective
        
        relatedactionset = self.ltm.get(currentenvironment["description"]+currentenvironment["objective"]+currentenvironment["prior axioms"], namespace = "actions",k = MAXRELATEDACTIONSET)
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
            messages = self.ACTPLANPROMPT.format(beliefenvironment = currentenvironment, \
                        ACPtrace = ACPtrace_text, \
                        relatedactions = '\n'.join(relatedactionlist), \
                        actionplanexamples = self.env.problemenv.examples,\
                        errorfeedback = errorfeedback)
            print("ACTPLANPROMPT:",messages)
            output = llm_gpt4.predict(messages)
            
            
            try:
                output = ast.literal_eval(output)
            except Exception  as e:
                #errorfeedback = "Here is the last actionplan generated. "+ output+ "\n But this action plan has the following error. Modify the plan to remove the error.\n"+str(e)
                input("Press any key to continue...")
                continue
            print("ACTPLANPROMPT output:",output)
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
        #self.stm.set(errorfeedback,"errorfeedback")
        return output
        
    def checkplanequivalence(self,actionplan):
        ACPtrace = self.stm.get("ACPtrace")
        historicalplan = self.ltm.get(actionplan["actionplan"], namespace = "stmactionplan",k = 1)
        historicalplanid = ''.join([i['id'] for i in historicalplan])
        historicalactionplan = ''.join([i['metadata']['actionplan'] for i in historicalplan])
        messages = self.PLANEQUIVALENCEPROMPT.format(historicalactionplan = historicalactionplan, \
                        generatedactionplan = str(actionplan['actionplan']))
        print("PLANEQVPROMPT:",messages)
        output = llm_defn_model.predict(messages)
        print("PLANEQVPROMPT output:",output)
        if output == "True":
            output = actionplan
            output["planid"] = historicalplanid
        else:
            output = actionplan
            output["planid"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return output
        
    def actor(self,actionplan,currentcode="", codeerror = ""):
        relatedactionsets = {}
        actionids = list(set(actionplan["requiredactions"]))
        actionset = self.ltm.fetch(actionids, namespace = "actions")
        
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
        beliefenvironment = self.stm.get("currentenv")['env'] #["objective"]
        ACPtrace = self.stm.get("ACPtrace")
        prevactionplan = ACPtrace[-1]["actionplan"]["actionplan"] if ACPtrace else ""
        messages = self.ACTORPROMPT.format(beliefenvironment = beliefenvironment, \
                        actions = relatedactiontext, \
                        actionplan = actionplantext, \
                        error = codeerror)
        print("ACTORPROMPT:",messages)
        output = llm_gpt4.predict(messages)
        print("ACTORPROMPT output:",output)
        output = ast.literal_eval(output)
        output["requirements"] = '\n\n'.join([relatedaction["requirements"]+"\n\n"+relatedaction["code"] for id,relatedaction in relatedactionsets.items()]) 
        
        print("ACTOR Code:",output["code"])
        return output
        
    
    def critique (self,currentactionplan,currentperception):
        currentenvironment = self.stm.get("currentenv")['env']
        #envobjective = currentenvironment["objective"]
        #beliefaxioms = currentenvironment["beliefaxioms"]
        #critique = self.stm.get("critique")
        #ACPtrace = self.stm.get("ACPtrace")
        #actionplan = ACPtrace[-1]["actionplan"]["actionplan"]
        #perception = ACPtrace[-1]["perception"]
        messages = self.CRITIQUEPROMPT.format(beliefenvironment = str(currentenvironment), \
                        actionplan = currentactionplan, \
                        perception = currentperception)
        print("CRITIQUEPROMPT:",messages)
        output = llm_model.predict(messages)
        print("CRITIQUEPROMPT output:",output)
        output = ast.literal_eval(output)
        
        self.stm.set(output,"critique")
        return output
        
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
    
    def processstmactionplan(self,output,action,historicalactionplans,critiquefeedback):
        ########### store actionplan in stm #####################################################################
        if output["planid"] in historicalactionplans:
            newactionplan = historicalactionplans[output["planid"]]
            cumulativereward = gamma*newactionplan["cumulative reward"]
            newaction = True
        else:
            newactionplan = pickle.loads(pickle.dumps(output,-1))
            newactionplan["trials"] = 0
            cumulativereward = 0
            newaction = True
        newactionplan['action'] = action
        newactionplan["cumulative reward"] =  cumulativereward + critiquefeedback["feedback"]
        newactionplan["trials"] += 1
        
        ###### update stalefactor
        historicalactionplans = {k: {k1: v1 + 1 if k1 == 'stalefactor' else v1 for k1, v1 in v.items()} for k, v in historicalactionplans.items()}
        newactionplan["stalefactor"] = 0
        
        if (newactionplan["cumulative reward"] > 0 and newaction) or (not newaction and newactionplan["cumulative reward"] > -CUMULATIVEREWARDTHRESHOLD) :
        ########### for new action plans if reward is >0 then add to memory
            historicalactionplans[output["planid"]] = newactionplan
            if newaction:
            ######## add embedding
                output['type'] = "stmactionplan"
                ltmdata = [{'id': output["planid"], 'values': output['actionplan'], 'metadata': output }]
                self.ltm.set(data = ltmdata, namespace = "stmactionplan")
                del output['type']
        elif not newaction and newactionplan["cumulative reward"] < -CUMULATIVEREWARDTHRESHOLD:
        ########### for old action plans if reward is < -threshold then del from memory
            del historicalactionplans[output["planid"]]
            self.ltm.delete([output["planid"]])
            
        if len(historicalactionplans) > self.stmsize:
            ##### forget stalest action plan
            stalefactors = {k: max([v1 if k1 == 'stalefactor' else -1 for k1, v1 in v.items()])  for k, v in historicalactionplans.items() }
            key_of_max_value = max(stalefactors, key=stalefactors.get)
            del historicalactionplans[key_of_max_value]
            self.ltm.delete([key_of_max_value])
            
        print("HISTORICALACTIONPLANS.. ", historicalactionplans)
        self.stm.set(historicalactionplans,"actionplans")
        return newactionplan["cumulative reward"] 
            #####################################################################################################
            
    def actionplantoaction(self,output):
        ########## check for known action
        print("Generating action....")
        historicalactionplans = self.stm.get("actionplans")
        if output["planid"] in historicalactionplans:
            action = historicalactionplans[output["planid"]]["action"]
            output["actionplan"] = historicalactionplans[output["planid"]]["actionplan"]
            output["requiredactions"] = historicalactionplans[output["planid"]]["requiredactions"]
        else:
        ########### generate action code          
            action = None
            while action is None:
                try:
                    action = self.actor(output)
                except Exception as e:
                    pass
                    print ("Error", str(e))
                k = input("Press any button to continue ...")
        ##### write actor output to environment
        if action['functioncall'] != "":
            actioncode = action['requirements']+"\n\n"+action['code']+ "\n\nresult="+action['functioncall'] 
        else:
            actioncode = action['requirements']+"\n\n"+action['code']    
        print("Final Action code:",  actioncode)           
        self.env.write(actioncode)
        
        ##### Resolve any code errors if present
        while self.env.codeerror:
            print("Resolving code error and regenerating action....")
            hint = input("You may add a hint to resolve the error ...")
            #actioncode = action['requirements']+"\n\n"+action['code'] 
            
            codeerrorprompt = """
            Following is the action code generated for the actionplan. 
            action code:
               {}
            But a code error recieved while executing the full program (concatenation of requirements, code and functioncall) in the environment.
            Code error:
               {}
            update the action code  (code, requirements and functioncall) to remove all code errors. at any cost to remove all errors. Make sure not to create any infinite loops. It should run for finite time.
            """
            
            
            newaction = None
            while newaction is None:
                try:
                    newaction = self.actor(output,str(action),codeerrorprompt.format(str(action), self.env.perception+"\n"+hint))
                except Exception as e:
                    pass
                    print ("Error", str(e))
                k = input("Press a key to continue ...")    
                
            action = newaction
            if action['functioncall'] != "":
                actioncode = action['requirements']+"\n\n"+action['code'] + "\n\nresult="+action['functioncall']
            else:
                actioncode = action['requirements']+"\n\n"+action['code']
            print("Final Action code:",  actioncode)
            self.env.write(actioncode )
            
            #lifetime -= 1
        return action,historicalactionplans
    
    def run (self, lifetime = float("Inf")):   
        counter = 0
        while True:
            if lifetime <= 0 or self.env.goalreached:
                break
            ###### Run actor
            print("Running actionplan....")
            output = None
            while output is None:
                try:
                    output = self.actplan()
                    if output["actionplan"] == "":
                        raise NameError("No action plan generated")
                except Exception as e:
                    pass
                    print ("Error", str(e))
                k = input("Press any button to continue ...")
            
            ########## get planid
            print("Getting planid...")
            flag = True
            while flag:
                try:
                    output = self.checkplanequivalence(output)
                    flag = False
                except Exception as e:
                #    pass
                    print ("Error",  traceback.format_exc())
                k = input("Press any button to continue ...")
            
            ######### actionplan to action ###########
            action,historicalactionplans = self.actionplantoaction(output)
            
            self.env.getreward()
            
            ########## update environment state
            currentenvironment = self.stm.get("currentenv")
            currentenvironment["env"]["current state"] = self.env.state
            self.stm.set(currentenvironment,"currentenv")
            
            ##### run critique
            print("Running critique....")
            critiquefeedback = self.critique(output["actionplan"], str(self.env.perception))
            k = input("Press any button to continue ...")
            
            
        ########### store actionplan in stm #####################################################################
            k = input("Press any button to continue ...")
            cumulativereward = self.processstmactionplan(output,action,historicalactionplans,critiquefeedback)
            
            ###### set Action perception trace ##################################################################
            output["cumulative reward"] = cumulativereward
            
            # if critiquefeedback["feedback"] > 0.5:
                # critiquefeedback["feedback"] = "very positive" 
            # elif critiquefeedback["feedback"] > 0 and critiquefeedback["feedback"] < 0.5:
                # critiquefeedback["feedback"] = "positive" 
            # elif critiquefeedback["feedback"] < 0 and critiquefeedback["feedback"] > -0.5:
                # critiquefeedback["feedback"] = "negative" 
            # elif critiquefeedback["feedback"] < -0.5:
                # critiquefeedback["feedback"] = "very negative" 
            # else:
                # critiquefeedback["feedback"] = "neutral"
                
            newACPT = {"actionplan": output,"perception": str(critiquefeedback)}
            self.stm.set(newACPT,"ACPtrace")
            
            self.stm.set(str(self.env.perception), "EnvTrace")
            self.stm.set(self.env.state, "state")
            
            with open(self.stmstoragefile, 'wb') as f:
                pickle.dump((self.stm,self.env.problemenv.actiontrace,self.env.problemenv.observation,self.env.problemenv.observation,self.env.problemenv.reward,self.env.problemenv.totalreward),f)
            if output["cumulative reward"] >= CUMULATIVEREWARDTHRESHOLD:
                action["actiontype"] = "dynamic"
                self.storeactionasskill(action)
            
            counter += 1
            ########## If Short term memory fills up restimate environment ######################################
            if counter >= EPISODELEN:
                print("Running searcher....")
                env = None
                while env is None:
                    try:
                        env = self.searcher()
                    except Exception as e:
                        pass
                        print ("Error", str(e))
                    k = input("Press any button to continue ...")
                counter = 0
            lifetime -= 1
        self.searcher()    
            
        
        
class neoenv():
    def __init__(self,
                 bootstrapbeliefenvironment = {"description": "","objective": "", "belief axioms":""},
                 problemenv = chatenvobj):
                 #searcherobjective = DEFAULTSEARCHEROBJECTIVE):
                 #actplanobjective =  DEFAULTACTPLANJECTIVE, 
                 #actorobjective = DEFAULTACTOROBJECTIVE, 
                 #critiqueobjective = DEFAULTCRITIQUEOBJECTIVE):
        self.perception = ""
        self.codeerror = False
        self.goalreached = False
        self.problemenv = problemenv
        self.state = ""
        
        #self.searcherobjective = searcherobjective
        # self.actplanobjective = actplanobjective
        # self.actorobjective = actorobjective
        # self.critiqueobjective = critiqueobjective
        self.bootstrapbeliefenvironment = bootstrapbeliefenvironment
    def execcode(self, code):
        output = None
        return_status = None
        error = None
        try:
    # Create an empty namespace (dictionary) for the exec function
            exec_namespace = {"envobject": self}
            #print("Executing Code: ", code)
            exec(code,exec_namespace)
            output = exec_namespace.get("result", None)    
            return_status = 0
        except Exception as e:
            output = traceback.format_exc()
            return_status = 1
        print ("ACTION EXECUTION OUTPUT", output,return_status)    
        return (output,return_status)
      
    def write(self,actioncode):
        actioncode = CONTEXTCODE+"\n"+actioncode
        self.perception,self.codeerror = self.execcode(actioncode)    


    def getreward(self):
        self.perception,self.state = self.problemenv.getfeedback()
        self.goalreached = self.problemenv.checkgoal()#input("write your feedback.. ")    
        