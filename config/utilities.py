from config.keys import *
from config.prompts import *
from langchain.chat_models import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
import os
import re
import ast
from openai import OpenAI
os.environ["OPENAI_API_KEY"] = OPENAIAPIKEY
client = OpenAI()

def get_embeddings(text,model="text-embedding-3-large"):
    response = client.embeddings.create(input = [text], model=model).data[0].embedding
    return response

llm_gpt4_turbo = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-4-1106-preview",openai_api_key=OPENAIAPIKEY)
llm_model = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-3.5-turbo-1106",openai_api_key=OPENAIAPIKEY)
llm_gpt4o = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-4o",openai_api_key=OPENAIAPIKEY)
llm_gpt4o_mini = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-4o-mini",openai_api_key=OPENAIAPIKEY)


#embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAIAPIKEY)
llm_model = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-3.5-turbo-1106",openai_api_key=OPENAIAPIKEY)

#llm_inst_model = OpenAI(temperature=0.7, request_timeout=50, model="gpt-3.5-turbo-instruct",openai_api_key=OPENAIAPIKEY)
#llm_defn_model = OpenAI(temperature=0, request_timeout=50, model="gpt-3.5-turbo-instruct",openai_api_key=OPENAIAPIKEY)
llm_0_4_model = ChatOpenAI(temperature=0.4, request_timeout=30, model="gpt-3.5-turbo",openai_api_key=OPENAIAPIKEY, verbose=True)
llm_gpt4 = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-4-0613",openai_api_key=OPENAIAPIKEY)
llm_gpt4_turbo = ChatOpenAI(temperature=0.7, request_timeout=50, model="gpt-4-1106-preview",openai_api_key=OPENAIAPIKEY)
llm_gpt4_turbo_hightemp = ChatOpenAI(temperature=0.8, request_timeout=50, model="gpt-4-1106-preview",openai_api_key=OPENAIAPIKEY)

LEARNERPROMPT = PromptTemplate(input_variables=SEARCHERPROMPTINPUTVARIABLES, template=searchertemplate)
ACTORPROMPT = PromptTemplate(input_variables=ACTORPROMPTINPUTVARIABLES, template=actortemplate)
ACTPLANPROMPT = PromptTemplate(input_variables=ACTPLANPROMPTINPUTVARIABLES, template=actionplantemplate)
CRITIQUEPROMPT = PromptTemplate(input_variables=CRITIQUEPROMPTINPUTVARIABLES, template=critiquetemplate)
CODEEQUIVALENCEPROMPT = PromptTemplate(input_variables=CODEEQUIVALENCEVARIABLES, template=codequivalencetemplate)
CODEERRORPROMPT = PromptTemplate(input_variables=CODEERRORVARIABLES, template=coderrortemplate)
#PLANEQUIVALENCEPROMPT = PromptTemplate(input_variables=PLANEQVVARIABLES, template=planequivalencetemplate)


def extractdictfromtext(text):
    dict_pattern = re.compile(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', re.MULTILINE | re.DOTALL)
    match = dict_pattern.search(text)
    if match:
        dict_str = match.group(0)
        dict_str = dict_str.strip()
        return ast.literal_eval(dict_str)
    else:
        raise NameError("No dictionary found")
    