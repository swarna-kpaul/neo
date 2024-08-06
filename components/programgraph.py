import math
from neo.environment.bootstrapactions import primitives
from combinatorlite import returnSubgraph, combinatorruntimeerror
import pickle
############ initialize program graph

C = 0.2 ## exploration factor
K = 0.5 ## similarity factor
gamma = 0.3
###### update embeddings of 

def _getprogramdesc(graph,terminalnode, programdesc = [],nodestraversed = []):
    
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraveresed:
                programdesc,nodestraversed = _getprogramdesc(graph,parent_label,programdesc,nodestraversed)
    programdesc.append(graph["nodes"][terminalnode]["desc"])
    nodestraversed.append(parent_label)
    return programdesc,nodestraversed
    
def getprogramdesc(graph,terminalnode, allprogramdesc = {}):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in allprogramdesc:
                allprogramdesc = getprogramdesc(graph,parent_label,allprogramdesc)
    allprogramdesc[terminalnode],_ = _getprogramdesc(graph,terminalnode,[],[])
    allprogramdesc[terminalnode] = '\n'.join(allprogramdesc[terminalnode])
    return allprogramdesc
    
############ update procedural memory for new program with embeddings ############
def updateproceduremem(env,terminalnode):
    allprogramdesc = getprogramdesc(env.graph,terminalnode,{})
    for k,v in allprogramdesc.items():
        if not env.LTM.fetch(k,'procedural') and env.graph["nodes"][k]["es"] ==1: ## memory not present and nodes already executed
            env.LTM.set(v,v,k,'procedural')
            

############ fetch relevant subprograms from procedural memory #################    
def getrelevantnodes(env, query, top_k = 1):
    nodeembeddings = env.LTM.get(query, memorytype = "procedural")   
    nodevalues = {i[1]["id"] : [env.graph["nodes"][i[1]["id"]]["V"],env.graph["nodes"][i[1]["id"]]["EXPF"], i[0]] for i in nodeembeddings}
    nodevalues = [[k,v[0]+C*v[1]+K*v[2]]  for k,v in nodevalues.items()]
    relevantnodes = sorted(nodevalues, key=lambda item: item[1], reverse=True)[:top_k] 
    return relevantnodes
    
def getprogramto_extend(env,query):
    relevantnodes = getrelevantnodes(env, query )
    if not relevantnodes:
        return False,None
    nodeid = relevantnodes[0][0]
    programdesc,_ =  _getprogramdesc(graph,nodeid)
    programdesc =  '\n'.join([v for k,v in sorted(programdesc).items()])
    return nodeid,programdesc

############# fetch external environment trace ##################
def fetchenvtrace(env,terminalnode,envtrace = [], nodestraversed = []):
    graph = env.graph
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if parent_label not in nodestraveresed:
                envtrace,nodestraversed = fetchenvtrace(graph,parent_label,envtrace,nodestraversed)
    if graph["nodes"][terminalnode]["nm"] not in list(primitives.keys()):
    ############ for external functions only
         args = []
         for port,parent_label in parents.items():
             args.append(str(graph["nodes"][parent_label]["dat"]))
         envtrace.append({"action": graph["nodes"][terminalnode]["nm"]+"("+",".join(args)+")", "observation":graph["nodes"][terminalnode]["data"]})
         nodestraversed.append(terminalnode)
    return envtrace,nodestraversed
 
############# Update node values #####################

def updatevalue(env,terminalnode):
    graph = env.graph
    #graph["nodes"][terminalnode]["R"] = reward
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        N = 0
        for port,parent_label in parentnodes.items(): ###### iterate all parents
            if graph["nodes"][parent_label]["V"] < gamma*graph["nodes"][terminalnode]["V"]+ graph["nodes"][parent_label]["R"]:
                graph["nodes"][parent_label]["V"] = gamma*graph["nodes"][terminalnode]["V"] + graph["nodes"][parent_label]["R"]
            N += graph["nodes"][parent_label]["N"]
            updatevalue(graph, parent_label)
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
             updatevalue(env, parent_label)  
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
        output = traceback.format_exc()
        return 0, output
         
     ########## execute graph
    exec_namespace["graph"] =  env.graph
    exec(code,exec_namespace)
    terminalnode = exec_namespace.get("terminalnode", None)
     
    ########## set data as blank for the executing subgraph
    pg.resetdata(env.graph,terminalnode)
    try:
        output = runp(terminalnode,env.graph)
        updateN(env,terminalnode)
    except combinatorruntimeerror as e:
        print(traceback.format_exc())
        errornode = e.errors[0]["nodeid"]
        env.graph["nodes"][errornode]["es"] = 4 
        pg.setfailurenode(env.graph, terminalnode)         
   
    return terminalnode
     
     


