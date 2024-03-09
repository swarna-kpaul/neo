from scienceworld import ScienceWorldEnv


class world_exception(Exception):
    def __init__(self, message={}):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.error = message

class chatenv():
    def __init__(self):
        self.environment = {"description": "Allow user to ask questions and provide optimal answers","objective": "Allow user to ask questions and provide optimal answers", "beliefaxioms":""}
        return
    def reset(self):
        pass
    
    def getfeedback(self):
        return input("write your feedback.. ")  
    
    def act(self):
        return input("Ask a question.. "),1
    
    def checkgoal(self):
        return False
        
chatenvobj = chatenv()


from scienceworld import ScienceWorldEnv
from models.buildstatespacemodel import *

class world_exception(Exception):
    def __init__(self, message={}):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.error = message


class scienv():
    def __init__(self,task = "1-1", objective = None):
        self.task = task
        self.env = ScienceWorldEnv(task)
        self.totalexplore = 9
        self.MINREWARD = -100
        self.MAXREWARD = 100
        obs1, info1 = self.env.reset()
        self.trace = []
        self.actiontrace = []
        self.reward = -1
        self.totalreward = 0
        self.goalreached = False
        self.toberesetflag = False
        self.rootstate = True
        self.additionalstateinfo = ""
        predescription = "An AI agent helping execute a science experiment in a simulated environment with limited number of objects and actions available at each step. "
        prioraxioms = """
        an agent situated in textual task environment. Generate a sequence of actions to meet the objective.
        FOCUS is a extremely critical action that can be only used the number of times 'focus' is mentioned in the task description and in the exact same sequence. Using it more than that or inappropiately (such as on a wrong object) will terminate the session and the task will be rendered as incomplete. focus can be used on the object which is available in current state. Do not add too many consecutive wait.
        Do not make up new actions or objects.
             
        An action can be taken in the environment by calling the function takeenvaction with the action name as parameter.
        
        DO NOT TAKE ANY ACTION ON ANY OBJECT that is NOT IN ACCESSIBLE OBJECTS in CURRENT STATE
        
        Here are the following set of allowed actions. where OBJ should be replaced by any object that you can find in your current state.
          """+str(self.env.getPossibleActions())+"""
         
        ALL ACTIONS SHOULD BE STRICTLY SELECTED FROM THE ABOVE LIST.        

        On taking an action the environment returns observation in text form. The function getanswer can be called to extract relevant information from the observation to aid further decision making.        
         """
          
         
        if objective == None:
            objective = self.env.getTaskDescription()
        else:
            objective = self.env.getTaskDescription() +". "+ objective
                
        self.examples = """
        Example 1:
           ["look around", "open door to greenhouse"]
        Example 2:
           ["go door to hallway", "open door to kitchen"]
        """
        self.environment = {"description": predescription + objective, "objective": objective, "prior axioms": prioraxioms, "belief axioms": "", "current state": self.getstate(), "examples": self.examples}
        return
     
    def reset(self):
        obs1, info1 = self.env.reset()
        #self.env.load(self.task, random.choices(range(10))[0])
        self.additionalstateinfo = ""
        self.environment["current state"] = self.getstate()
        self.rootstate = True
        self.totalreward = 0
        self.toberesetflag = False
        
     
    def getstate(self):
        obs, _,_,_ = self.env.step("look around")
        state = """
        Currently you see the following things:
          """+ obs+self.additionalstateinfo+"""
               
        Currently you can access the following objects::
          """+str(self.env.getPossibleObjects())+"""
               
        The agent have following things in its inventory.
        """+ str(self.env.inventory()).replace("In your inventory, you see:","")
        
        return state
        
    def getfeedback(self):
        feedback = self.success_map('reward',self.totalreward)
        print ("total reward", self.totalreward)
        if self.toberesetflag:
            self.reset()
        return  feedback
    
    def traceact(self):
        for actiontext in self.actiontrace:
            observation, reward, self.goalreached, info = self.env.step(actiontext)
        return observation
    
    def act(self,actiontext):
        self.actiontrace.append(actiontext)
        
        prevstate = self.getstate()
        
        startstatetotalpossibleactions = len(self.env.getValidActionObjectCombinationsWithTemplates())
        
        observation, reward, self.goalreached, info = self.env.step(actiontext)
        
        poststate = self.getstate()
        self.totalreward += reward
        self.rootstate = False
        
        if observation == "No known action matches that input.":
            self.trace.append({"action":actiontext, "observation" : observation.replace("\n", "; "), "state": self.getstate(), "reward":float('-Inf'),"totactions": 1, "starttotactions": startstatetotalpossibleactions,"isvalidactionformemorizing": False })
        elif observation in ["The door is not open.", "The door is already open.","It's not clear how to get there from here."] or observation.startswith("Its not clear how to") or observation.startswith("I'm not sure"):
            self.trace.append({"action":actiontext, "observation" : observation.replace("\n", "; "), "state": self.getstate(), "reward":float('-Inf'),"totactions": 1, "starttotactions": startstatetotalpossibleactions,"isvalidactionformemorizing": True })
            #raise world_exception("invalid action")
        elif actiontext.startswith("focus") and reward < 0:
            observation += " You focused on the wrong object and that resulted in a critical mistake the environment was reset"
            self.goalreached = False
            self.trace.append({"action":actiontext, "observation" : observation.replace("\n", "; "), "state": self.getstate(), "reward":float('-Inf'),"totactions":1,"starttotactions": startstatetotalpossibleactions, "isvalidactionformemorizing": True})  #( "{ Action taken: "+actiontext+" ; Observation : "+ observation.replace("\n", "; ")+"}")
            #return self.observation#
            print("Punishment:", -100)
            self.toberesetflag = True
            
            raise world_exception("invalid action")
        else:
            if poststate == prevstate and actiontext not in [ "look around", "reset task", "reset", "inventory"] and not actiontext.startswith("look"):
                self.additionalstateinfo += "\n "+observation
            if reward > 0:
                normalizedreward = math.log(reward)
            elif reward < 0: 
                normalizedreward = -math.log(-reward)
            else:
                normalizedreward = reward 
            totalpossibleactions = len(self.env.getValidActionObjectCombinationsWithTemplates())
            self.trace.append({"action":actiontext, "observation" : observation.replace("\n", "; "), "state": self.getstate(), "reward": normalizedreward, "totactions": totalpossibleactions,"starttotactions": startstatetotalpossibleactions, "isvalidactionformemorizing": True})        
        return observation,reward
    
    def getpossibleactions(self):
        return  len(self.env.getValidActionObjectCombinationsWithTemplates())
      
    def checkgoal(self):
        if self.totalreward == 100:
            return True
        else:
            return False
                
    
    def success_map(self, metric, score):
        feedback = ''
        if metric == 'reward':
            if score < -50:
                feedback += "Total reward is: "+str(score)+". The agent made critical mistakes and the task was terminated and reset."
            if score < 0:
                feedback += "Total reward is: "+str(score)+". The agent performed very poorly and could not make any critical progress."
            if score >= 0 and score < 20:
                feedback += "Total reward is: "+str(score)+". The agent performed poorly and made some progress but not enough to solve the task."
            if score >= 20 and score < 50:
                feedback += "Total reward is: "+str(score)+". The agent performed moderately and made some critical progress but not enough to solve the task."
            if score >= 50 and score < 90:
                feedback += "Total reward is: "+str(score)+". The agent performed very well and made significant critical progress but not enough to solve the task."
            if score >= 90 and score < 100:
                feedback += "Total reward is: "+str(score)+". The agent performed exceptionally well and made significant critical progress, was just slight away from solving the task."
            if score == 100:
                feedback += "Total reward is: "+str(score)+". The agent performed exceptionally well and successfully solved the task."
        
        return feedback