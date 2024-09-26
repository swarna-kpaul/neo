from neo.config.keys import *
from neo.config.prompts import *
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts.prompt import PromptTemplate
import os
import re
import ast
import openai
openai.api_key = OPENAIAPIKEY
os.environ["OPENAI_API_KEY"] = OPENAIAPIKEY
client = openai.OpenAI()

def chatpredict(sytemmessage, usermessage = None, model = "gpt-4o", temperature = 0.5):
    if usermessage == None:
        messages=[
        {"role": "system", "content": sytemmessage}
        ]
    else:
        messages=[
        {"role": "system", "content": sytemmessage},
        {"role": "user", "content": usermessage}
        ]      
    response = openai.chat.completions.create(
               model=model,  # or use "gpt-3.5-turbo"
               temperature = temperature,
               timeout=30,
               messages=messages
               )
    return response.choices[0].message.content

# LEARNERSYSTEMPROMPT = PromptTemplate(input_variables=SEARCHERPROMPTINPUTVARIABLES, template=searchertemplate)
# ACTORPROMPT = PromptTemplate(input_variables=ACTORPROMPTINPUTVARIABLES, template=actortemplate)
# ACTPLANPROMPT = PromptTemplate(input_variables=ACTPLANPROMPTINPUTVARIABLES, template=actionplantemplate)
# CRITIQUEPROMPT = PromptTemplate(input_variables=CRITIQUEPROMPTINPUTVARIABLES, template=critiquetemplate)
# CODEEQUIVALENCEPROMPT = PromptTemplate(input_variables=CODEEQUIVALENCEVARIABLES, template=codequivalencetemplate)
# CODEERRORPROMPT = PromptTemplate(input_variables=CODEERRORVARIABLES, template=coderrortemplate)
# #PLANEQUIVALENCEPROMPT = PromptTemplate(input_variables=PLANEQVVARIABLES, template=planequivalencetemplate)
# SUMMARIZEPROMPT = PromptTemplate(input_variables=SUMMARIZEVARIABLES, template=summarizetext)
# SUBTASKPROMPT = PromptTemplate(input_variables=SUBTASKVARIABLES, template=subtasktemplate)
# TEXTSIMILARITYPROMPT = PromptTemplate(input_variables=SIMILARITYVARIABLES, template=textsimilaritytemplate)

def get_embeddings(text,model="text-embedding-3-large"):
    response = client.embeddings.create(input = [text], model=model).data[0].embedding
    return response
    
def summarize(text):
    systemmessage = summarizesystemtext
    usermessage = summarizeusertext.format(objective = text)
    output = chatpredict(systemmessage,usermessage)
    #print("Summarized text:",output)
    return output

def extractdictfromtext(text):
    dict_pattern = re.compile(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', re.MULTILINE | re.DOTALL)
    match = dict_pattern.search(text)
    if match:
        dict_str = match.group(0)
        dict_str = dict_str.strip()
        return ast.literal_eval(dict_str)
    else:
        raise NameError("No dictionary found")
    