from config.configurations import *
from config.prompts import *
from langchain.prompts.prompt import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAIAPIKEY)

textdataread = """
import sys
def textdataread(display_message = ""):
    text = input(display_message)
    return text
"""    

textshow = """
def showmessage(message):
    print(message)
    return "Message shown to the user"
"""

neosolver = """
def problemsolver(environement):
    lifetime = environement[1]
    envdescription = environement[0]
    env = {"description": problem,"objective": "", "beliefaxioms":""}
    solver = context.neosolvercreator(env)
    solver.run(lifetime)
    return solver.stm.get("critique")
"""

askgpt ="""
from config.keys import *
from langchain.chat_models import ChatOpenAI
llm_model = ChatOpenAI(temperature=0.7, request_timeout = 30,model="gpt-3.5-turbo",openai_api_key=OPENAIAPIKEY)
def askgpt(question):
    output = llm_model.predict(question)
    return output
"""

bingsearch = """
from langchain.utilities import BingSearchAPIWrapper
import os
os.environ["BING_SUBSCRIPTION_KEY"] = "f5f5b72543d54c60af687e17bad487dc"
os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"
search = BingSearchAPIWrapper(k=2)
def bingsearch(text):
    return search.run(text)
"""

takeenvaction = """
def takeenvaction(actionvalue):
    return envobject.problemenv.act(actionvalue)
"""


createenvironment = """
import ast
def createenvironment(task):
    flag = True
	erroroutput = ""
    while flag:
        prompt = "System: You need to transform the problem description to a json format called as environment.\n" +\
            " problem description:\n"+\
			task+"\n"+\
			"The output environment should be strictly in the following json format. Add escape characters where required. \n"+
			"{'description': <a brief description of the problem environment>, 'objective': <what is needed to solve the problem>, 'beliefaxioms': <belief or axioms or causal statements about the problem>}"
        output = llm_model.predict(prompt+erroroutput)
		try:
		    output = ast.literal_eval(output)
			flag = False
        except Exception as e:
		    erroroutput = "\n\nHere is the error while parsing the output json. Correct the output json. \n" + str(e)
		    
	return output
"""

bootstrapactions = [{"description": """A function (named textdataread) to read and collect user's or envirnment's responses. The response text data can be typed by the user through standard input.
It returns the text data provided by the user or environment.""",
                     "code": textdataread,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name": "textdataread",
                     "input parameter": "message that should be displayed to the user",
                     "output": "text data that user has given as input"},
                    {"description": "A function (named textshow) to display a message to the user on standard output. It takes the message to be displayed as parameter.",
                     "code": textshow,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name": "textshow",
                     "input parameter": "message that should be displayed to the user",
                     "output": "None"},
                    {"description": """A function (named neosolver) to solve a arbitrary problem environment.
If the problem environment is barely known, it interacts with the environment to know it more and derives an estimate. Therafter it finds an optimal solution.
This is an autonomous AI agent that runs for a fixed lifetime. """,
                     "code": neosolver,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name":"neosolver",
                     "input parameter": "list of two items. 1st item represents lifetime of the agent and second is the text description of the problem",
                     "output": "Output of the critique on solution of the problem"},
                     {"description": """A function (named askgpt) to provide answer to general questions using GPT3.5 LLM. It can also write code if properly asked to do so. It can also provide output in structured format like, json yaml etc. if properly prompted to do so.""",
                     "code": askgpt,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name":"askgpt",
                     "input parameter": "a question or prompt in plaintext",
                     "output": "answer in plaintext"},
                     {"description": """A function (named bingsearch) to search the web based on input text. The search may return most updated results to date for any search string""",
                     "code": bingsearch,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name":"bingsearch",
                     "input parameter": "a question or search string in plaintext",
                     "output": "search result in plaintext"},
                     {"description": """A function (named takeenvaction) to take action in a task environment.""",
                     "code": takeenvaction,
                     "requirements": "",
                     "actiontype": "fixed",
                     "type":"actions",
                     "name":"takeenvaction",
                     "input parameter": "a action value that will be taken in the task environment",
                     "output": "observation returned by the environment in text format"}
                     ]
                     
                    

pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV
)
index=pinecone.GRPCIndex(DEFAULT_PINECONE_INDEX_NAME)                    
def writebootstrapactions(bootstrapactions):
    cutoffscore = 0.7
    CODEEQUIVALENCEPROMPT = PromptTemplate(input_variables=CODEEQUIVALENCEVARIABLES, template=codequivalencetemplate)
    for action in bootstrapactions:
        embedding = embeddings_model.embed_query(action["description"])
        xc = index.query(vector = embedding, filter={"type": "actions", "actiontype" : "fixed"}, top_k=1, include_metadata=True)
        result = xc["matches"]
        print("result",result)
        data = [ i for i in result if i['score'] > cutoffscore ]
        score = data[0]['score'] if data else 0
        metadata = data[0]['metadata'] if data else {}
        dataid = data[0]["id"] if data else 0
        id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if score > 0.95:
           id = dataid
        elif metadata:
            messages = CODEEQUIVALENCEPROMPT.format(code1 = action["code"], code2 = metadata["code"])
            print("CODEEQUIVALENCEPROMPT:",messages)
            output = llm_defn_model.predict(messages)
            print("CODEEQUIVALENCEPROMPT output:",output)
            if output == "True":
                id = dataid
        ltmdata = [{'id': str(id), 'values': embedding, 'metadata': action }]
        index.upsert(ltmdata)  