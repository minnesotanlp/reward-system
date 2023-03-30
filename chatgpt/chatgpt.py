import time
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
import warnings
from dataclasses import dataclass
from typing import List, Tuple
import minichain
import os
import diff_match_patch as dmp_module
dmp = dmp_module.diff_match_patch()

import spacy
sent_tokenizer = spacy.load("en_core_web_sm")

application = Flask(__name__)
app = Api(app=application,
          version="1.0",
          title="ReWARD",
          description="Record Writer Actions for Rhetorical Adjustments")

name_space = app.namespace('ReWARD', description='Record writing activity')

model = app.model('Recording Writer Actions for Rhetorical Adjustment',
                  {'Reward': fields.String(required=True,
                                         description="--",
                                         help="--")})

os.environ["OPENAI_KEY"] = "----"
warnings.filterwarnings("ignore")
MEMORY = 1
suggestion = "abc"
same_line_before = ""
same_line_after = ""


@dataclass
class State:
    memory: List[Tuple[str, str]]
    human_input: str = ""

    def push(self, response: str) -> "State":
        memory = self.memory if len(self.memory) < MEMORY else self.memory[1:]
        return State(memory + [(self.human_input, response)])

class ChatPrompt(minichain.TemplatePrompt):
    template_file = "chatgpt.pmpt.tpl"
    def parse(self, out: str, inp: State) -> State:
        result = out.split("Assistant:")[-1]
        return inp.push(result)

def run_chatgpt(before, after, current, level):
    with minichain.start_chain("chatgpt") as backend:
        prompt = ChatPrompt(backend.OpenAI())
        state = State([])
        t = "This is what comes before: \"" + before + "\". Here is what comes after: \"" + after + "\". Please optimize this sentence: \"" + current + "\". The length of sentence should not be too long or too short than previous one."
        #text_revise = "This is what comes before: \"" + before + "\". Here is what comes after: \"" + after + "\". Please optimize this paragraph: \"" + current + "\". The length of paragraph should not be too long or too short than previous one."
        # if level:
        #     t = text_revise
        state.human_input = t
        print("Human: ", t)
        state = prompt(state)
        print("ChatGPT: ", state.memory[-1][1])
        return state.memory[-1][1]

@name_space.route("/activity")
class MainClass(Resource):
    @app.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error'},
             params={'activity': 'data from most recent writing activity',
                     'timestamp': 'The time at which writer action was recorded'})
    def get(self):
        try:
            summary = "retrieving the writing actions real time from user input into the overleaf editor"
            # resp_json = request.get_data()
            # print(resp_json)\
            global suggestion
            while (True):
                if (suggestion == "abc"):
                    time.sleep(0.1)
                else:
                    print("I am going to send: ",suggestion)
                    send = suggestion
                    suggestion = "abc"
                    return {
                        "status": send,
                        "same_line_before": same_line_before,
                        "same_line_after": same_line_after
                    }
        except KeyError as e:
            name_space.abort(500, e.__doc__, status="Could not retrieve information", statusCode="500")
        except Exception as e:
            name_space.abort(400, e.__doc__, status="Could not retrieve information", statusCode="400")

    @app.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error'},
             params={'activity': 'data from most recent writing activity',
                     'timestamp': 'The time at which writer action was recorded'})
    @app.expect(model)

    def post(self):
        try:
            info = request.get_json(force=True)
            state = info['state']
            if state == "assist":
                dmp.Match_Distance = 5000
                start = dmp.match_main(info["current_content"], info["selected_text"], 0)
                length = len([each for each in sent_tokenizer(info["selected_text"]).sents])
                print(length)
                if length == 1:
                    level = 0
                else:
                    level = 1
                global suggestion, same_line_before, same_line_after

                same_line_before = info["current_content"][:start]
                same_line_after = info["current_content"][start+len(info["selected_text"]):]
                suggestion = run_chatgpt(info["pre_content"]+info["current_content"][:start],
                  info["current_content"][start+len(info["selected_text"]):]+info["pos_content"],
                  info["selected_text"],
                  level)
            return {
                "status": "Updated recent writing actions in doc",
            }
        except KeyError as e:
            name_space.abort(500, e.__doc__, status="Could not save information", statusCode="500")
        except Exception as e:
            name_space.abort(400, e.__doc__, status="Could not save information", statusCode="400")


if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)