import sys
from neo.config.keys import *
from langchain.utilities import BingSearchAPIWrapper
import os
from langchain.chat_models import ChatOpenAI
import ast
os.environ["BING_SUBSCRIPTION_KEY"] = BING_SUBSCRIPTION_KEY
os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"
search = BingSearchAPIWrapper(k=2)
llm_model = ChatOpenAI(temperature=0.7, request_timeout = 30,model="gpt-3.5-turbo",openai_api_key=OPENAIAPIKEY)

################## Get user text input ####################
def textdataread(display_message = ""):
    text = input(display_message)
    return text

################## Show text output to user ##################
def textshow(message):
    print(message)
    return ""

################## Ask any question to gpt #############
def askgpt(question):
    output = llm_model.predict(question)
    return output

################# Ask question on specific context to gpt and return output in specfic data type
def getanswer(question,text,outputdatatype):
    prompt = """System: You are an intelligent agent that can answer user questions based on the given context. Give to the point exact answer. THE OUTPUT SHOULD BE STRICTLY A PYTHON"""+outputdatatype.upper()+""" FORMAT. Incase the output is not a"""+outputdatatype.upper()+""" return NAN \n\n context:\n"""+text+"""\nAnswer the following question from the above context without considering any other prior information.\nuser: \n"""+question
    output = llm_model.predict(prompt)
    if output == "NAN":
        return ""
    elif outputdatatype in ["number","boolean","list","dictionary"]:
        return ast.literal_eval(output)
    else:
        return output

################## Search a string in bing and get answer #######################
def bingsearch(text):
    return search.run(text)


#################################### describe external function set ###############################
extfunctionset = {"textdataread": {"description": """A function to read and collect user's or environment's responses. The response text data can be typed by the user through standard input. """,
                     "function": textdataread,
                     "input": "It takes one input text message that should be displayed to the user. ",
                     "output": "Returns the text data that user has given as input.",
                     "args": 1},
                  "textshow": {"description": "A function (named textshow) to display a message to the user on standard output. It takes the message to be displayed as parameter. ",
                     "function": textshow,
                     "input": "It takes one input text message that should be displayed to the user. ",
                     "output": "Returns blank text.",
                     "args": 1},
                   "askgpt":  {"description": """A function (named askgpt) to provide answer to general questions using GPT3.5 LLM. It can also provide output in code or structured format like, json yaml etc. if properly prompted to do so. """,
                     "function": askgpt,
                     "input": "It takes one input question or prompt in plaintext. ",
                     "output": "Returns answer in plaintext.",
                     "args": 1},
                   "bingsearch":  {"description": """A function (named bingsearch) to search the web based on input text. The search may return most updated results to date for any search string. """,
                     "code": bingsearch,
                     "input": "It takes one input question or search string in plaintext. ",
                     "output": "Returns search result in plaintext.",
                     "args":1},
                   "getanswer":   {"description": """A function (named getanswer) to get precise answer to a question based on a given text. The answer is given in the expected datatype. The output datatype can be number, boolean, list, dictionary and text. """,
                     "code": getanswer,
                     "input": "It takes 3 input. a question, a text from where the question needs to be answered and an expected output data type. ",
                     "output": "Returns the answer in the expected output datatype.",
                     "args":3}
                     }