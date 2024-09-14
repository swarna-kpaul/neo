import sys
from neo.config.keys import *
#from neo.environment.envtemplate import *
from langchain.utilities import BingSearchAPIWrapper
import os
from langchain.chat_models import ChatOpenAI
import ast
import pyaudio
import wave
import base64
import io
import numpy as np
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioDataStream, AudioConfig, SpeechSynthesisOutputFormat,ResultReason, CancellationReason
from azure.cognitiveservices.speech.audio import PushAudioInputStream
speech_key="853d745aa313452180a16a2c0764c82f"
service_region="eastus"

os.environ["BING_SUBSCRIPTION_KEY"] = BING_SUBSCRIPTION_KEY
os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"
search = BingSearchAPIWrapper(k=2)
llm_model = ChatOpenAI(temperature=0.7, request_timeout = 30,model="gpt-3.5-turbo",openai_api_key=OPENAIAPIKEY)


# ################### decorator wrapper to record environment trace ###################
# def captureenvtrace(env):
    # def decorator(func):
        # def inner(*args, **kwargs):
            # output = func(*args, **kwargs)
            # envtrace = {"action": str(func())+"("+str(args)+str(kwargs)+")", perception: str(output)}
            # env.STM.append("envtrace",envtrace)
            # return output
        # return inner
    # return decorator
    


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
    output = llm_model.predict(question)
    return output,output

################# Ask question on specific context to gpt and return output in specfic data type
def getanswer(env,question,text,outputdatatype):
    prompt = """System: You are an intelligent agent that can answer user questions based on the given context. Give to the point exact answer. THE OUTPUT SHOULD BE STRICTLY A PYTHON"""+outputdatatype.upper()+""" FORMAT. Incase the output is not a"""+outputdatatype.upper()+""" return NAN \n\n context:\n"""+text+"""\nAnswer the following question from the above context without considering any other prior information.\nuser: \n"""+question
    output = llm_model.predict(prompt)
    if output == "NAN":
        return "","No output"
    elif outputdatatype in ["number","boolean","list","dictionary"]:
        return ast.literal_eval(output),output
    else:
        return output,output

################## Search a string in bing and get answer #######################
def bingsearch(env,text):
    output = search.run(text)
    return output, "Here is the search result: "+output


##################  record audio
def record_until_silence(env,dummy):
    THRESHOLD = 500  # Silence threshold
    CHUNK_SIZE = 16000  # Number of frames per buffer
    FORMAT = pyaudio.paInt16  # Format of sampling
    CHANNELS = 1  # Number of audio channels
    RATE = 16000  # Sampling rate
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    print("Recording...")
    frames = []
    silent_chunks = 0
    while True:
        data = stream.read(CHUNK_SIZE)
        #data = np.frombuffer(data, dtype=np.int16)
        #reduced_noise = nr.reduce_noise(y=data, sr=RATE)
        #data = reduced_noise.tobytes()
        frames.append(data)
        print("chunk avg",np.max(np.frombuffer(data, dtype=np.int16)))
        if np.max(np.frombuffer(data, dtype=np.int16)) < THRESHOLD: ## check silence
            silent_chunks += 1
            if silent_chunks > 3:  # If silence is detected for consecutive chunks, stop recording
                break
        else:
            silent_chunks = 0
    print("Finished recording.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    audiodata = b''.join(frames)
    #print("audio",audiodata)
    with io.BytesIO() as buffer:
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audiodata)
        buffer.seek(0)
        base64_audio = base64.b64encode(buffer.read()).decode('utf-8')
    return base64_audio, "recorded audio returned"
#base64_audio = record_until_silence(1,1)

############## play audio ################
def play_base64_audio(env, base64_string):
    # Decode the base64 string to get the audio data
    audio_data = base64.b64decode(base64_string)
    # Use a BytesIO buffer to read the audio data as if it were a file
    audio_buffer = io.BytesIO(audio_data)
    # Open the audio buffer using the wave module
    with wave.open(audio_buffer, 'rb') as wf:
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        # Open a stream with the correct settings
        stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
        # Read data in chunks and play the audio
        data = wf.readframes(16000)
        while data:
            stream.write(data)
            data = wf.readframes(16000)
        # Cleanup
        stream.stop_stream()
        stream.close()
        audio.terminate()
    return "", "audio played"

########## speech recognize 
def recognize_speech(env, base64_audio):
    audio_data = base64.b64decode(base64_audio)
# Convert the byte stream into a binary stream
    audio_stream = io.BytesIO(audio_data)
# Create a SpeechConfig instance with your subscription key and region
    speech_config = SpeechConfig(subscription=speech_key, region=service_region)
# Create an AudioInputStream from the binary stream
    push_stream  = PushAudioInputStream()
# Create an AudioConfig object using the AudioInputStream
    audio_config = AudioConfig(stream=push_stream )
    # Push the audio data into the stream
    bytes_written = push_stream.write(audio_data)
    push_stream.close()
    # Create a SpeechRecognizer with the given settings
    speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    # Start speech recognition
    result = speech_recognizer.recognize_once()
    # Check the result
    if result.reason == ResultReason.RecognizedSpeech:
        print(f" Speecch Recognized: {result.text}")
        return result.text, f"Speech Recognized: {result.text}"
    elif result.reason == ResultReason.NoMatch:
        message = "No speech could be recognized"
        print(message)
        return message,message
    elif result.reason == ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        message = f"Speech Recognition canceled: {cancellation_details.reason}"
        print(message)
        return message,message

    
#################################### describe external function set ###############################
extfunctionset = {"textdataread": {"description": """A function to read and collect user's or environment's responses. The response text data can be typed by the user through standard input. """,
                     "function": textdataread,
                     "input": " It has one input port that should take a text message that needs to be displayed to the user. ",
                     "output": "Returns the text data that user has given as input.",
                     "args": 1,
                     "type": {'fun':{'i':['any'],'o':['text']}}},
                  "textshow": {"description": "A function (named textshow) to display a message to the user on standard output. It takes the message to be displayed as parameter. ",
                     "function": textshow,
                     "input": "It has one input port that takes a text message that should be displayed to the user. ",
                     "output": "Returns a text that states required message has been displayed.",
                     "type": {'fun':{'i':['any'],'o':['any']}},
                     "args": 1},
                   "askgpt":  {"description": """A function (named askgpt) to provide answer to general questions using GPT3.5 LLM. It can also provide output in code or structured format like, json yaml etc. if properly prompted to do so. """,
                     "function": askgpt,
                     "input": "It has one input port that takes one input question or prompt in plaintext. ",
                     "output": "Returns answer in plaintext.",
                     "type": {'fun':{'i':['any'],'o':['text']}},
                     "args": 1},
                   "bingsearch":  {"description": """A function (named bingsearch) to search the web based on input text. The search may return most updated results to date for any search string. """,
                     "function": bingsearch,
                     "input": "It has one input port that takes one input question or search string in plaintext. ",
                     "output": "Returns search result in plaintext.",
                     "type": {'fun':{'i':['any'],'o':['text']}},
                     "args":1},
                   "getanswer":   {"description": """A function (named getanswer) to get precise answer to a question based on a given text. The answer is given in the expected datatype. The output datatype can be number, boolean, list, dictionary and text. For getting a structured answer for a question on a given context use this function""",
                     "function": getanswer,
                     "input": "It has 3 input port that takes 3 input. the original question, a text from where the original question needs to be answered and an expected output data type. ",
                     "output": "Returns the answer in the expected output datatype.",
                     "type": {'fun':{'i':['text','text','text'],'o':['text']}},
                     "args":3},
                   "record_until_silence":   {"description": """A function to record audio from microphone until there is a silence for 3 seconds.""",
                     "function": record_until_silence,
                     "input": "One input, can be anything",
                     "output": "Returns recorded audio in base64 encoded wav format",
                     "type": {'fun':{'i':['any'],'o':['text']}},
                     "args":1},
                    "play_base64_audio":   {"description": """A function to play audio.""",
                     "function": play_base64_audio,
                     "input": "One input, base64 encoded audio data",
                     "output": "Returns blank string",
                     "type": {'fun':{'i':['text'],'o':['text']}},
                     "args":1},
                     "recognize_speech":   {"description": """A function to convert speech to text.""",
                     "function": recognize_speech,
                     "input": "One input, base64 encoded audio data containing speech",
                     "output": "Returns recognized text",
                     "type": {'fun':{'i':['text'],'o':['text']}},
                     "args":1}
                     }