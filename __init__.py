from neo.environment.envtemplate import *
env = bootstrapenv(objective = "You should take text input from the user. The user may ask question or provide instructions or ask to solve a task. You may need to answer questions, follow instructions and solve tasks based on users input. At the end ask for user feedback.", rewriteprocmem = True, prioraxioms= "You can use the getanswer function to generate specific structured answer for a question on a context",shortdescription = "Carry out user commands")
from neo.components.internalfunctions import *