from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import os
from config.keys import *
from datetime import datetime
import string
import random
from neo.config.utilities import embeddings_model
from sklearn.metrics.pairwise import cosine_similarity
#from langchain.chat_models import ChatGooglePalm
import uuid


class LTM():  ######### longterm memory - 3 types of memory semantic, episodic and procedural
    def __init__ (self):
        self.memory = {"semantic":{},"episodic": {},"procedural":{}, "externalactions":{}} #record structure --> {id : {"embedding":, "data":} }
        #self.index = pinecone.GRPCIndex(INDEX_NAME)
        #self.dbtype = dbtype
    
    def set(self, text, data, recordid=str(uuid.uuid4()), memorytype = "semantic"):
        embedding = embeddings_model.embed_documents(text) ### get embeddings ############
        ########### update/insert  record
        self.memory[memorytype][recordid] = {"embedding":embedding, "data":data}
    
    
    def get(self,query, memorytype = "semantic", cutoffscore = 0.5 ,top_k=-1):
        queryembedding = embeddings_model.embed_query(query)
        
        sim = [[cosine_similarity([queryembedding], [mem["embedding"]])[0][0],{"data":mem["data"],"id":id}]  for id,mem in self.memory[memorytype].items()]
        top_results = [i for i in top_results if i[0] > cutoffscore]
        if top_k > 0:
            top_results  = sorted(sim, key=lambda item: item[0], reverse=True)[:top_k]
        #top_results = [i[1] for i in top_results]
        return top_results
        
    def fetch(self, recordid, memorytype = "semantic"):
        if recordid in self.memory[memorytype]:
            return self.memory[memorytype][recordid]
        else:
            return False
        
    def delete(self, id, memorytype = "semantic"):
        del self.memory[memorytype][recordid]
        

class STM():  ### Short term memory -- {"conversation": , "timestamp": }
    def __init__ (self,memorysize = DEFAULT_STM_SIZE):
        self.memory = {"critique":{"feedback":-1,"reason":""}, "actionplan":[], "envtrace":[], "state": "","relevantbeliefs":[], "relevantactions":{}}
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
        self.stm[memorytype] = data
        
    def append(self,memorytype,data):
        if memorytype in self.stm:
            self.stm[memorytype].append(data)
        else:
            self.stm[memorytype] = [data]
    
    def delete(self,memorytype):
        if isinstance(self.stm[memorytype]) == list:
            self.stm[memorytype] = []
        elif isinstance(self.stm[memorytype]) == dict:
            self.stm[memorytype] = {}
        else:
            self.stm[memorytype] = ""
    
    
    def get(self, memorytype):
        #if key == "ACPtrace": 
        #    chatdata = [ i['chat'] for i in self.stm[key]]
        #elif key == "currentenv" and not self.stm[key]:
        #    id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        #    return {'id': id, 'env': {}}
        #else:
        data = self.stm[memorytype]
        return data
    
stm = STM()    
ltm = LTM()