import math
from neo.environment.primitives import primitives
from combinatorlite import *
from neo.config.utilities import summarize
import pickle
import ast
############ initialize program graph

C = 0.1 ## exploration factor
K = 0.5 ## similarity factor
X = 0.4 ## value factor
gamma = 0.9
MAXPROGLENGTH = 10
###### update embeddings of 

def getprogramdesc(graph,terminalnode, programdesc = [],nodestraversed = []):
    
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraversed:
                programdesc,nodestraversed = getprogramdesc(graph,parent_label,programdesc,nodestraversed)
    programdesc.append((graph["nodes"][terminalnode]["desc"],terminalnode))
    nodestraversed.append(terminalnode)
    return programdesc,nodestraversed
    
def getallprogramdesc(graph,terminalnode, allprogramdesc = {}):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in allprogramdesc:
                allprogramdesc = getallprogramdesc(graph,parent_label,allprogramdesc)
    allprogramdesc[terminalnode],_ = getprogramdesc(graph,terminalnode,[],[])
    allprogramdesc[terminalnode] = [desc for desc,nodeid in allprogramdesc[terminalnode]]
    allprogramdesc[terminalnode] = '\n'.join(allprogramdesc[terminalnode])
    return allprogramdesc
    
############ update procedural memory for new program with embeddings ############
def updateproceduremem(env,terminalnode):
    allprogramdesc = getallprogramdesc(env.graph,terminalnode,{})
    for k,v in allprogramdesc.items():
        
        if not env.LTM.fetch(k,'procedural') and env.graph["nodes"][k]["es"] ==1: ## memory not present and nodes already executed
            progsummary = summarize(v)
            env.LTM.set(progsummary,progsummary,k,'procedural')
            

############ fetch relevant subprograms from procedural memory #################    
def getrelevantnodes(env, query, top_k = 1,C=C,K=K,X=X):
    nodeembeddings = env.LTM.get(query, memorytype = "procedural", cutoffscore = 0.1, top_k = 10)   
    nodevalues = {i[1]["id"] : [env.graph["nodes"][i[1]["id"]]["V"],env.graph["nodes"][i[1]["id"]]["EXPF"], i[0]] for i in nodeembeddings}
    nodevalues = [[k,X*v[0]+C*v[1]+K*v[2]]  for k,v in nodevalues.items()]
    relevantnodes = sorted(nodevalues, key=lambda item: item[1], reverse=True)[:top_k] 
    return relevantnodes
    
def getprogramto_extend(env,query, subtasks):
    graph = env.graph
    relevantnodes = getrelevantnodes(env, query )  
    if not relevantnodes:
        return False,None,None
    env.STM.set("relevantnodes", relevantnodes)
    nodeid = relevantnodes[0][0]
    programdesc,_ =  getprogramdesc(graph,nodeid, programdesc = [],nodestraversed = [])
    priorprogramdesc = ""
    if len(programdesc) > MAXPROGLENGTH:
        priorprogramdesc = programdesc[:len(programdesc) - MAXPROGLENGTH]
        priorprogramdesc = summarize('\n'.join([desc for desc,idx in priorprogramdesc]))
        programdesc = programdesc[len(programdesc) - MAXPROGLENGTH :]
        
    taskprogramnodeids = [idx for desc,idx in programdesc]
    
    ######## get subtask nodes
    subtaskrelevantnodes = []
    for subtask in subtasks:
        relevantnode = getrelevantnodes(env, subtask,top_k = 1,C=0.1,K=0.7,X=0.2)
        if relevantnode:
            if relevantnode[0][0] not in taskprogramnodeids:
                subtaskrelevantnodes.append( graph["nodes"][relevantnode[0][0]]["desc"] +"; node id -> "+str(relevantnode[0][0]))   
    subtaskrelevantnodes = "\n".join(subtaskrelevantnodes)
    
    programdesc = [desc+"; node id -> "+str(idx) for desc,idx in programdesc]
    programdesc =  '\n'.join(programdesc)
    programdesc = priorprogramdesc+"\n"+programdesc
    return nodeid,programdesc,subtaskrelevantnodes

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
                if len(str(graph["nodes"][parent_label]["dat"])) > 100:
                    args.append(str(graph["nodes"][parent_label]["dat"])[0:100])
                else:
                    args.append(str(graph["nodes"][parent_label]["dat"]))
            if len(str(graph["nodes"][terminalnode]["obs"])) > 100:
                obs = graph["nodes"][terminalnode]["obs"][0:100]
            else:
                obs = graph["nodes"][terminalnode]["obs"]
            envtrace.append({"action": graph["nodes"][terminalnode]["desc"]+" with inputs ("+",".join(args)+")", "observation":obs})
    nodestraversed.append(terminalnode)
    return envtrace,nodestraversed

############# Update node values #####################

def updatevalue(env,terminalnode,finalnode = False):
    graph = env.graph
    #graph["nodes"][terminalnode]["R"] = reward
    if graph["nodes"][terminalnode]["nm"] != "iW" and terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        ###### iterate all parents
        parentvalues = []
        N = 0
        for port,parent_label in parentnodes.items(): 
            updatevalue(env, parent_label, False)
            N += graph["nodes"][parent_label]["N"]
            parentvalues.append( graph["nodes"][parent_label]["V"])
        allchildvalues = [graph["nodes"][k]["V"] for k,v in graph["edges"].items() if terminalnode in v.values()]
        if allchildvalues:
            avgvalue = (max(allchildvalues) + max(parentvalues))/2
        else:
            avgvalue = max(parentvalues)
            
        graph["nodes"][terminalnode]["V"] = gamma*avgvalue + graph["nodes"][terminalnode]["R"] #/rewardpenalty   
        graph["nodes"][terminalnode]["EXPF"] = math.sqrt(math.log(N)/graph["nodes"][terminalnode]["N"])


############# Update node values #####################

# def updatevalue(env,terminalnode,finalnode = False):
    # graph = env.graph
    # #graph["nodes"][terminalnode]["R"] = reward
    # if graph["nodes"][terminalnode]["nm"] != "iW":
           # allchildnodes = [k for k,v in graph["edges"].items() if terminalnode in v.values()]
           # if allchildnodes:
               # maxchildvalue = max([ graph["nodes"][node]["V"] for node in allchildnodes])
           # else:
               # maxchildvalue = 0
           # if graph["nodes"][terminalnode]["N"] > 1:
               # rewardpenalty = math.log2(graph["nodes"][terminalnode]["N"])
           # else:
               # rewardpenalty = 1
           # graph["nodes"][terminalnode]["V"] = gamma*maxchildvalue + graph["nodes"][terminalnode]["R"] #/rewardpenalty
           
    # if terminalnode in graph['edges']:
        # parentnodes = graph['edges'][terminalnode]
        # N = 0
        # for port,parent_label in parentnodes.items(): ###### iterate all parents
            # N += graph["nodes"][parent_label]["N"]
            # updatevalue(env, parent_label, False)
            
        
        # graph["nodes"][terminalnode]["EXPF"] = math.sqrt(math.log(N)/graph["nodes"][terminalnode]["N"])
    # #return 

##################################
def dedupaddlink(graph,childnode,*parentnodes):
    ########### check self loop ############
    if childnode in parentnodes:
        
        raise NameError("a self loop is not allowed in node link")
    ############ check if same childnode exists with same parents ############
    for dedupnodeid in [dedupnodeid for dedupnodeid, node in graph["nodes"].items() if graph["nodes"][childnode]["nm"] == node["nm"]]:
        if graph["nodes"][childnode]["nm"] == "K": 
            if graph["nodes"][childnode]["K"] != graph["nodes"][dedupnodeid]["K"]:
                continue
        if dedupnodeid in graph["edges"]:
            if list(graph["edges"][dedupnodeid].values()) == list(parentnodes):
                ################# same node exists
                ########## reconnect all childnodes of childnode if any
                for childid, edges in graph["edges"].items():
                    for port,parentid in edges.items():
                        if parentid == childnode:
                            graph["edges"][childid][port] = dedupnodeid
                ############ delete childnode #######
                remove_node(graph,childnode)
                #childnode = dedupnodeid
                return dedupnodeid
    ########### delete existing edges of childnode
    if childnode in graph["edges"]:
        del graph["edges"][childnode]
    addlink(graph,childnode,*parentnodes)           
    return childnode

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
        #graph = exec_namespace.get("graph", None)
        #terminalnode = list(graph["terminalnodes"].keys())[0]
    except Exception as e:
        tb = traceback.format_exc().splitlines()
        tb = [x.strip() for x in tb]
        tb = tb[tb.index("exec(code,exec_namespace)")+1:]
        tb = "\n".join(tb)
        output = "Here is the previous code: \n"+ code+ "\n\n Here is the error after running the previous code :\n"+ tb + "\n\n MAKE SURE TO CORRECT THE ERROR AT ALL COST"
        return 1, prevterminalnode,output
         
    ################ check FGPM correctness
    #namespace = globals()
    terminalnodes = list(graph["terminalnodes"].keys())
    if terminalnodes:
        terminalnode = terminalnodes[0]
    else:
        terminalnode = prevterminalnode
    
    status, errormsg = checkcorrectness(graph,prevterminalnode, terminalnode,env.initnode, code, exec_namespace)
    if status == 1:
       errormsg = "Here is the previous code: \n"+ code+ "\n\n Here is the error after running the code :\n"+ errormsg
       return 1,prevterminalnode, errormsg
       
     ########## execute graph
    exec_namespace["graph"] =  env.graph
    exec(code,exec_namespace)
    ############ get terminalnode
    terminalnodes = list(env.graph["terminalnodes"].keys())
    allvariablenames = extract_variable_names(code)
    terminalnode = prevterminalnode
    for _terminalnode in terminalnodes:
        if check_variables_in_globals(allvariablenames, _terminalnode,exec_namespace):
            terminalnode = _terminalnode
            break
    #terminalnode = exec_namespace.get("terminalnode", None)
     
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
    
    for var in allvariablenames:
        del var
    return 0,terminalnode,output
     
     
def detectloop(graph,terminalnode,childnodes = [],loopcon = []):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        childnodes.append(terminalnode)
        for port,parent_label in parentnodes.items():
            if parent_label in childnodes:
                loopcon.append((terminalnode,parent_label))
            childnodes,loopcon=detectloop(graph,parent_label,childnodes,loopcon)
        return childnodes,loopcon
    else:
        return [],loopcon

################# check correctness of program
def checkcorrectness(graph,prevterminalnode, terminalnode,initialnode, code, exec_namespace):
    errormsg = ""
    status = 0
################# check if graph is broken
    programdesc,_ =  getprogramdesc(graph,prevterminalnode, programdesc = [],nodestraversed = [])
    prevprogramnodeids = list(set([idx for desc,idx in programdesc if idx != terminalnode]))
    allparentnodes = [list(v.values()) for k,v in graph["edges"].items()]
    allparentnodes = list(set([item for sublist in allparentnodes for item in sublist]))
    
    if not list(set(prevprogramnodeids).intersection(allparentnodes)): #[k for k,v in graph["edges"].items() if prevterminalnode in v.values()] and prevterminalnode != terminalnode 
        ######################### no connection to prevterminalnode
        errormsg += " NO NODES OF NEW PROGRAM IS CONNECTED TO THE ANY NODE OF EXISTING PROGRAM " 
        status = 1
    ##################### broken graph   
    allvariablenames = extract_variable_names(code)    
    errornodes,_ = checkprogram(graph,terminalnode, initialnode, nodestraversed = [], errornodes = [])
    if errornodes:
        unconnectednodes = []
        for node,args,connected in errornodes:
            errormsg += "\n"+check_variables_in_globals(allvariablenames, node,exec_namespace)[0]+" TAKES "+ str(args)+" INPUT ARGUMENTS, BUT THERE ARE "+str(connected)+" INPUT CONNECTIONS."
            status = 1
    ######################### broken node
    danglingnodes = [k for k,v in graph["nodes"].items() if k not in list(graph["edges"].keys()) and k != initialnode]
    for node in danglingnodes:
        errormsg += "\n NONE OF THE INPUT PORTS OF "+check_variables_in_globals(allvariablenames, node,exec_namespace)[0]+" ARE CONNECTED."
        status = 1
    
    ######################### check for multiple terminalnodes ##############
    nodeids = [exec_namespace[var] for var in allvariablenames if var in exec_namespace]
    allparentids = [v.values() for k,v in graph["edges"].items()] 
    uniqueelements = lambda lol: list(set([item for sublist in lol for item in sublist]))
    allparentids = uniqueelements(allparentids)
    
    terminalnodes = list(set([node for node in nodeids if node not in allparentids]))
    if len(terminalnodes) > 1:
    ######## multiple terminal nodes
        errormsg += "\n"+', '.join([check_variables_in_globals(allvariablenames, node,exec_namespace)[0] for node in terminalnodes ])+ " ARE MULTIPLE TERMINAL NODES CREATED BY THE PROGRAM. THERE SHOULD BE ONLY A SINGLE TERMINAL NODE SUCH THAT ALL OTHER NODES SHOULD HAVE AT LEAST A CHILD NODE."
        status = 1
    errormsg += "\n\n MAKE SURE TO CORRECT THE ABOVE ERROR AT ALL COST"
    
    ######## check if there are parent node of initial node
    if initialnode in graph["edges"]:
        parentnodes = list(graph["edges"][initialnode].values())
        errormsg += "\n"+', '.join([check_variables_in_globals(allvariablenames, node,exec_namespace)[0] for node in parentnodes])+" ARE NODES INCORRECTLY CONNECTED AS PARENT NODES OF INITIAL NODE. INTIAL NODE SHOULD NOT HAVE ANY PARENT NODES"
    
    ######## check for cycles ############
    
    
    
    return status, errormsg
    
    
    

def checkprogram(graph,terminalnode, initialnode, nodestraversed = [], errornodes = []):
    if terminalnode != initialnode:
        if terminalnode in graph['edges']:
            parentnodes = graph['edges'][terminalnode]
            if graph['nodes'][terminalnode]['args'] != len(parentnodes): 
        ######## some ports are not connected
                errornodes.append((terminalnode,graph['nodes'][terminalnode]['args'],len(parentnodes)))
            for port,parent_label in parentnodes.items(): ###### iterate all parents
                if parent_label not in nodestraversed:
                    errornodes,nodestraversed = checkprogram(graph,parent_label,initialnode,nodestraversed, errornodes)
    nodestraversed.append(terminalnode)
    return errornodes,nodestraversed


def extract_variable_names(code):
    # Parse the code into an AST
    tree = ast.parse(code)
    
    # Set to store variable names
    variable_names = set()

    class VariableNameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            # If the node is a variable being assigned (Store context), add its name
            if isinstance(node.ctx, ast.Store):
                variable_names.add(node.id)
            self.generic_visit(node)

    # Create an instance of the visitor and visit the AST nodes
    visitor = VariableNameVisitor()
    visitor.visit(tree)
    
    return variable_names
    
def check_variables_in_globals(variable_names, target_value,exec_namespace):
    # Find variables in globals that match the target value
    matching_variables = [var for var in variable_names if var in exec_namespace and exec_namespace[var] == target_value]
    #if not matching_variables:
    #    matching_variables = [""]
    return matching_variables



