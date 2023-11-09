from scienceworld import ScienceWorldEnv

class chatenv():
    def __init__(self):
        self.environment = {"description": "Allow user to ask questions and provide optimal answers","objective": "Allow user to ask questions and provide optimal answers", "beliefaxioms":""}
        return
        
    def getfeedback(self):
        return input("write your feedback.. ")  
    
    def act(self):
        return input("Ask a question.. ")
    
    def checkgoal(self):
        return False
        
chatenvobj = chatenv()


class scienv():
    def __init__(self,task = "1-1"):
        self.env = ScienceWorldEnv(task)
        obs1, info1 = self.env.reset()
        self.observation = []
        self.actiontrace = []
        self.reward = -1
        self.totalreward = 0
        self.goalreached = False
        predescription = "An AI agent helping execute a science experiment in a simulated environment with limited number of objects and actions available at each step. "
        prioraxioms = """
        an agent situated in textual task environment. Action can be taken by calling the function module named 'takeenvaction'. 
        The takeenvaction takes a text value as an argument, that denotes the type of action that will be taken.
        Here are the possible set of parameter values  that can be passed as argument to 'takeenvaction', where OBJ should be replaced by any object that you can find in your current state.  You can take only one action. The environment is fully not observable. New objects and states can be observed after taking different actions. The action plan should be realistically and scientifically valid. 
        you may reset the environment if you feel stuck and need to start over.
        focus is a extremely critical action that can be only used the number of times 'focus' is mentioned in the task description. Using it more than that or inappropiately (such as on a wrong object) will terminate the session and the task will be rendered as incomplete. focus can be used on the object which is available in current state.
        Do not make up new actions or objects. If you dont find appropriate objects for actions to meet the objective then generate plan to explore the environment to find required objects. If some events need some time to occur after some action is taken then take the action wait to observe the effect after some time.
        Set of parameter values:
          """+str(self.env.getPossibleActions())
          
      
        self.environment = {"description": predescription + self.env.getTaskDescription(), "objective": self.env.getTaskDescription(), "prior axioms": prioraxioms, "belief axioms": "", "current state": self.getstate()}
        
        self.examples = """
        Example 1:
           {"planid" : "jkuhy85r",
            "actionplan": "call module takeenvaction with the parameter 'look around'", "requiredactions" :["12735468"],
            "cumulative reward" : 0}
        Example 2:
            {"planid" : "jkuhy85r",
            "actionplan": "call module takeenvaction with the parameter 'open door to greenhouse'", "requiredactions" :["12735468"],
            "cumulative reward" : 0}
        """
        return
        
    def getstate(self):
        obs, _,_,_ = self.env.step("look around")
        state = """
        Currently you see the following things:
          """+ obs+"""
               
        Currently you can access the following objects::
          """+str(self.env.getPossibleObjects())+"""
               
        The agent have following things in its inventory.
        """+ str(self.env.inventory()).replace("In your inventory, you see:","")
        
        return state
        
    def getfeedback(self):
        #if max(self.reward) == 0:
        #    reward = -0.5
        #else:
        #    reward = max(self.reward)
        return "Observation: "+'\n'.join([i.replace("\n", "; ") for i in self.observation])+" External feedback: "+ str(self.success_map('reward',self.reward)), self.getstate()
    
    def traceact(self,actiontext):
        try:
            observation, reward, self.goalreached, info = self.env.step(actiontext)
        except:
            pass
        return observation
    
    def act(self,actiontext):
        self.actiontrace.append(actiontext)
        try:
            observation, reward, self.goalreached, info = self.env.step(actiontext)
            self.observation.append( "{ Action taken: "+actiontext+" ; Observation : "+ observation.replace("\n", "; ")+"}")
            if actiontext == "reset task":
                self.reward = -1
                self.totalreward = 0
            else:
                self.reward +=reward
                self.totalreward += reward
        except Exception as e:
            self.observation = "{ Action taken: "+actiontext+" ; Observation : Error - "+ str(e).replace('\n'," ")+"}"
            self.reward -=1
        
        return self.observation
    
    def checkgoal(self):
        #obs1, info1 = self.env.reset()
        self.observation = []
        self.reward = -1
        print ("total reward", self.totalreward)
        return self.goalreached
    
    def success_map(self, metric, score):
        feedback = ''
        if metric == 'reward':
            if score == -100:
                feedback += "The agent made critical mistakes and the task was terminated and reset."
            if score < 0:
                feedback += "The agent performed very poorly and could not make any critical progress."
            if score >= 0 and score < 20:
                feedback += "The agent performed poorly and made some progress but not enough to solve the task."
            if score >= 20 and score < 50:
                feedback += "The agent performed moderately and made some critical progress but not enough to solve the task."
            if score >= 50 and score < 90:
                feedback += "The agent performed very well and made significant critical progress but not enough to solve the task."
            if score >= 90 and score < 100:
                feedback += "The agent performed exceptionally well and made significant critical progress, was just slight away from solving the task."
            if score == 100:
                feedback += "The agent performed exceptionally well and successfully solved the task."
        
        return feedback