let serverURL;
// serverURL = "http://127.0.0.1:5000/"
// serverURL = "http://localhost"
serverURL = "your_url_here";
let headers = new Headers();
headers.append('GET', 'POST', 'OPTIONS');
headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000/');
headers.append('Access-Control-Allow-Credentials', 'true');

import { diff_match_patch, DIFF_DELETE, DIFF_INSERT, DIFF_EQUAL } from './diff-match-patch/index.js';
var dmp = diff_match_patch;

let text = [];
let changemade;
let clipboard = "";
let filename = "";
let prelineNumber;
let lineNumber;
let copyLineNumbers;
let projectID = "no url"
let suggestion = ""

chrome.runtime.onMessage.addListener(
    function (request, sender, sendResponse) {
        console.log("Entered");
        text = text.filter(function(element) {return element !== undefined;});
        projectID = request.project_id
        filename = request.editingFile;
        if (request.message == "assist"){
            var d = new Date();
            var ms = d.getMilliseconds();
            var time = d.toString().slice(0,24)+':'+ms+d.toString().slice(24,);
            postWriterText({state: "assist",timestamp: time, project: projectID, file: filename, pre_content: request.pre_content,
            pos_content: request.pos_content, selected_text: request.selected_text, current_content: request.current_line_content,
            current_line_content: request.current_line_content, line: request.line});
            generateText();
        }
        else{
            lineNumber = findLineEdit(request.edittingLines, request.edittingArray, request.paragraphLines, request.paragraphArray);
        }
        if (request.message == "listeners") {
            // process edits, find the diff, as additions or deletions
           console.log("***** press *****");
           text.push(request.text);
           console.log(text)
           console.log(request.revisions);
           if (prelineNumber == null){
               prelineNumber = lineNumber;
           }
           if (prelineNumber != lineNumber && lineNumber != null){
               console.log("***** different line *****");
               trackWriterAction(4, text[0], request.text, prelineNumber);
               trackWriterAction(0, request.text, request.revisions, lineNumber);
               prelineNumber = lineNumber
           }
           else{
               trackWriterAction(0, request.text, request.revisions, lineNumber);
               prelineNumber = lineNumber
           }
        }
        else if (request.message == "hidden") {
            // process edits, find the diff, as additions or deletions
           console.log("***** hidden *****");
           console.log(request.revisions);
           // text.push(request.text);
           if (text[0] != null && request.revisions != null){
               trackWriterAction(4, text[0], request.revisions, lineNumber);
               prelineNumber = lineNumber
               text = [request.revisions];
           }
        }
        else if (request.message == "scroll"){
            console.log("***** scroll *****");
            console.log(request.revisions);
            if (text[0] !== undefined && text.length > 1){
                trackWriterAction(4, text[0], request.text, lineNumber);
                prelineNumber = lineNumber
            }
            text = [request.revisions];
        }
        else if (request.message == "switch"){
            console.log("***** switch *****");
            console.log(request.revisions);
            if (text[0] !== undefined && text.length > 1){
                trackWriterAction(4, text[0], request.text, lineNumber);
                prelineNumber = lineNumber
            }
            text = [request.revisions];
        }
        else if (request.message == "cut") {
            // process edits, find the diff, as additions or deletions
           // text.push(request.text);
           clipboard = request.cutted;
           if(text[0] !== undefined){
            trackWriterAction(4, text[0], request.text, prelineNumber);
           }
           trackWriterAction(1, request.text, request.revisions, lineNumber);
           text = [request.revisions];
        }
        else if (request.message == "copy") {
            // process edits, find the diff, as additions or deletions
           // text.push(request.text);
           clipboard = request.copied;
           if(text[0] !== undefined){
            trackWriterAction(4, text[0], request.text, prelineNumber);
           }
           copyLineNumbers = request.edittingLines
           trackWriterAction(2, request.text, request.revisions, lineNumber);
           text = [request.revisions];
        }
        else if (request.message == "paste") {
            // process edits, find the diff, as additions or deletions
           // text.push(request.text);
           console.log("***** paste *****")
           clipboard = request.pasted;
           if(text[0] !== undefined){
            trackWriterAction(4, text[0], request.text, prelineNumber);
           }
           trackWriterAction(3, request.text, request.revisions, lineNumber);
           text = [request.revisions];
        }
    }
);

function findLineEdit(edittingLines, edittingArray, paragraphLines, paragraphArray) {
    if (edittingArray.length > paragraphArray.length) {  // line(s) added
        for (let i = 0; i < paragraphArray.length; i++){
            if (paragraphArray[i] != edittingArray[i]){
               console.log(parseInt(paragraphLines[i]) + (edittingArray.length - paragraphArray.length));
               return (parseInt(paragraphLines[i]) + (edittingArray.length - paragraphArray.length))
            }
        }
        console.log(edittingLines[edittingArray.length - 1])
        return edittingLines[edittingArray.length - 1]
    } else {
        for (let i = 0; i < edittingArray.length; i++){
            if(edittingArray[i] != paragraphArray[i]){
               console.log(edittingLines[i])
               return parseInt(edittingLines[i])
            }
        }
        console.log("All lines are the same");
        return prelineNumber
    }
}

function difference(paragraph, revisions) { // utilizing Myer's diff algorithm
    // classifications:
    // 1. addition
    // 2. deletion
    // classification: for swapping texts can be handeled in the back end
    var diff = dmp.prototype.diff_main(
        paragraph,
        revisions);
    // [1: Hello, 1: Goodbye, 0: World];
    // diff = dmp.prototype.diff_cleanupSemantic(diff);
    return diff;
}

// refactor to track writer input
//TODO: support for other actions
function trackWriterAction(state, writerText, revisions, ln) {
    // post comment to the backend
    let change = "addition";
    let diff = difference(writerText, revisions);
    if (diff.length == 0){
     return 0
    }
    var d = new Date();
    var ms = d.getMilliseconds();
    var time = d.toString().slice(0,24)+':'+ms+d.toString().slice(24,)
    if (state == 3){
        postWriterText({timestamp: time, project: projectID, file: filename, text: writerText, revision: revisions,
        state: state, cb: clipboard, line: ln})
        text = [revisions]
        clipboard = "";
    }
    else if (diff[0][0] === -1) {
            change = "deletion";
            changemade = difference(text[0], revisions)
            postWriterText({timestamp: time, project: projectID, file: filename, text: revisions, revision: changemade,
             state: state, cb: clipboard, line: ln})
            text = [revisions]
    }
    else if (diff[0][1] === '\n' || diff[0][1] === ' ') {
        change = "addition";
        changemade = difference(text[0], revisions)
        postWriterText({timestamp: time, project: projectID, file: filename, text: revisions, revision: changemade,
         state: state, cb: clipboard, line: ln})
        text = [revisions]
    }
    else if (diff.length < 2 && (state== 0 || state == 4)) {
        change = "no change";  //TODO: resolve issue, "no change" may also suggest movement to a new line
    }
    else {
        if (state == 1 || state == 2) {
            change = "cut/copy";
            postWriterText({timestamp: time, project: projectID, file: filename, text: revisions, revision: diff,
            state: state, cb: clipboard, line: ln, copyLineNumbers:copyLineNumbers})
            text = [revisions]
            clipboard = "";
        }
        else if(diff[1][0] === -1) {
            change = "deletion";

            if ((diff[1][1] == '\n' || diff[1][1].includes(' '))|| state != 0){
               // if user delete a space, the chars array will be send to the backend for processing
                changemade = difference(text[0], revisions)
                postWriterText({timestamp: time, project: projectID, file: filename, text: revisions, revision: changemade,
                state: state, cb: clipboard, line: ln})
                text = [revisions]
            }
        }
        else if (diff[1][0] === 1){
            change = "addition";
            if ((diff[1][1] == '\n' || diff[1][1].includes(' ')) || state != 0){
                // if user add a space, the chars array will be send to the backend for processing
                changemade = difference(text[0], revisions)
                postWriterText({timestamp: time, project: projectID, file: filename, text: revisions, revision: changemade,
                state: state, cb: clipboard, line: ln})
                text = [revisions]
            }
        }
    }
}


async function postWriterText(activity) {
    console.log(activity);
    await fetch(serverURL + "/ReWARD/activity", {
            mode: 'no-cors',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: 'POST',
            body: JSON.stringify(activity),
        }, async function (err, resp, body) {
            const message = await resp.json();
            console.log(message);
            if (err) {
                console.log('Could not post writer actions.');
                console.log(err);
            }
        }
    );
}

async function generateText() {
    console.log("from main.py:");
    const response = await fetch(serverURL + "/ReWARD/activity", {
        mode: 'no-cors',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: 'GET',
    });
    console.log("from main.py:");
    const message = await response.json();
    console.log("from main.py:",message.status);
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.tabs.sendMessage(tabs[0].id, {source: "chatgpt", suggestion: message.status, same_line_before: message.same_line_before, same_line_after: message.same_line_after}, function (response) {
        });
    });
}