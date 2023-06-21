import time
import copy
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
import warnings
from typing import List, Tuple
from dataclasses import dataclass, replace
from minichain import OpenAI, prompt, show, transform, Mock
import os
import diff_match_patch as dmp_module
dmp = dmp_module.diff_match_patch()
import traceback
from rich.console import Console
console = Console()
from pymongo import MongoClient

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

os.environ["OPENAI_API_KEY"] = ""
warnings.filterwarnings("ignore")
MEMORY = 0
suggestion = "abc"
same_line_before = ""
same_line_after = ""
selected_text = ""
suggestion_Log = ""

@dataclass
class State:
    memory: List[Tuple[str, str]]
    human_input: str = ""

    def push(self, response: str) -> "State":
        memory = self.memory if len(self.memory) < MEMORY else self.memory[1:]
        return State(memory + [(self.human_input, response)])

    def __str__(self):
        return self.memory[-1][-1]


# Chat prompt with memory

@prompt(OpenAI(), template_file="chat.pmpt.tpl")
def chat_response(model, state: State) -> State:
    return model.stream(state)


@transform()
def update(state, chat_output):
    result = chat_output.split("Assistant:")[-1]
    return state.push(result)


def chat(before, after, current, state):
    command = "This is what comes before: \"" + before + "\". Here is what comes after: \"" + after + "\". Please paraphrase this sentence/paragraph: \"" + current + "\". The length of sentence should not be too long or too short than previous one."
    state = replace(state, human_input=command)
    return update(state, chat_response(state))


import pymongo


# for using Azure CosmoDB
def get_collection():
    # Get connection info from environment variables
    print("STARTING AGAIN")
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('DB_NAME')
    COLLECTION_NAME = os.getenv('COLLECTION_NAME')

    print("CONNECTION STRING: ", CONNECTION_STRING)
    print("DB NAME: ", DB_NAME)
    print("COLLECTION NAME: ", COLLECTION_NAME)

    # Create a MongoClient
    client = pymongo.MongoClient(CONNECTION_STRING)
    try:
        client.server_info()  # validate connection string
    except pymongo.errors.ServerSelectionTimeoutError:
        raise TimeoutError("Invalid API for MongoDB connection string or timed out when attempting to connect")

    db = client[DB_NAME]
    return db[COLLECTION_NAME]


# create database instance
db = get_collection()
client = MongoClient('localhost', 27017)
db = client.flask_db
activity = db.activity


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
            return {
                "state": summary
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

    def atbound(self, text, j):
        if j + 1 == len(text):
            return True
        elif text[j + 1][0] == '\n':
            return True
        return False

    def sentence_reform(self, splited):
        j = 0
        while j < len(splited):
            if j + 1 < len(splited) and (splited[j][-1:] == '\n') and splited[j + 1][0] != '\n':
                splited[j + 1] = splited[j][-1:] + splited[j + 1][:]
                splited[j] = splited[j][:-1]
                j += 1
            elif (splited[j][-1:] == '\n') and self.atbound(splited, j):
                splited.insert(j + 1, splited[j][-1:])
                splited[j] = splited[j][:-1]
                j += 2
            else:
                j += 1
        k = 0
        while k < len(splited):
            if splited[k] == '':
                splited.pop(k)
            k += 1
        return splited

    def findback(self, i, type, skip, text):
        back = ""
        check = 0
        if ("\n" in text[i][1]) or (
                " " in text[i][1] and len(text[i][1]) > 1 and self.exist_and_not_skip(i + 1, text, skip)):
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
        if ("\n" in text[i][1]) or (
                " " in text[i][1] and len(text[i][1]) > 1 and self.exist_and_not_skip(i - 1, text, skip)):
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
                    if idx3 > idx2:
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

    def pasteHandler(self, pre, cur, order):
        # if order is 1, mean cur is longer than pre
        # if order is 2, means pre is longer than cur
        change = ""
        i = 0
        j = 0
        diff_section1 = []
        diff_section2 = []

        # use to handle some edge cases
        if cur == []:
            print("".join(pre[:]), "--deleted")
            return
        elif pre == []:
            print("".join(cur[:]), "--added")
            return

        # const_pre and const_cur is use to reconstruct the original text
        original_pre = copy.deepcopy(pre)
        original_cur = copy.deepcopy(cur)
        for k in range(len(pre)):
            if pre[k][0] == '\n':
                pre[k] = pre[k][1:]
        for k in range(len(cur)):
            if cur[k][0] == '\n':
                cur[k] = cur[k][1:]

        # use to handle most common cases
        switch = 0
        if len(pre) == len(cur):
            length = len(pre)
            for i in range(length):
                if pre[i] != cur[i]:
                    diff_section1.append(original_pre[i])
                    diff_section2.append(original_cur[i])
        elif order == 1:
            long = cur
            short = pre
            original_long = original_cur
            original_short = original_pre
            length = len(pre)
            while i < length:
                if short[i] != long[i]:
                    if switch:
                        diff_section1.append(original_long.pop(i))
                        long.pop(i)
                    else:
                        diff_section2.append(original_long.pop(i))
                        long.pop(i)
                elif short[i] == long[i]:
                    i += 1
                j += 1
                if len(pre) > len(cur):
                    switch = 1
                    length = len(cur)
                    long = pre
                    short = cur
                    original_long = original_pre
                    original_short = original_cur
                elif switch == 1 and len(cur) > len(pre):
                    switch = 0
                    length = len(pre)
                    long = cur
                    short = pre
                    original_long = original_cur
                    original_short = original_pre
            if i < len(long):
                diff_section1.extend(original_short[i - 1:])
                diff_section2.extend(original_long)
        else:
            long = pre
            short = cur
            original_long = original_pre
            original_short = original_cur
            length = len(cur)
            while i < length:
                if short[i] != long[i]:
                    if switch:
                        diff_section2.append(original_long.pop(i))
                        long.pop(i)
                    else:
                        diff_section1.append(original_long.pop(i))
                        long.pop(i)
                elif short[i] == long[i]:
                    i += 1
                j += 1
                if len(pre) < len(cur):
                    switch = 1
                    length = len(pre)
                    long = cur
                    short = pre
                    original_long = original_cur
                    original_short = original_pre
                elif switch == 1 and len(cur) < len(pre):
                    switch = 0
                    length = len(cur)
                    long = pre
                    short = cur
                    original_long = original_pre
                    original_short = original_cur
            if i < len(long):
                diff_section1.extend(original_long)
                diff_section2.extend(original_short[i - 1:])

        diff_sentence1 = "".join(diff_section1[:1])
        for l in range(1, len(diff_section1[1:]) + 1):
            if diff_section1[l][0] != '\n':
                diff_sentence1 += " " + diff_section1[l]
            else:
                diff_sentence1 += diff_section1[l]

        diff_sentence2 = "".join(diff_section2[:1])
        for m in range(1, len(diff_section2[1:]) + 1):
            if diff_section2[m][0] != '\n':
                diff_sentence2 += " " + diff_section2[m]
            else:
                diff_sentence2 += diff_section2[m]

        if diff_sentence1 == "" and diff_sentence2 == "":
            change = "All lines are the same"
        elif diff_sentence1 == "" and diff_sentence2 != "":
            change = diff_sentence2 + "--added"
        elif diff_sentence1 != "" and diff_sentence2 == "":
            change = diff_sentence1 + "--deleted"
        elif diff_sentence1 != "" and diff_sentence2 != "":
            change = diff_sentence1 + "->" + diff_sentence2

        return change

    def post(self):
        try:
            global suggestion, same_line_before, same_line_after, selected_text, suggestion_Log
            info = request.get_json(force=True)
            state = info['state']
            console.log(info)
            try:
                onkey = info['onkey']
            except:
                onkey = ""
            if state == "assist":
                # find where the selection begin
                dmp.Match_Distance = 5000
                start = dmp.match_main(info["current_content"], info["selected_text"], 0)
                end = start + len(info["selected_text"]) - 1

                # if selected text is not a complete sentence
                for j in range(end, len(info["current_content"]), 1):
                    if info["current_content"][j] in ".?!;\n":
                        end = j + 1
                        break
                    end += 1
                for i in range(start, 0, -1):
                    if info["current_content"][i] in ".?!;\n":
                        start = i + 1
                        break
                    start -= 1

                selected_text = info["current_content"][start:end]
                # text on the same line but not selected
                same_line_before = info["current_content"][:start]
                same_line_after = info["current_content"][end:]

                # By combining the text content on the other lines
                # with the unselected content on the same line, we get the context.
                # Passing the context to the language model along with the selected content
                before = info["pre_content"] + same_line_before
                after = same_line_after + info["pos_content"]
                try:
                    suggestion = str(chat(before, after, selected_text, State([])).run())
                except:
                    suggestion = ""

                # setup all logging info
                info["selected_text"] = selected_text
                info["context above"] = before
                info["context below"] = after
                info["suggestion"] = suggestion
                info.pop("pre_content")
                info.pop("pos_content")
                info.pop("current_content")

                # send ChatGPT's paraphrase to the frontend
                suggestion_Log = suggestion
                suggestion = "abc"
                diffs_html = ""
                if suggestion_Log != "":
                    diffs = dmp.diff_main(selected_text, suggestion_Log)
                    dmp.diff_cleanupSemantic(diffs)
                    diffs_html = dmp.diff_prettyHtml(diffs)

                activity.insert_one(info)
                console.log(info)
                data = {
                    "status": "ChatGPT",
                    "suggestion": suggestion_Log,
                    "diffs_html": diffs_html,
                    "same_line_before": same_line_before,
                    "same_line_after": same_line_after
                }
                response = jsonify(data)
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                return response

            elif state == "user_selection":
                if info["accept"]:
                    info["changes"] = selected_text + "->" + suggestion_Log
                else:
                    info["changes"] = "All lines are the same"

                activity.insert_one(info)
                console.log(info)
                response = jsonify({"status": "Updated recent writing actions in doc"})
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                return response

            elif state == 2:
                info = self.copyHandler(info)
            elif (onkey in "zZyY" and len(info['revision']) >= 4) or state == 3:
                if onkey in "zZyY":
                    text = ""
                    for each in info["revision"]:
                        if each[0] == 0 or each[0] == -1:
                            text += each[1]
                    pre_text = self.sentence_reform(text.splitlines(keepends=True))
                    cur_text = self.sentence_reform(info["text"].splitlines(keepends=True))
                else:
                    pre_text = self.sentence_reform(info["text"].splitlines(keepends=True))
                    cur_text = self.sentence_reform(info["revision"].splitlines(keepends=True))
                pre = []
                cur = []
                for s in pre_text:
                    for each in sent_tokenizer(s).sents:
                        pre.extend([str(each)])
                for s in cur_text:
                    for each in sent_tokenizer(s).sents:
                        cur.extend([str(each)])
                if len(pre) < len(cur):
                    change = self.pasteHandler(pre, cur, 1)
                else:
                    change = self.pasteHandler(pre, cur, 2)
                if change != "All lines are the same":
                    charNum = self.pasteCountChar(info["text"], info["revision"])
                    lineNum = info['line']
                    info["changes"] = ['(' + str(lineNum) + ',' + str(charNum) + ') ' + change]
                else:
                    info["changes"] = "All lines are the same"
            else:
                changes = self.typeHandler(info)
                info["changes"] = changes

            info.pop('onkey')
            info.pop('line')
            if state == 0 or state == 4:
                info['state'] = "Type"
                info.pop('cb')
            elif state == 1:
                info['state'] = "Cut"
                info['clipboard'] = info.pop('cb')
            elif state == 2:
                info['state'] = "Copy"
                info.pop('copyLineNumbers')
                info['clipboard'] = info.pop('cb')
            elif state == 3:
                info['state'] = "Paste"
                info['clipboard'] = info.pop('cb')
            # add document to database
            activity.insert_one(info)
            console.log(info)

            response = jsonify({"status": "Updated recent writing actions in doc"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response

        except KeyError as e:
            name_space.abort(500, e.__doc__, status="Could not save information", statusCode="500")
        except Exception as e:
            print(traceback.print_exc())
            name_space.abort(400, e.__doc__, status="Could not save information", statusCode="400")

    def options(self):
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
