import random
import string
import math 
alpha = 0.2
gamma = 0.9
TDTHRESHOLD = 0.2
ucb_c = 0.9
NONLINEARITYFACTOR = 3
EXPLORETRIALTHRES = 2
class envmodel():
    def __init__(self):
        self.rootnodeid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.invalidnodeid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.DEFAULTVALUE = 0
        self.statespace = {"nodes":{
                                   self.rootnodeid: { "state": "start",
                                                    "value" : self.DEFAULTVALUE,
                                                    "trial" : 1,
                                                    "ucb": 0,
                                                    "totalpossibleaction":1,
                                                    "defaultucbfactor" : 0
                                                    },
                                   self.invalidnodeid: { "state": "invalid",
                                                    "value" : self.DEFAULTVALUE,
                                                    "trial" : 0,
                                                    "ucb": 0,
                                                    "totalpossibleaction":1,
                                                    "defaultucbfactor" : 0
                                                       }
                                   },
                            "edges": { self.rootnodeid+"-"+self.rootnodeid:
                                   {"action": "dummy","from":self.rootnodeid,"to":self.rootnodeid, "reward" : 0}
                                   }}
        self.totaltrials = 0
        self.defaultucb = self.DEFAULTVALUE + 1
        self.rootstate = True
        
        
    def addaction(self,action,startstate, endstate, reward, totalactions,starttotactions):
        ###### if parent node of start node is root node then increment rootnode trial by 1
        if self.rootstate:
            self.statespace["nodes"][self.rootnodeid]["trial"] +=1

        ############## add retrieve start state
        startnodeid = [id for id,node in self.statespace["nodes"].items() if node["state"] == startstate] 
        if startnodeid:
            startnodeid = startnodeid[0]
                
        else:
            startnodeid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.statespace["nodes"][startnodeid] = {"state": startstate, "value" : self.DEFAULTVALUE,"trial" : 1,"totalpossibleaction":starttotactions}
            ########## add root node edge
            #rootnodeid = self.statespace["nodes"]["start"]["id"]
            self.statespace["edges"][self.rootnodeid+"-"+startnodeid+"-"+"dummy"] = {"action": "dummy", "reward": 0,"from":self.rootnodeid,"to":startnodeid}
        
        if self.rootstate:
            self.statespace["nodes"][startnodeid]["trial"] +=1
            self.rootstate = False
        
        ############## add retrieve end state
        if reward == float('-Inf'):
            ############ invalid action
            endnodeid = self.invalidnodeid
        else:
            endnodeid = [id for id,node in self.statespace["nodes"].items() if node["state"] == endstate]         
            if endnodeid:
                endnodeid = endnodeid[0]
                self.statespace["nodes"][endnodeid]["trial"] +=1
            else:
                endnodeid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                self.statespace["nodes"][endnodeid] = {"state": endstate, "value" : self.DEFAULTVALUE,"trial" : 1,"totalpossibleaction":totalactions}
        
        ############## add update edge
        edge = [edgeid for edgeid, edge in self.statespace["edges"].items() if edge["from"] == startnodeid and edge["to"] == endnodeid and edge["action"] == action ]
        if edge:
            edgeid = edge[0]
            reward = max(reward, self.statespace["edges"][edgeid]["reward"])
        else:
            edgeid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.statespace["edges"][edgeid] = {"action": action, "reward": reward,"from":startnodeid,"to":endnodeid}
        self.totaltrials += 1
        
    def parseacpt_trace(self,ACPT,startstate):    
        for actionperception in ACPT:
            self.addaction(actionperception["action"], startstate, actionperception["state"], actionperception["reward"], actionperception["totactions"], actionperception["starttotactions"])
            startstate = actionperception["state"]
            
        self.updatevalue()        

        
    def updatevalue(self):
        maxvaluediff = 0
        for i in range(10): ###### run for n iterations
            for fromnodeid,node in self.statespace["nodes"].items(): ######## update value of all nodes
                if node["state"] in ["start", "invalid"]:
                    continue
                fromnodevalue = node["value"]
                tonodes = [(edge["to"],edge["reward"]) for edge in self.statespace["edges"].values() if edge["from"] == fromnodeid and edge["reward"] != float('-Inf')]
                
                tonodevalues = [ self.statespace["nodes"][tonode[0]]["value"] for tonode in tonodes]
                ####### update value of from node for each tonode independently
                for tonode in zip(tonodes,tonodevalues):
                    fromnodevalue += alpha*(tonode[0][1] + gamma*tonode[1] - fromnodevalue)
                    maxvaluediff = max(maxvaluediff, (tonode[0][1] + gamma*tonode[1] - fromnodevalue))
                self.statespace["nodes"][fromnodeid]["value"] = fromnodevalue
            if  maxvaluediff < TDTHRESHOLD:
                break            
            
        ########## update UCB
        for id,node in self.statespace["nodes"].items():
            if node["state"] not in ["start", "invalid"]:
                parentnodetrials = sum([ self.statespace["nodes"][edge["from"]]["trial"] for edge in self.statespace["edges"].values() if edge["to"] == id ])
                self.statespace["nodes"][id]["ucb"] = self.statespace["nodes"][id]["value"] + ucb_c*math.sqrt(math.log(parentnodetrials)/self.statespace["nodes"][id]["trial"])
                numberofvalidactionstaken = len([edge for edge in self.statespace["edges"].values() if edge["from"] == id and self.statespace["nodes"][edge["to"]]["state"] != "invalid"])
                self.statespace["nodes"][id]["defaultucbfactor"] = pow((self.statespace["nodes"][id]["totalpossibleaction"] - numberofvalidactionstaken)/self.statespace["nodes"][id]["totalpossibleaction"], NONLINEARITYFACTOR)

        
        self.defaultucbexplore = ucb_c*math.sqrt(math.log(self.totaltrials))
        
        
        
    def getplandetails(self,currentstate):
        actionpath = []
        fromnode = [id for id,node in self.statespace["nodes"].items() if node["state"] == currentstate]
        if fromnode:
            fromnodeid = fromnode[0]
        else:
            prompt = "\n\nYou are at the state: \n"+currentstate +"\n\n"
            return prompt,[],[],False,1
        tonode = ""
        avoidactions = []
        visitednodeids = [fromnodeid]
        while True:
            tonodes = [[edge["to"],edge["action"]] for edge in self.statespace["edges"].values() if edge["from"] == fromnodeid]        
            tonodes_ucb = [[self.statespace["nodes"][tonode[0]]["ucb"],tonode[0],self.statespace["nodes"][tonode[0]]["value"]] for tonode in tonodes if self.statespace["nodes"][tonode[0]]["state"] != "invalid"]
            if not tonodes:
               print("NO LEAFNODES....")
               break
            if not tonodes_ucb:
               avoidactions = [i[1] for i in tonodes]
               print("NO VALID LEAFNODES....")
               break
            tonode = max(tonodes_ucb, key=lambda x: x[0])
           
            fromnodetrials = self.statespace["nodes"][fromnodeid]["trial"]
            defaultucbexplore = ucb_c*math.sqrt(math.log(fromnodetrials))
            defaultucb = self.DEFAULTVALUE + self.statespace["nodes"][fromnodeid]["defaultucbfactor"]*defaultucbexplore
            tonodeexploreucb = (tonode[0] - tonode[2])*self.statespace["nodes"][fromnodeid]["defaultucbfactor"] + tonode[2]
            
            if tonodeexploreucb < defaultucb:
               avoidactions = [i[1] for i in tonodes]
               print("EXPLORING....")
               break
            if tonode[1] in visitednodeids:
               print("LOOP DETECTED.... ",tonode[1])
               break
            bestaction = [i[1] for i in tonodes if i[0] == tonode[1] ][0]
            actionpath.append(bestaction)
            currentstate = self.statespace["nodes"][tonode[1]]["state"]
            fromnodeid = tonode[1]
            visitednodeids.append(fromnodeid)
        prompt = ""
        ucbfactor = self.statespace["nodes"][fromnodeid]["defaultucbfactor"]
        if self.statespace["nodes"][fromnodeid]["trial"] > EXPLORETRIALTHRES:
            explore = True
        else:
            explore = False
        #if actionpath:
        #    prompt = "YOU NEED TO TAKE THE FOLLOWING ACTIONS IN SEQUENCE \n"+ "\n".join(actionpath)+"\n\n You arrive at the following state after taking the above actions\n"+currentstate+"\n\n"
        #else:
        prompt = "You are at the state: \n"+currentstate +"\n\n" 
        if avoidactions:
            prompt += "find rest of the action plan. You should STRICTLY AVOID the following IMMEDIATE ACTIONS from the current state. \n" + "\n".join(avoidactions)
        else:
            prompt += "find rest of the action plan."
        actionpath = ".\n Call the takeenvaction module with parameter ".join(actionpath)
        return prompt,actionpath,avoidactions,explore,ucbfactor
        
  
   