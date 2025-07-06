actionsimilaritysystemtemp = """You are a action text similarity checker.
Return the most similar action text with respect to user action text from the following list. DO NOT add any extra explanations or texts.
ALWAYS REPLACE THE OBJ with the correct object/objects available.
{action_texts}
Output should be strictly in the following format
{{"result": "<matched action text.  THIS SHOULD NOT CONTAIN OBJ>"}}

"""

actionsimilarityusertemp = """action text: {action_text}
"""
ACTIONSIMSYSTEMVARIABLES = ["action_texts"]
ACTIONSIMUSERVARIABLES = ["action_text"]