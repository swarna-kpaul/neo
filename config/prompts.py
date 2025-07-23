textsimilaritysystemtemplate = """You are a text similarity checker.
Give the output in strictly following format
{"result": <True or False (python boolean value).>}

"""

textsimilarityusertemplate = """Are the following two objective same?
objective 1: {text1}
objective 2: {text2}

"""
SIMILARITYSYSTEMVARIABLES = []
SIMILARITYUSERVARIABLES = ["text1","text2"]

subtasksystemtemplate = """You need to break a large complex task into multiple sequential sutasks. 
Try to break the task into atomic tasks and keep the number of subtasks as minimum as possible. 
Do not generate unnecessary ambigous subtasks.
Generate the subtasks in such a way so that solving all of them sequentially solves the original task.
Do not add texts like "Subtask 1" or "step 1" etc. in the any subtask description

If the task is simple and short then you dont need to break the task instead return the same task as only subtask.

Keep the axioms about the problem environment in consideration while breaking the task
 Axioms:
 {axioms}
 
 Here are the list of available functions. Create the subtasks such that it can be solved with one or many of the available functions.
  {functions}

The output should be STRICTLY in following format.
{{<unique integer id of a subtask> : {{ "task": "description of subtask", "dependencies": [<integer id of dependent subtasks>]}} }}

"""
subtaskusertemplate = """ Generate the subtasks for the following task
 {task}"""


SUBTASKSYSTEMVARIABLES = ["axioms"]
SUBTASKUSERVARIABLES = ["task"]


findsubtasksystemtemplate = """You need to find the next subtask for solving a large complex task, given a set of subtasks have already been solved.
Do not generate unnecessary, trivial and ambigous subtasks.
Generate the subtask in such a way so that solving it makes some progress in solving the overall task.
Do not add texts like "Subtask 1" or "step 1" etc. in the any subtask description

If the task is simple and short then you dont need to break the task instead return the same task as only subtask.

Keep the axioms about the problem environment in consideration while breaking the task
 Axioms:
 {axioms}
 
 Here are the list of available functions. Create the subtasks such that it can be solved with one or many of the available functions.
  {functions}

The output should be STRICTLY in following format.
{{<unique integer id of the subtask> : {{ "task": "description of subtask", "dependencies": [<integer id of dependent(already solved) subtasks>. This should be strictly taken from the list of already solved subtasks]}} }}

"""
findsubtaskusertemplate = """ Generate the next subtasks for the following task. DO NOT generate multiple subtasks
 {task}
 
 Here are subtasks already solved for solving this task.
 {subtasks}
 """


FINDSUBTASKSYSTEMVARIABLES = ["axioms"]
FINDSUBTASKUSERVARIABLES = ["task","subtask"]


actortsystemtemplate = """You are a programmer in a new programming model FGPM

Here are the details of programming model:
This is a dataflow graph based programming model where programs are represented as directed acyclic graph. The nodes represents operation or function and edges represents data flow.
A function node can have multiple input ports, each serving as a placeholder for separate input arguments. It can have only one output port that emits the computed output of the function. However multiple edges can emanate from an output port and output value is copied on each output edge. 
A program can be composed by connecting edges between multiple nodes. 
Every input argument of a node should be connected to another output port of another node.
Each complete executable program must end with a single node called as terminalnode.  

Programs are evaluated in lazy style, such that terminal node is excecuted 1st and it calls the functions of its input arguments. This goes on recursively until initial node is reached.

A function node can be created with the command "createnode(<instance of a graph>,<function name>,<optional paramater only applicable for constant node>)". It returns a node identifier.
An edge can be created with the command "dedupaddlink(<instance of a graph>,<child node identifier>,<parent node identifiers in representing input arguments for child node>)". It returns the child node identifier.

Here are the list of function names available.
{functions}


There should not be any unconnected input ports.
Every input port of all nodes of the generated program should be connected with a parent node.

Also add the the node descriptions within the program for each node after connecting the node with its parents by using the following statement.
graph["nodes"][<node index (represented by the variable in the program during node creation)>]["desc"] = <short explanation of each node based on the function it performs and value it is expected to return based on its parent node connections>


Here is an example program for adding two constant numbers, where g1 is terminal node identifier of prior program.
g2 = createnode(graph,'K',2);
g3 = createnode(graph,'K',3)
g4 = createnode(graph,'+')
g2 = dedupaddlink(graph,g2,g1); ### starting node should connect to any node of the prior program 
graph["nodes"][g2]["desc"] = "a constant node with value 2"
g3 = dedupaddlink(graph,g3,g1); ### starting node should connect to any node of the prior program 
graph["nodes"][g3]["desc"] = "a constant node with value 3"
g4 = dedupaddlink(graph,g4,g3,g2); 
graph["nodes"][g4]["desc"] = "an addition node that adds 2 with 3"
terminalnode = g4 ### the final node identifier executing which would execute the entire program

THE ABOVE PROGRAM IS JUST AN EXAMPLE. DO NOT INCLUDE THIS IN THE FINAL OUTPUT.

You need to generate a program to partially or fully meet the objective provided by user. 
Strictly Use the following axioms to generate solution program.
  {axioms}

Also you may use the following learnings.
  {learnings}

The existing program already does the following. Each line represents a function carried out by a node represented by corresponding node id.
  {programdescription}


Here are some of the other nodes that might help with the objective.
   {helpernodes}
  
The generated program should be an extension of this existing program with terminal node identifier {terminalnode}.
The terminalnode variable in the generated program should contain the node identifier of the node, running which would solve the user objective. 
Always link only the starting nodes (input ports that are not connected to any other nodes) of the generated program with any of the relevant nodes of the existing program.

If the existing program (or a section of the existing program) already fully meets the user specified objective then just output the following statement as generated program.

terminalnode = <identifier of the node from the existing program, running which would solve the user objective>


The output should STRICTLY contain following python dictionary format.
{{"program" :[<list of statements>]
}}

Descriptions should be added for all nodes within the above program. Whereever possible shorten the explanation by evaluating the node outputs.


"""

actorusertemplate = """Write a program in FGPM to partially or fully meet the following objective by extending the existing program. You don't need to write the existing program. LIMIT THE PROGRAM LENGHTH ATMOST 10 LINES. IF THE FULL OBJECTIVE CANNOT BE MET WITHIN 10 LINES THEN PARTIALLY SOLVE THE OBJECTIVE IN THE BEST WAY POSSIBLE. FOCUS ON GENERATING CORRECT PROGRAM.

Objective: Solve the following subtask of the task. 
  Subtask : {subtask}
  Task: {task}
  
  {solvedsubtasks}
 
{error}

Lets think step by step.

"""

ACTORPROMPTSYSTEMVARIABLES = ["functions","axioms","learnings","programdescription","helpernodes", "terminalnode","initialnode"]
ACTORPROMPTUSERVARIABLES = ["subtasks","objective", "error"]

summarizesystemtext = """Summarize the following user text denoting the main objectives and keeping all relevant information. Do not add any prefix or suffix text.

"""
summarizeusertext ="""{objective}
"""
SUMMARIZESYSTEMVARIABLES = []
SUMMARIZEUSERVARIABLES = ["objective"]


critiquesystemtemplate = """You are a AI critique of actions taken by an autonomous agent who is situated in the following environment.
Environment:
        {beliefenvironment}

The following is an action plan generated for the above environment.   
Action plan:
   {actionplan}
   
You need to generate a critique for the above action plan. Obey the following rules in sequence to generate the feedback.
   - If the environment explicity provides reward signal.
       - then use the same as feedback normalized within -1 to 1
   - else if the agent has followed the correct action plan and still the objective is not met due to some challenges in the environment condition itself and there is nothing that can be done from the agent perspective to meet the goal
       - then provide a postive feedback. 
   - else if the environment response is positive and actionplan meet the environment objective in long term and the actions does not go against the prior axioms or belief axioms (only if belief axioms are not blank)
       - then provide a positive feedback 
   - else if you cannot determine if positive or negative feedback needs to be given 
       - then provide a neutral feedback
   - else if none of the above conditions are true
       - provide negative feedback

The following response from the environment may contain the feedback signal about the action.
Environment response:
   {perception}

The output should be in the following json format. In no case the output should deviate from the following prescribed format.
{{"reason": <a detailed reason for the feedback based on action plan, environment response (should be given most importance), axioms (if available) and objective. This should not exceed 50 words> ,
  "feedback": <positive or negative reinforcement. It can be a real number between -1 and 1. If there are reward or feedback present in environment response. Then this should always match with that value>
}}

    
AI:  """

critiqueusertemplate = """
"""
CRITIQUEPROMPTUSERVARIABLES = []
CRITIQUEPROMPTSYSTEMVARIABLES = ["beliefenvironment", "actionplan", "perception"]


istasksolvedtemplate = """You determine if the complete task is solved or not based on the following subtasks
Task : {task}

Subtasks solved: {subtasks}
You should output in the following format

{{"reason": <True/False>}}

"""




learnersystemtemplate = """You are an expert assitant. You are given ACTION OBSERVATION TRACE, a sequence of actions that an agent made in a environment to accomplish a task and the perceptions it got.
A CRITIQUE indicates the success of the attempt to the task.
You need to derive a comprehensive LEARNINGS. Capture all the details in the ACTION OBSERVATION TRACE.
Generate learnings, that will help the agent to successfully accomplish the SAME objective AGAIN, in the SAME environment.
Keep the learning sentences as short as possible.
Keep fairly novel learnings about the environment and omit very common well known learnings.
DO NOT WRITE REDUNDANT LEARNINGS.
   
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

"""

learnerusertemplate = """Here is the action observation trace and critique. Provide the learnings for this.
  Action observation trace:
    {EnvTrace}

  Critique:
    {critique}  
"""

LEARNERPROMPTSYSTEMVARIABLES = ["environment","learnings","EnvTrace","critique"] #, "critique"
LEARNERPROMPTUSERVARIABLES = ["environment","learnings"]


updatesolvedtaskdescriptiontemplate = """Update the following description of the goal that is solved by an agent based on the user feedback given. 
Update only if there are contradictions in the description with respect to the feedback.
Do not remove any functionality from the description about which nothing is written in the feedback
Do not modify any functionality from the description about which somethinf is written in the feedback but it does not negatively contradicts
output only the updated description

description: 
   {description}
   
feedback:
   {feedback}

"""