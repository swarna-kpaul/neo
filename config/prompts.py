
# beliefenvironment
#      Description: short summary of the environment 
#      Objective: Objective of the agent in the environment
#      Actionset: Set of valid actions for the environment.
#      beliefaxioms : belief axioms with level of belief. Level of belief can be weak, moderate, strong and very strong

# DEFAULTACTPLANJECTIVE = """ You are an action planner for an AI agent. 
# Use the belief axioms, the objective of the environment model, the previous action perception trace and output of the critique to provide an action plan.
# The action should be inline with the objective and should get positive feedback from the critique in long term.
# You may use chain of thoughts to generate action plan.
# The output action plan should be concise and in algorithm format and contain enough detail to convert into a complete code.
# Keep a balance of exploration and exploitation in the actionplan to know more about the environment and meet the objective in the already known environment respectively.
# In the initial phase when the environment is not known well explore more to know the environment. 
# The output should be in following json format. In no case the output should deviate from the following json format.
# {"actionplan": <algorithm of actionplan in detail text format>,
# "subproblems" : [<distinct list of subproblems to be solved to carry out the action plan.>]
# }
#"""
# actionplantemplate = """System: {objective}
    # Environment:
        # {beliefenvironment}  
      
    # Action Perception trace:
        # {ACPtrace}
    
    # Critque:
       # {critique}
    
    # Perception: {lastperception}
    # Action: """
    
    
##Following is the critique provided by another expert agent on the previous action plan based on the internal criterias of the AI agent for generating an action plan
#Internal critique:
#    {internalcritique}    


#Following are the historical action plans provided by you and the corresponding responses generated by the environment on executing the action plan.
#Action plan history:
#   {ACPtrace}

#The action plan should get positive feedback from the critique in long term and meet the objective in the environment. From the action plan history if there is no progress observed in meeting the objective or gets negative feedback, the plan needs to be changed. If some actions are invalid in the plan then change the actions.


subtasktemplate = """System: You need to break a task into multiple sequential sutasks. 
Try to break the task into atomic tasks and keep the number of subtasks as minimum as possible. 
Generate the subtasks in such a way so that solving all of them sequentially solves the original task.
if a subtask needs input/help from any other subtasks please specify that explicitly in the corresponding subtask.

Keep the axioms about the problem environment in consideration while breaking the task
 Axioms:
 {axioms}

The output should be in following format.
{{"subtasks": [<list of subtasks>] }}

User: Generate the subtasks for the following task
 {task}

"""

SUBTASKVARIABLES = ["axioms","task"]


coderrortemplate = """Here is the error recieved after running the following code. Correct the following code to remove all errors.
 {code}

error:
 {error}
"""

CODEERRORVARIABLES = ["code","error"]

actionplantemplate = """System: You are an AI action planner for an autonomous agent. You are situated in a task environment, as provided by the user, prior axioms are the fixed rules and constraints of the environment, the belief axioms are your beliefs about the environment. You need to generate an action plan to meet the objective in the environment. Do not generate any aditional explanations.
 
The plan should be structured and have enough details to convert into a program.
Prior axioms should be given more preference than belief axioms.
The action plan should not have contradicting logic.

Here is a program that might partially meet the objective. Find rest of the program to fully meet the objective.
{programdescription}

Here is the actions taken be the above program and observations recieved from the external environment 
{envtrace}

Following is the list of stored functions.    
 {relatedactions}

Apart from above functions you may use conditional statements, arithmetic operations, logical operations, loop.
The action plan should be generated in functional style and do not use variable assignments.

The output should be in following format. Do not add the json tags so that it can be directly read by python. In NO CASE the output should deviate from the following format.
{{"planid" : <8 digit alphanumeric id>,
"actionplan": <algorithm of actionplan in plaintext. It should contain enough details to convert it into code. If a function module is called that takes input parameters, then properly supply the value of the input parameters in the actionplan. Do not call no-existent functions in allowed actions. Do not create infinite loops. Do not make up new actions or functions. Do not generate plans in separate lines.>,
"requiredactions" : [<distinct subset of moduleid from stored function modules needed to carry out the action plan. All modules should be strictly from stored function modules and do not make up any moduleids.>]
}}

Here are some example output.
  {actionplanexamples}


User: {userpromptprefix}
Environment:
        {beliefenvironment}  
        
{errorfeedback}


AI: 

"""

useractionplanmeetobjective = "Generate the action plan for the following environment. Give more importance on the belief axioms to generate a correct action plan. The action plan should be directed to meet the objective of the environment. If meeting the objetive needs for a subproblem to be solved then create the plan to solve the subproblem."

useractionplanexplore = "Generate a long random action plan to know more about the environment. Folow the belief axioms to generate correct action plan. Take actions to EXPLORE NEW AREAS and gain new information that is not available in belief axioms. "
    
ACTPLANPROMPTINPUTVARIABLES = ["beliefenvironment","programdescription","envtrace", "relatedactions","errorfeedback","userpromptprefix","actionplanexamples"]


actionplancritiquetemplate = """System: You are a critique of generated action plan by an AI agent situated in an environment. 
Check if the action plan violates any constraints in the following prior and belief axioms
Environment axioms:
    {axioms}  
 
Here is the action plan:
Action plan:
     {actplan}
     
and here is the objective of the plan
Objective:
    {objective}

The output should always be in the following json format. In no case it should deviate from the following format.
{{
 "feedback": <valid if the action plan satisfies all the constraints and invalid if it doesnt>,
 "reason" : <concise reason of the feedback based on which the action plan can be corrected>
}}

AI: 
"""

ACTPLANCRITIQUEINPUTVARIABLES = ["axioms", "actplan", "objective"]

# DEFAULTACTOROBJECTIVE = """ You are part of an AI agent that converts action plan to concrete executable action in form of python code. 
# The action is executed in an external environment.
# Use the related action modules as reusable functions or combine and/or modify them to create a new action code as per the action plan.
# If Current code and code error is available then you need to modify the current code to remove the code errors. 
# The output should only be in the following json format. No other text should be there. Add escape charachters wherever required to make the following a valid json definately.
# {"description" : <a short description of the action not exceeding 100 tokens>,
# "code": "<executable python 3 code of the action. The output code should be complete and executable in itself. add escape charachter before double quotes  within the function definition>",
# "requirements": "<full function definition code from related action modules, if any to be used in the above code. add escape charachter before double quotes  within the function definition>",
# "functioncall": "<above function name>(<required argument values>)"
# }

# The structure of the code will be as follows:
# import <any required inbuilt python library>
# <New function defintion with arguments and proper indentation. function body may contain python loops, conditional statements, arithmetic operations, python inbuilt functions,
# logical operations, variable assignments, complex math operations, 
# function calls with appropriate parameters that to related action modules that are defined above.
# Always return the data that you want to send to the main AI agent. 
# The return data can be any data collected from the environment, user , other AI agent or ant specific return data mention in the action plan.
# The above function call should not be present here.>

# """
# actortemplate = """System: {objective}
    # Related action modules:
        # {actions}
    
    # Action plan: {actionplan}
    
    # Current code:
       # {currentcode}
    
    # Code error:
       # {error}
        
    # Action: """

#  , 


actortemplate = """System: You are a programmer in a new programming model FGPM

Here are the details of programming model:
This is a dataflow graph based programming model where programs are represented as directed acyclic graph. The nodes represents operation or function and edges represents data flow.
A function node can have multiple input ports, each serving as a placeholder for separate input arguments. It can have only one output port that emits the computed output of the function. However multiple edges can emanate from an output port and output value is copied on each output edge. 
A program can be composed by connecting edges between multiple nodes. 
Every input argument of a node should be connected to another output port of another node.
Each complete executable program must end with a single node called as terminal node.  

Programs are evaluated in lazy style, such that terminal node is excecuted 1st and it calls the functions of its input arguments. This goes on recursively until initial node is reached.

A function node can be created with the command "createnode(<instance of a graph>,<function name>,<optional paramater only applicable for constant node>)". It returns a node identifier.
An edge can be created with the command "dedupaddlink(<instance of a graph>,<child node identifier>,<parent node identifiers in representing input arguments for child node>)". It returns the child node identifier.

Here are the list of function names available.
{functions}


There should not be any unconnected input ports.
Every input port of all nodes of the generated program should be connected with a parent node.

Also add the the node descriptions in within the program by using the following statement.
graph["nodes"][<node index (represented by the variable in the program during node creation)>]["desc"] = <short explanation of each node based on the function it performs and value it is expected to return>


Here is an example program for adding two constant numbers, where g1 is terminal node identifier of prior program.
g2 = createnode(graph,'K',2);
graph["nodes"][g2]["desc"] = "a constant node with value 2"
g3 = createnode(graph,'K',3)
graph["nodes"][g3]["desc"] = "a constant node with value 3"
g4 = createnode(graph,'+')
g2 = dedupaddlink(graph,g2,g1); ### starting node should connect to any node of the prior program 
g3 = dedupaddlink(graph,g3,g1); ### starting node should connect to any node of the prior program 
g4 = dedupaddlink(graph,g4,g3,g2); 
graph["nodes"][g4]["desc"] = "an addition node that adds 2 with 3"


THE ABOVE PROGRAM IS JUST AN EXAMPLE. DO NOT INCLUDE THIS IN THE FINAL OUTPUT.

You need to generate a program to partially or fully meet the objective provided by user. 
Use the following rules and learnings about the task environment to generate solution program.
  {axioms}

The existing program already does the following. Each line represents a function carried out by a node represented by corresponding node id.
  {programdescription}
  
The generated program should be an extension of this existing program with terminal node identifier {terminalnode}.
Always link only the starting nodes (input ports that are not connected to any other nodes) of the generated program with any of the relevant nodes of the existing program.
If the existing program already fully meets the user specified objective then just output the following statement as generated program.

solved = 'yes'


The output should STRICTLY contain following python dictionary format.
{{"program" :[<list of statements>]
}}

Descriptions should be added for all nodes within the above program. Whereever possible shorten the explanation by evaluating the node outputs.


User : Write a program in FGPM to partially or fully meet the following objective by extending the existing program. You don't need to write the existing program. LIMIT THE PROGRAM LENGHTH ATMOST 10 LINES. IF THE FULL OBJECTIVE CANNOT BE MET WITHIN 10 LINES THEN PARTIALLY SOLVE THE OBJECTIVE IN THE BEST WAY POSSIBLE. FOCUS ON GENERATING CORRECT PROGRAM.
Objective: 
 {objective}

{error}

Lets think step by step.

AI:

"""

#The terminal node of the existing program do the following.
#  {terminalnodedescription}

ACTORPROMPTINPUTVARIABLES = ["functions","axioms","programdescription", "terminalnode","initialnode","objective", "error"]

summarizetext = """System: You are an efficient summarizer of text.
You need to summarize the User provided text within 10 words. The summary should contain all relevant information from user text.

User: {objective}

AI:
"""

SUMMARIZEVARIABLES = ["objective"]

##################################################### with action plan #################################################
# actortemplate = """System: You are a programmer in a new programming model FGPM

# Here are the details of programming model:
# This is a dataflow graph based programming model where programs are represented as directed acyclic graph. The nodes represents operation or function and edges represents data flow.
# A function node can have multiple input ports, each serving as a placeholder for separate input arguments. It can have only one output port that emits the computed output of the function. However multiple edges can emanate from an output port and output value is copied on each output edge. A program can be composed by connecting edges between multiple nodes. Each complete executable program must start with an initial node ("iW") and end with a single terminal node. 
# Every input argument of a node should be connected to another output port of another node.
# Programs are evaluated in lazy style, such that terminal node is excecuted 1st and it calls the functions of its input arguments. This goes on recursively until initial node is reached.

# A function node can be created with the command "createnode(<instance of a graph>,<function name>,<optional paramater>)". It returns a node identifier.
# An edge can be created with the command "addlink(<instance of a graph>,<parent node identifier>,<child node identifier>>)". It returns a edge identifier.

# Here are the list of function names available.
# {functions}

# Here is an example program for adding two constant numbers, where g1 in initial node identifier.
# g2 = createnode(graph,'K',2);
# g3 = createnode(graph,'K',3)
# g4 = createnode(graph,'+')
# addlink(graph,g1); 
# addlink(graph,g2,g1); 
# addlink(graph,g3,g1);
# addlink(graph,g4,g3,g2);
# terminalnode = g4

# The output should be STRICTLY in the following python json format
# Whereever possible shorten the explanation by evaluating the node outputs
# {{"program" :[<list of statements>],
# "desc":[list of short explanation of each node based on the function it performs and value it is expected to return. Each element is a dictionary where key is the node index and value is the description. Explanations should be generated for all nodes. You may assign random node indexes in the explanations. ]
# }}

# You need to generate a program as per the plan provided by user to meet the following objective.
# Objective: 
 # {objective}
 
# The generated program should be an extension of an existing program with terminal node identifier {terminalnode} and initial node identifier {initialnode}. You may link the relevant nodes of the generated program with this terminal node or initial node.

# The existing program already do the following.
  # {programdescription}
  
# The terminal node of the existing program do the following.
  # {terminalnodedescription}


# User : Write a program in FGPM to implement the following plan by extending the existing program. You don't need to write the existing program.

# Plan:
 # {actionplan}

# AI:

# """

#ACTORPROMPTINPUTVARIABLES = ["functions","objective","programdescription", "terminalnode","initialnode","terminalnodedescription","actionplan"]

# actortemplate = """System:  You are part of an AI agent that converts action plan to concrete executable action code in form of python 3 code.
# Try to write a general code so that it can be reused in other actionplans. 
# The action is executed in an external environment. Following is the objective of AI agent in the environment.  Where the objective says your long-term goals, the beliefaxioms are your beliefs on how the enviornment works or responds and the guidelines that needs to be followed to perform an action. 
 # Environment:
        # {beliefenvironment}  

# The actionplan is provided by the user that tries to meet the above environment objective obeying the beliefaxioms.


# You can use the related function modules as reusable functions or combine and/or modify them to create a new action code as per the action plan. Following are the related function code that can be useful in constructing the action code.
# Related function modules:
   # {actions}

# The output should ONLY be in the following SINGLE JSON format PARSABLE in python3. No other text should be there. DO NOT ADD JSON TAGS. It should be a single json record only. Add escape charachters wherever required to make the following a valid json definately.
# {{
  # "name": <a meaningful name of the action not exceeding 7 tokens>,
  # "input parameter" : <required input parameters of the function in the following code. If no parameters are required then keep it blank enclosed with double quotes>, 
  # "output" : <output returned by the function. If no output is returned then keep it blank enclosed with double quotes.>
  # "description" : "<a short description of the action not exceeding 100 tokens>",
  # "code": "<executable python 3 code of the action. The output code should be complete and executable in itself. add escape charachter before double quotes  within the function definition. Should not contain infinite loops. DO NOT use WHILE LOOPS. STRICTLY Don't make up any new function call apart from whatever available in Related function modules. STRICTLY Do not add same functions (or functions with same name) here which are there in requirements below. do not import problemenv or envobject. These are presupplied objects and need not to be imported>",
  # "requirements": "<full function definition code from related function modules, if any to be used in the above code. If no requirements are needed then keep this blank. add escape charachter before double quotes  within the function definition. Do not make up new functions or modify functions. Only exact function definitions from related function modules should be here>",
  # "functioncall": "<entrypoint function name in the above code>(<required argument values. this should not be any variable but an exact value>) if no entrypoint function call is required or entrypoint function is called in above code then keep this blank"
# }}

# The final code is concatenation of "requirements", "code" and "functioncall". Thus both "requirements" and "code" should contain valid python code.
# The final code should not have infinite loops and should run for finite time and halt. 
# The "functioncall" should contain the entrypoint function execution string of "code", if required.

# The structure of the code will be as follows:
# import <any required inbuilt python library>
# <New function defintion with arguments and proper indentation. function body may contain python loops, conditional statements, arithmetic operations, python inbuilt functions,
# logical operations, variable assignments, complex math operations, 
# function calls with appropriate parameters that to related function modules that are defined above.
# Always return the data that you want to send to the main AI agent. 
# The return data can be any data collected from the environment, user , other AI agent or ant specific return data mention in the action plan.
# The above entrypoint function call should not be present here.>

  
# User: Write the action code for the following action plan
# Action plan: 
   # {actionplan}

# {error}

# AI: 
    
# """




# removecodeerror = """System: You are a Python3 code corrector. Based on the log of the code error you modify the code and make sure the code runs successfully.
 
# Here is the algorithm based on which the code has been generated

# """

 
searchertemplate = """System: You are an expert assitant. You are given ACTION OBSERVATION TRACE, a sequence of actions that an agent made in a environment to accomplish a task and the perceptions it got.
A CRITIQUE indicates the success of the attempt to the task.
You need to derive a comprehensive LEARNINGS. Capture all the details in the ACTION OBSERVATION TRACE.
Generate learnings, that will help the agent to successfully accomplish the SAME objective AGAIN, in the SAME environment.
Keep the learning sentences short. Do not use short forms.
Keep fairly novel learnings about the environment and omit very common well known learnings.
Each line can ONLY be of the following forms :
                            X Y Z 

where X and Z are entities, subject, object, events from action perception trace and Y is relation between X and Z. DO NOT add "_" in X, Y or Z. Rogorously capture everything in the action observation trace as memory. COMBINE MULTIPLE LINES into one if either X and Y are same or Y and Z are same.

    
Update on top of the current learnings based on the action observation trace and critique. 
Modify or remove the existing learnings only if it contradicts with  ACTION OBSERVATION TRACE. You can add your new learnings.

The output should always be STRICTLY generated in the following json structure. DO NOT enclose output with JSON TAGS. Add escape charachters wherever required to make the following a valid json definately.
{{  
 "learnings": <list of learnings. DO NOT WRITE REDUNDANT LEARNINGS. DO NOT WRITE CONTRADICTING LEARNINGS>
 }}
    
Here is the environment objective and prior axioms. 
Environment:
    {environment}

Here is the list of current learnings. You should update these learnings.
Learnings:
    {learnings}

User: Here is the action observation trace and critique. Provide the learnings for this.
Action observation trace:
    {EnvTrace}

Critique:
    {critique}  
       
AI:

"""

#Critque:
#       {critique}


SEARCHERPROMPTINPUTVARIABLES = ["environment","learnings","EnvTrace","critique"] #, "critique"


# DEFAULTCRITIQUEOBJECTIVE = """You are a critique of actions taken by an AI agent.
# The actions should satisfy the environment objective. The perceptions from the environment contains the feedback signal about the action.
# Based on the action perception trace and Environment objective provide a positive or negative reinforcement.
# Use the Environment axioms and the previous critique to provide detail reason of the feedback.
# The output should be in the following json format.
# {"feedback": <positive or negative reinforcement. It can be a real number between -1 and 1>,
# "reason": <reason for the feedback> }
# """

# critiquetemplate = """System: {objective}
    
    # Environment objective:
        # {envobjective}
    # Environment axioms:
        # {beliefenvironmentaxioms}
    
    # Previous Critique:
        # {critique}
    
    # Action Perception trace:
       # {ACPtrace}
       
    # AI:  

# """

critiquetemplate = """System: You are a AI critique of actions taken by an autonomous agent who is situated in the following environment.
Environment:
        {beliefenvironment}

The following is an action plan generated for the above environment.   
Action plan:
   {actionplan}
You need to generate a critique for the above action plan. You should provide a positive feedback if the environment response is positive and actionplan meet the environment objective in long term and the actions does not go against the prior axioms or belief axioms (only if belief axioms are not blank). Else you should provide a negative feedback. You provide a neutral feedback if you cannot determine either case.

The following response from the environment may contain the feedback signal about the action.
Environment response:
   {perception}
If the above response contains any feedback or reward signal then update your critique accordingly. Give more importance on environment response for updating the feedback value. If the environment response gives negative feedback then always update the feedback with negative value.

The output should be in the following json format. In no case the output should deviate from the following prescribed format.
{{"reason": <a detailed reason for the feedback based on action plan, environment response (should be given most importance), beliefaxioms (if available) and objective. This should not exceed 50 words> ,
  "feedback": <positive or negative reinforcement. It can be a real number between -1 and 1. If there are reward or feedback present in environment response. Then this should always match with that value>
}}

    
AI:  """

CRITIQUEPROMPTINPUTVARIABLES = ["beliefenvironment", "actionplan", "perception"]


codequivalencetemplate = """System: You are a python code equivalence checker.
If Code 1 and Code 2 are definately semantically equivalent then output True else output False.
    Code 1:
        {code1}
        
    Code 2:
        {code2}
    AI:
"""

CODEEQUIVALENCEVARIABLES = ["code1", "code2"]


planequivalencetemplate = """System:  Determine if the following two plans are algorithmically exactly equal. If they are equal then output True else False. If any one of them is blank then output False

plan 1:
  {historicalactionplan}
  
plan 2:
  {generatedactionplan}
  
Output should be strictly either True or False.

example output:

 example 1:
   True

 example 2:
   False

AI:
"""

PLANEQVVARIABLES = ["historicalactionplan","generatedactionplan"]

EXTRACTLEARNINGS = """System: You are an expert agent that extracts relevant learnings.

User: Extract top 10 learnings from the following list of learnings that are essential to meet the following objective.

Objective:
   {objective}
   
Learnings:
   {learnings}

"""

EXTRACTLEARNVARIABLES = ["objective","learnings"]