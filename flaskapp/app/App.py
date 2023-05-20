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
# application.config["MONGO_URI"] = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE']
# mongo = PyMongo(application)
# db = mongo.db

os.environ["OPENAI_KEY"] = ""
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
        state = prompt(state)
        return state.memory[-1][1]

@name_space.route("/activity")
class MainClass(Resource):

    check = 0
    @app.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error'},
             params={'activity': 'data from most recent writing activity',
                     'timestamp': 'The time at which writer action was recorded'})
    def get(self):
        try:
            summary = "retrieving the writing actions real time from user input into the overleaf editor"
            # resp_json = request.get_data()
            # print(resp_json)
            global suggestion
            while (True):
                if (suggestion == "abc"):
                    time.sleep(0.1)
                else:
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

    def exist_and_not_skip(self, i, text, skip):
        try:
            if (text[i][0]) != skip:
                return True
            else:
                return False
        except IndexError:
            return True

    def findback(self, i, type, skip, text):
        back = ""
        check = 0
        if ("\n" in text[i][1]) or (" " in text[i][1] and len(text[i][1]) > 1 and self.exist_and_not_skip(i + 1, text, skip)):
            return check, back
        for k in range(i + 1, len(text)):
            if text[k][0] == skip or len(text[k]) > 2:
                if text[k][0] == skip:
                    check = 1
                k += 1
            else:
                idx = -1
                idx1 = text[k][1].find(" ")
                idx2 = text[k][1].find("\n")
                if idx2 >= 0 > idx1:
                    idx = idx2
                elif idx1 >= 0 > idx2:
                    idx = idx1
                elif idx1 > idx2 >= 0:
                    idx = idx2
                elif idx2 > idx1 >= 0:
                    idx = idx1
                if text[k][0] != 0:
                    text[k].append(1)
                if idx == 0:
                    if text[k][0] == type:
                        back += text[k][1]
                    return check, back
                else:
                    if idx == -1:
                        back += text[k][1]
                    else:
                        if text[k][0] == type:
                            back += text[k][1]
                        else:
                            back += text[k][1][:idx]
                        return check, back
        return check, back

    def findfront(self, i, skip, text):
        front = ""
        check = 0
        if ("\n" in text[i][1]) or (" " in text[i][1] and len(text[i][1]) > 1 and self.exist_and_not_skip(i-1,text, skip)):
            return check, front
        for k in range(i - 1, -1, -1):
            if text[k][0] == skip:
                check = 1
                k -= 1
            else:
                if (text[k][1].rfind(" ") == (len(text[k][1]) - 1)) or (
                        text[k][1].rfind("\n") == (len(text[k][1]) - 1)):
                    return check, front
                elif (text[k][1].rfind(" ") != 0) or (text[k][1].rfind("\n") != 0):
                    idx2 = text[k][1].rfind(" ")
                    idx3 = text[k][1].rfind("\n")
                    if idx3 > idx2 and (idx2 != -1):
                        idx2 = idx3
                    if idx2 == -1:
                        front = text[k][1] + front
                    else:
                        front = text[k][1][idx2 + 1:] + front
                        return check, front
        return check, front

    def countChar(self, op, i, text):
        pos = 0
        if "\n" == text[i][1][0]:
            return pos
        for k in range(i - 1, -1, -1):
            if op == -1 and (text[k][0] == 1 or text[k][0] == -1):
                k -= 1
            elif text[k][0] == -1 and op == 1:
                k -= 1
            else:
                idx = text[k][1].rfind("\n")
                if idx == (len(text[k][1]) - 1):
                    break
                elif idx == -1:
                    pos += len(text[k][1])
                else:
                    pos += len(text[k][1][idx + 1:])
                    break
        return pos

    def pasteCountChar(self, text, revision):
        i = 0
        pos = 0
        for j in range(len(text)):
            try:
                if text[j] != revision[j]:
                    i = j - 1
                    break
                if j == (len(text) - 1):
                    i = len(text) - 1
            except IndexError:
                i = j
                break
        if text[i] == '\n' or text[i - 1] == '\n':
            return pos
        for k in range(i, -1, -1):
            if text[k] == '\n':
                break
            pos += 1
        return pos

    def typeHandler(self, info):
        text = info['revision']
        lineNum = info['line']
        length = len(text)
        changes = []
        swapword = []
        index = 0
        for i in range(length):
            front = ""
            back = ""
            if len(text[i]) > 2 or text[i][0] != -1:
                continue
            elif (text[i][0] == -1) and (0 < i < length - 1):
                check2, front = self.findfront(i, 1, text)
                check1, back = self.findback(i, -1, 1, text)
                pos = self.countChar(-1, i, text)
                if check1 or check2:
                    swapword.append(
                        '(' + str(lineNum) + ',' + str(pos - len(front)) + ')' + ", " + front + text[i][
                            1] + back + "->")
                elif front + back != "":
                    check2, front1 = self.findfront(i, -1, text)
                    check1, back1 = self.findback(i, -1, -1, text)
                    changes.append('(' + str(lineNum) + ',' + str(pos - len(front)) + ')' + ", " + front + text[i][
                        1] + back + "->" + front1 + back1)
                else:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

            elif (text[i][0] == -1) and i == 0:
                check1, back = self.findback(i, -1, 1, text)
                pos = self.countChar(-1, i, text)
                if front + back != "":
                    check1, back1 = self.findback(i, -1, -1, text)
                    changes.append('(' + str(lineNum) + ',' + str(pos - len(front)) + ')' + ", " + front + text[i][
                        1] + back + "->" + front + back1)
                else:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

            elif (text[i][0] == -1) and (i + 1 == length):
                pos = self.countChar(-1, i, text)
                if " " in text[i][1] or "\n" in text[i][1]:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")
                elif length == 1:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")
                else:
                    check2, front = self.findfront(i, 1, text)
                    if front + back != "":
                        check2, front1 = self.findfront(i, -1, text)
                        changes.append(
                            '(' + str(lineNum) + ',' + str(pos - len(front1)) + ')' + ", " + front1 + text[i][
                                1] + back + "->" + front + back)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

        for i in range(length):
            front = ""
            back = ""
            if len(text[i]) > 2 or text[i][0] != 1:
                continue
            elif (text[i][0] == 1) and (0 < i < length - 1):
                pos = self.countChar(1, i, text)
                if i == length - 2 and (
                        text[length - 1][1][0].isspace() or text[length - 1][1][0] == "\n") and swapword == []:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                else:
                    check1, back = self.findback(i, 1, -1, text)
                    check2, front = self.findfront(i, -1, text)
                    if (check1 or check2) and (swapword != []):
                        swapword[index] += (front + text[i][1] + back)
                        changes.append(swapword[index])
                        index += 1
                    elif front + back != "":
                        check2, front1 = self.findfront(i, 1, text)
                        check1, back1 = self.findback(i, 1, 1, text)
                        changes.append(
                            '(' + str(lineNum) + ',' + str(
                                pos - len(front1)) + ')' + ", " + front1 + back1 + "->" + front +
                            text[i][1] + back)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")

            elif (text[i][0] == 1) and (i == 0):
                check1, back = self.findback(i, 1, -1, text)
                pos = self.countChar(1, i, text)
                if front + back != "":
                    check1, back1 = self.findback(i, 1, 1, text)
                    changes.append(
                        '(' + str(lineNum) + ',' + str(pos - len(front)) + ')' + ", " + front + back1 + "->" + front +
                        text[i][
                            1] + back)
                else:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
            elif (text[i][0] == 1) and (i + 1 == length):
                check, front = self.findfront(i, -1, text)
                pos = self.countChar(1, i, text)
                if check:
                    swapword[index] += (front + text[i][1])
                    changes.append(swapword[index])
                elif text[i][1][0] == " " or text[i][1][0] == "\n":
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                elif length == 1:
                    changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                else:
                    check2, front = self.findfront(i, -1, text)
                    if front + back != "":
                        check1, back1 = self.findback(i, 1, 1, text)
                        changes.append(
                            '(' + str(lineNum) + ',' + str(
                                pos - len(front)) + ')' + ", " + front + back + "->" + front +
                            text[i][1] + back1)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
        return changes

    def copyHandler(self, info):
        text = info['text']
        clipboard = info['cb']
        linenumbers = info['copyLineNumbers']
        i = text.find(clipboard)
        charPos = 0
        linePos = 0
        for k in range(i, -1, -1):
            if text[k] == '\n':
                linePos += 1
        for l in range(i - 1, -1, -1):
            if text[l] == '\n':
                break
            charPos += 1
        info['cb'] = '(' + str(linenumbers[linePos]) + ',' + str(charPos) + ')' + ", " + info['cb']
        return info

    def atbound(self,text, j):
        if j + 1 == len(text):
            return True
        elif text[j + 1][0] == '\n':
            return True
        return False

    def post(self):
        try:
            info = request.get_json(force=True)
            state = info['state']
            if state == "user_selection":
                print("more detail in the future")
            elif state == "assist":
                dmp.Match_Distance = 5000
                start = dmp.match_main(info["current_content"], info["selected_text"], 0)
                length = len([each for each in sent_tokenizer(info["selected_text"]).sents])
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
                info["context above"] = info["pre_content"]+info["current_content"][:start]
                info["context below"] = info["current_content"][start+len(info["selected_text"]):]+info["pos_content"]
                info["suggestion"] = suggestion
                info.pop("pre_content")
                info.pop("pos_content")
                info.pop("current_content")
            elif state == 2:
                info = self.copyHandler(info)
            elif state != 3:
                changes = self.typeHandler(info)
                info["changes"] = changes
            if state == 0 or state == 4:
                info.pop('line')
                info.pop("cb")
            elif state == 1:
                info.pop('line')
                info["cut"] = info.pop("cb")
            elif state == 2:
                info.pop('copyLineNumbers')
                info["copy"] = info.pop("cb")

            #db.activity.insert_one(info)
            print(info)

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