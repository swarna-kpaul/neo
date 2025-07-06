import sys
from neo.config.keys import *
from neo.config.utilities import chatpredict
from neo.environment.sciworld import scienv_obj

#from neo.environment.envtemplate import *
#from langchain.utilities import BingSearchAPIWrapper
import os
import traceback
#from langchain.chat_models import ChatOpenAI
import requests
import ast
import wave
import base64
import io
import numpy as np
import pickle
from PIL import Image
import imageio

   
#### get explicit env feedback 
def getenvfeedback(env):
    return scienv_obj.getfeedback()
    #return input("Enter your explicit feedback if any: ")


#### get explicit env feedback 
def getenvstate(env):
    return scienv_obj.getstate()
    #return input("Enter your explicit feedback if any: ")


################## Get user text input ####################
def textdataread(env,display_message = ""):
    text = input(display_message)
    return text,"The user has entered the following text : "+text

################## Show text output to user ##################
def textshow(env,message):
    print(message)
    return "","The message "+str(message)+" has been displayed"

################## Ask any question to gpt #############
def askgpt(env,question):
    print("askgpt question: ", question)
    output = chatpredict(question)
    return output,output

################# Ask question on specific context to gpt and return output in specfic data type
def getanswer(env,question,text,outputdatatype):
    systemprompt = """You are an intelligent agent that can answer user questions based on the given context. Give to the point exact answer. THE OUTPUT SHOULD BE STRICTLY A PYTHON"""+outputdatatype.upper()+""" FORMAT. Incase the output is not a"""+outputdatatype.upper()+""" return NAN \n\n context:\n"""+text+"""\nAnswer the following question from the above context without considering any other prior information."""
    userprompt = question
    output = chatpredict(systemprompt,userprompt)
    if output == "NAN":
        return "","No output"
    elif outputdatatype in ["number","boolean","list","dictionary"]:
        return ast.literal_eval(output),output
    else:
        return output,output


def take_sci_action(env,action_text):
    obs,reward = scienv_obj.act(action_text)
    message = f"Observation: {obs} \n Reward:{str(reward)}"
    return obs,message

    
#################################### describe external function set ###############################
extfunctionset = {"textdataread": {"description": """A function to read text data that should be typed by the user through standard input. """,
                     "function": textdataread,
                     "input": " It has one input port that should take a text message that needs to be displayed to the user. ",
                     "output": "Returns the text data that user has typed.",
                     "args": 1,
                     "type": {'fun':{'i':['any'],'o':['text']}}},
                  "textshow": {"description": "A function to display or print a message to the user on standard output.",
                     "function": textshow,
                     "input": "One input port that takes a text message that should be displayed to the user. ",
                     "output": "Returns a text that states required message has been displayed.",
                     "type": {'fun':{'i':['any'],'o':['any']}},
                     "args": 1},
                   "askgpt":  {"description": """A function (named askgpt) to provide answer to general questions using GPT3.5 LLM. It can also provide output in code or structured format like, json yaml etc. if properly prompted to do so. """,
                     "function": askgpt,
                     "input": "It has one input port that takes one input question or prompt in plaintext. ",
                     "output": "Returns answer in plaintext.",
                     "type": {'fun':{'i':['any'],'o':['text']}},
                     "args": 1},
                  "getanswer":   {"description": """Get precise answer to a question based on a given text. The answer is given in the expected datatype. The output datatype can be number, boolean, list, dictionary and text. For getting a structured answer for a question on a given context use this function""",
                     "function": getanswer,
                     "input": "It has 3 input port that takes 3 input. the original question, a text from where the original question needs to be answered and an expected output data type. output datatypes can be text,num, bool, any",
                     "output": "Returns the answer in the expected output datatype.",
                     "type": {'fun':{'i':['text','text','text'],'o':['text']}},
                     "args":3},
                  "take_sci_action":   {"description": """Take an action in the scienceworld environment""",
                     "function": take_sci_action,
                     "input": "Takes 1 input, action text that needs to be taken.",
                     "output": "Returns observation.",
                     "type": {'fun':{'i':['text'],'o':['text']}},
                     "args":1}
                     }
                     
extfunctionset = {k:v for k,v in extfunctionset.items() if k in ["take_sci_action","getanswer"]}