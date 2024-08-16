import math
from neo.environment.bootstrapactions import primitives
from combinatorlite import *
import pickle
import ast
############ initialize program graph

C = 0.1 ## exploration factor
K = 0.4 ## similarity factor
X = 0.5 ## value factor
gamma = 0.3
###### update embeddings of 

def getprogramdesc(graph,terminalnode, programdesc = [],nodestraversed = []):
    
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraversed:
                programdesc,nodestraversed = getprogramdesc(graph,parent_label,programdesc,nodestraversed)
    programdesc.append(graph["nodes"][terminalnode]["desc"])
    nodestraversed.append(terminalnode)
    return programdesc,nodestraversed
    
def getallprogramdesc(graph,terminalnode, allprogramdesc = {}):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in allprogramdesc:
                allprogramdesc = getallprogramdesc(graph,parent_label,allprogramdesc)
    allprogramdesc[terminalnode],_ = getprogramdesc(graph,terminalnode,[],[])
    allprogramdesc[terminalnode] = '\n'.join(allprogramdesc[terminalnode])
    return allprogramdesc
    
############ update procedural memory for new program with embeddings ############
def updateproceduremem(env,terminalnode):
    allprogramdesc = getallprogramdesc(env.graph,terminalnode,{})
    for k,v in allprogramdesc.items():
        if not env.LTM.fetch(k,'procedural') and env.graph["nodes"][k]["es"] ==1: ## memory not present and nodes already executed
            env.LTM.set(v,v,k,'procedural')
            

############ fetch relevant subprograms from procedural memory #################    
def getrelevantnodes(env, query, top_k = 1):
    nodeembeddings = env.LTM.get(query, memorytype = "procedural", cutoffscore = 0.1, top_k = 3)   
    nodevalues = {i[1]["id"] : [env.graph["nodes"][i[1]["id"]]["V"],env.graph["nodes"][i[1]["id"]]["EXPF"], i[0]] for i in nodeembeddings}
    nodevalues = [[k,X*v[0]+C*v[1]+K*v[2]]  for k,v in nodevalues.items()]
    relevantnodes = sorted(nodevalues, key=lambda item: item[1], reverse=True)[:top_k] 
    return relevantnodes
    
def getprogramto_extend(env,query):
    relevantnodes = getrelevantnodes(env, query )
    if not relevantnodes:
        return False,None
    env.STM.set("relevantnodes", relevantnodes)
    nodeid = relevantnodes[0][0]
    programdesc,_ =  getprogramdesc(graph,nodeid, programdesc = [],nodestraversed = [])
    programdesc =  '\n'.join(programdesc)
    return nodeid,programdesc

############# fetch external environment trace ##################
def fetchenvtrace(env,terminalnode,envtrace = [], nodestraversed = []):
    graph = env.graph
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraversed:
                envtrace,nodestraversed = fetchenvtrace(env,parent_label,envtrace,nodestraversed)
        if graph["nodes"][terminalnode]["nm"] not in list(primitives.keys()):
    ############ for external functions only
            args = []
            for port,parent_label in parentnodes.items():
                args.append(str(graph["nodes"][parent_label]["dat"]))
            envtrace.append({"action": graph["nodes"][terminalnode]["nm"]+"("+",".join(args)+")", "observation":graph["nodes"][terminalnode]["dat"]})
    nodestraversed.append(terminalnode)
    return envtrace,nodestraversed
 
############# Update node values #####################

def updatevalue(env,terminalnode):
    graph = env.graph
    #graph["nodes"][terminalnode]["R"] = reward
    if graph["nodes"][terminalnode]["V"] == 0.0000001:
       graph["nodes"][terminalnode]["V"] = graph["nodes"][terminalnode]["R"] 
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        N = 0
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if graph["nodes"][parent_label]["V"] < gamma*graph["nodes"][terminalnode]["V"]+ graph["nodes"][parent_label]["R"]:
                graph["nodes"][parent_label]["V"] = gamma*graph["nodes"][terminalnode]["V"] + graph["nodes"][parent_label]["R"]
            N += graph["nodes"][parent_label]["N"]
            updatevalue(env, parent_label)
        graph["nodes"][terminalnode]["EXPF"] = math.sqrt(math.log(N)/graph["nodes"][terminalnode]["N"])
    #return 


############### Reset data ###################

def resetdata(graph,terminalnode):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            resetdata(graph,parent_label)
        graph["nodes"][terminalnode]["dat"] = None
        if graph['nodes'][terminalnode]['es'] != 4:
            graph['nodes'][terminalnode]['es'] = 0
        
def setfailurenode(graph, terminalnode):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        parentfailure = False
        for port,parent_label in parents.items(): ###### iterate all parents
            if graph["nodes"][parent_label]["es"] == 1:
                continue
            elif graph["nodes"][parent_label]["es"] == 0:
                setfailurenode(graph, parent_label)
            if graph["nodes"][parent_label]["es"] == 4:
                parentfailure = True 
        if  parentfailure:
            graph["nodes"][terminalnode]["es"] == 4    

############ update visit node count #################

def updateN(env,terminalnode):
    graph = env.graph
    #graph["nodes"][terminalnode]["R"] = reward
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents   
             updateN(env, parent_label)  
    graph["nodes"][terminalnode]["N"] += 1                

############ execute program #################
def execprogram(env,prevterminalnode, code):
    ########### check syntax of program
    output = None
    graph,_,_ = returnSubgraph(env.graph, prevterminalnode)
    try:
        exec_namespace = globals()
        exec_namespace["graph"] =  graph
        exec(code,exec_namespace)
        terminalnode = exec_namespace.get("terminalnode", None)
    except Exception as e:
        output = "Here is the previous code: \n"+ code+ "\n Here is the error after running the code :\n"+traceback.format_exc()
        return 1, prevterminalnode,output
         
    
    status, errormsg = checkcorrectness(graph,prevterminalnode, terminalnode,env.initnode, code)
    if status == 1:
       errormsg = "Here is the previous code: \n"+ code+ "\n Here is the error after running the code :\n"+ errormsg
       return 1,prevterminalnode,errormsg
     ########## execute graph
    exec_namespace["graph"] =  env.graph
    exec(code,exec_namespace)
    terminalnode = exec_namespace.get("terminalnode", None)
     
    ########## set data as blank for the executing subgraph
    resetdata(env.graph,terminalnode)
    try:
        output = runp(terminalnode,env.graph)
        updateN(env,terminalnode)
    except combinatorruntimeerror as e:
        print(traceback.format_exc())
        errornode = e.error[0]["nodeid"]
        env.graph["nodes"][errornode]["es"] = 4 
        setfailurenode(env.graph, terminalnode)         
   
    return 0,terminalnode,output
     
     

################# check correctness of program
def checkcorrectness(graph,prevterminalnode, terminalnode,initialnode, code):
    errormsg = ""
    status = 0
################# check if graph is broken
    if not [k for k,v in graph["edges"].items() if prevterminalnode in v.values()]:
        ######################### no connection to prevterminalnode
        errormsg += " no nodes of new program is connected to the terminal node identifier of existing program " 
        status = 1
    ##################### broken graph    
    errornodes,_ = checkprogram(graph,terminalnode, initialnode, nodestraversed = [], errornodes = [])
    if errornodes:
        unconnectednodes = []
        for node in errornodes:
            errormsg += "\n all input ports of "+extract_variables_with_value(code, node)[0]+" are not connected."
            status = 1
    ######################### broken node
    danglingnodes = [k for k,v in graph["nodes"].items() if k not in list(graph["edges"].keys()) and k != initialnode]
    for node in danglingnodes:
        errormsg += "\n none of the input ports of "+extract_variables_with_value(code, node)[0]+" are connected."
        status = 1
    
    return status, errormsg
    
    
    

def checkprogram(graph,terminalnode, initialnode, nodestraversed = [], errornodes = []):
    if terminalnode != initialnode:
        parentnodes = graph['edges'][terminalnode]
        if graph['nodes'][terminalnode]['args'] != len(parentnodes): 
        ######## some ports are not connected
            errornodes.append(terminalnode)
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraversed:
                errornodes,nodestraversed = checkprogram(graph,parent_label,initialnode,nodestraversed, errornodes)
    nodestraversed.append(terminalnode)
    return errornodes,nodestraversed


def extract_variables_with_value(code, target_value):
    # Parse the code into an AST
    tree = ast.parse(code)
    
    # Dictionary to store variables and their values
    variables_with_values = {}

    class VariableValueVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            # Check if the right-hand side of the assignment is a constant
            if isinstance(node.value, ast.Constant):
                value = node.value.value
            else:
                # If the value is not a constant, skip (more complex cases can be handled)
                return
            
            # Iterate through targets (left-hand side variables)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables_with_values[target.id] = value

            self.generic_visit(node)

    # Create an instance of the visitor and visit the AST nodes
    visitor = VariableValueVisitor()
    visitor.visit(tree)
    
    # Filter variables that match the target value
    matching_variables = [var for var, val in variables_with_values.items() if val == target_value]
    
    return matching_variables
