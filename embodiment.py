from searcher import *


def neosolvercreator(bootstrapenv = None, problemenv = None, stmloadfile = None, stmstoragefile = "./stm.pickle"):
    if bootstrapenv == None and problemenv == None:
        neoenvobj = neoenv()
    elif problemenv == None:
        neoenvobj = neoenv(bootstrapenv)
    elif bootstrapenv == None:
        neoenvobj = neoenv(problemenv = problemenv)   
    else:
        neoenvobj = neoenv(bootstrapenv, problemenv)       

    
    neosolver = neo(neoenvobj,stmloadfile, stmstoragefile, STMsize = 4 )
    return neosolver