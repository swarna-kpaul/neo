from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import os
from config.keys import *
from datetime import datetime
import string
import random
from neo.config.utilities import get_embeddings
from sklearn.metrics.pairwise import cosine_similarity
#from langchain.chat_models import ChatGooglePalm
import uuid


class LTM():  ######### longterm memory - 3 types of memory semantic, episodic and procedural
    def __init__ (self):
        self.memory = {"semantic":{},"episodic": {},"procedural":{}, "externalactions":{}} #record structure --> {id : {"embedding":, "data":} }
        #self.index = pinecone.GRPCIndex(INDEX_NAME)
        #self.dbtype = dbtype
    
    def set(self, text, data, recordid=str(uuid.uuid4()), memorytype = "semantic"):
        embedding = get_embeddings(text) ### get embeddings ############
        ########### update/insert  record
        self.memory[memorytype][recordid] = {"embedding":embedding, "data":data}
    
    
    def get(self,query, memorytype = "semantic", cutoffscore = 0.1 ,top_k=-1):
        queryembedding = get_embeddings(query)
        
        sim = [[cosine_similarity([queryembedding], [mem["embedding"]])[0][0],{"data":mem["data"],"id":id}]  for id,mem in self.memory[memorytype].items()]
        top_results = [i for i in sim if i[0] > cutoffscore]
        if top_k > 0:
            top_results  = sorted(top_results, key=lambda item: item[0], reverse=True)[:top_k]
        #top_results = [i[1] for i in top_results]
        return top_results
        
    def fetch(self, recordid, memorytype = "semantic"):
        if recordid in self.memory[memorytype]:
            return self.memory[memorytype][recordid]
        else:
            return False
        
    def delete(self, recordid, memorytype = "semantic"):
        del self.memory[memorytype][recordid]
        

class STM():  ### Short term memory -- {"conversation": , "timestamp": }
    def __init__ (self,memorysize = DEFAULT_STM_SIZE):
        self.memory = {"critique":{"feedback":-1,"reason":""}, "actionplan":[], "envtrace":[], "state": "","relevantnodes":[], "relevantactions":{}}
        self.memorysize = memorysize
        
    def set(self,memorytype,data):
        #if key == "ACPtrace": 
        #    if len(stmobj) >= self.memorysize:
        #        del stmobj[0]
        #    data["actionplan"]
        #    stmobj.append({"chat": data , "time" : datetime.now()})
            ## update cumulative rewards
            #stmobj = [{"chat": {"actionplan": {"planid": ACP["chat"]["actionplan"]["planid"], "actionplan": ACP["chat"]["actionplan"]["actionplan"], "requiredactions":  ACP["chat"]["actionplan"]["requiredactions"], "cumulative reward": data["actionplan"]["cumulative reward"] if ACP["chat"]["actionplan"]["planid"] == data["actionplan"]["planid"] else ACP["chat"]["actionplan"]["cumulative reward"]} , "perception":ACP["chat"]["perception"], "feedback": ACP["chat"]["feedback"]}, "time": ACP["time"]} for ACP in stmobj ]
        #elif key == "EnvTrace":
        #    if len(stmobj) >= self.memorysize:
        #        del stmobj[0]
        #    stmobj.append({"chat": data , "time" : datetime.now()})                
        #else:
        #    stmobj = data
        self.memory[memorytype] = data
        
    def append(self,memorytype,data):
        if memorytype in self.memory:
            self.memory[memorytype].append(data)
        else:
            self.memory[memorytype] = [data]
    
    def delete(self,memorytype):
        if isinstance(self.memory[memorytype]) == list:
            self.memory[memorytype] = []
        elif isinstance(self.memory[memorytype]) == dict:
            self.memory[memorytype] = {}
        else:
            self.memory[memorytype] = ""
    
    
    def get(self, memorytype):
        #if key == "ACPtrace": 
        #    chatdata = [ i['chat'] for i in self.memory[key]]
        #elif key == "currentenv" and not self.memory[key]:
        #    id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        #    return {'id': id, 'env': {}}
        #else:
        data = self.memory[memorytype]
        return data
    
stm = STM()    
ltm = LTM()