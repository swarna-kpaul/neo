from combinatorlite import creategraph, createnode, addlink, worldclass, runp, node_attributes_object
from combinatorlite.bootstrapactions import initworldbootfunctions
import math
node_attributes_object.updateattrib({"R":0,"V":0,"EXPF":0,"N":0,"desc":""}) # R -> reward, V -> value, EXPF -> exploration factor
############ initialize environment

init_world = worldclass(initworldbootfunctions)

############ initialize program graph
graph = creategraph('programgraph')
g1 = createnode(graph,'iW',init_world)
C = 0.2 ## exploration factor
K = 0.5 ## similarity factor

###### update embeddings of 

def _getprogramdesc(graph,terminalnode, programdesc = {}):
    
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parents.items(): ###### iterate all parents
            if parent_label not in programdesc:
                programdesc = _getprogramdesc(graph,parent_label,programdesc)
    programdesc[terminalnode] = graph["nodes"]["desc"]
    return programdesc
    
def getprogramdesc(graph,terminalnode, allprogramdesc = {}):
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parents.items(): ###### iterate all parents
            if parent_label not in allprogramdesc:
                allprogramdesc = getprogramdesc(graph,parent_label,allprogramdesc)
    allprogramdesc[terminalnode] = _getprogramdesc(graph,terminalnode)
    allprogramdesc[terminalnode] = '\n'.join([v for k,v in sorted(allprogramdesc[terminalnode]).items()])
    return allprogramdesc
    
############ update procedural memory for new program with embeddings ############
def updateproceduremem(env,graph,terminalnode):
    allprogramdesc = getprogramdesc(graph,terminalnode)
    for k,v in allprogramdesc.items():
        if not env.LTM.fetch(k,'procedural'): ## memory not present
            env.LTM.set(v,v,k,'procedural')
            

############ fetch relevant subprograms from procedural memory #################    
def getrelevantnodes(env, graph, objective, top_k = 1):
    nodeembeddings = env.LTM.get(objective, memorytype = "procedural")   
    nodevalues = {i[1]["id"] : [graph["nodes"][i[1]["id"]]["V"],graph["nodes"][i[1]["id"]]["EXPF"], i[0]] for i in nodeembeddings}
    nodevalues = [[k,v[0]+C*v[1]+K*v[2]]  for k,v in nodevalues.items()]
    relevantnodes = sorted(nodevalues, key=lambda item: item[1], reverse=True)[:top_k] 
    return relevantnodes
    
    
############# Update node values #####################

def updatevalue(graph,terminalnode):
    #graph["nodes"][terminalnode]["R"] = reward
    if terminalnode in graph['edges']:
        parentnodes = graph['edges'][terminalnode]
        for port,parent_label in parents.items(): ###### iterate all parents
            if graph["nodes"][parent_label]["V"] < gamma*graph["nodes"][terminalnode]["V"]+ graph["nodes"][parent_label]["R"]:
                graph["nodes"][parent_label]["V"] = gamma*graph["nodes"][terminalnode]["V"] + graph["nodes"][parent_label]["R"]
            N += graph["nodes"][parent_label]["N"]
            updatevalue(graph, parent_label)
        graph["nodes"][terminalnode]["EXPF"] = math.sqrt(math.log(N)/graph["nodes"][terminalnode]["N"])
     return

            
            


