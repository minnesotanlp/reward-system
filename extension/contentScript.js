editor = document.getElementsByClassName("editor")[0];
console.log(editor);

let paragraph = "";
let editingParagraph = "";
let state = 0;
let pasteData = "";
let clipboardData = "";
let project_id = ""
const reg1 = /(\\author(?:\[(\d*)\])*{+[^}\n\\]+}*)/g;
const reg2 = /(\\affil(?:\[(\d*)\])*{+[^}\n\\]+}*)/g;
let file;
let filename;

let paragraphArray = [];
let edittingArray = [];

let paragraphLines = [];
let edittingLines = [];

let tooltip = null;
let tptop = null;
let tpleft = null
let lines = null;
let idx = null;
let same_line_before = ""
let same_line_after = ""

let EXTENSION_TOGGLE = true
let tpcontent = "Hello, This is a tooltip!"

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if (request.source == "chatgpt"){
            tpcontent = request.suggestion;
            same_line_before = request.same_line_before
            same_line_after = request.same_line_after
            console.log("suggetion: ", tpcontent);

            tooltip = document.createElement('div');
            tooltip.style.position = 'fixed';
            tooltip.style.top =  tptop + 'px';
            tooltip.style.left = tpleft + 'px';
            tooltip.textContent = tpcontent;
            tooltip.style.border = '1px solid black';
            tooltip.style.padding = '5px';
            tooltip.style.backgroundColor = '#FFF8DC';
            document.body.appendChild(tooltip);

            // when user click away, the tooltip disappear
            document.addEventListener('click', tooltipClick);
        }
        else{
            EXTENSION_TOGGLE = request.toggle
            if (request.toggle) {
                getEditingText();
                paragraph = editingParagraph;
                paragraphArray = edittingArray;
                paragraphLines = edittingLines;
                console.log("CONTENT ON");
            } else {
                console.log("CONTENT OFF");
            }
        }
        return true;
    }
);

document.body.addEventListener('cut', (event) => {
    console.log('***** cut ****');
    clipboardData = event.clipboardData || window.clipboardData;
    pasteData = clipboardData.getData('Text');
    state = 1;
});


document.body.addEventListener('copy', (event) => {
    console.log('***** copy ****');
    clipboardData = event.clipboardData || window.clipboardData;
    pasteData = clipboardData.getData('Text');
    state = 2;

});

document.body.addEventListener('paste', (event) => {
    console.log('***** paste ****');
    clipboardData = event.clipboardData || window.clipboardData;
    pasteData = clipboardData.getData('Text');
    state = 3;
});

function getEditingText() { // find areas in current file that reader may be reading
    editingParagraph = "";
    edittingArray = [];
    edittingLines = [];
    let textarea = document.getElementsByClassName("cm-content cm-lineWrapping");
    let linearea = document.getElementsByClassName("cm-gutter cm-lineNumbers")[0].childNodes;
    console.log(linearea);

    lines = textarea[0].childNodes;
    var length = lines.length;
    for (var k = 1; k < length; k++) {
        line = lines[k].innerText;
        if(line === "\n"){
           line = "";
        }
        if(k > 1){
            line = "\n"+line;
        }
        editingParagraph += line;
        edittingArray.push(line);
        edittingLines.push(linearea[k].textContent);
    }

    editingParagraph = editingParagraph.replace(reg1, '\\author{anonymous}');
    editingParagraph = editingParagraph.replace(reg2, '\\affil{anonymous}');
    destroy();
    console.log(editingParagraph);
    console.log(edittingArray);
    console.log(edittingLines);

    return;
}

// if user leave the current page, send Message to background.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === 'hidden') {
      if (EXTENSION_TOGGLE) {
          chrome.runtime.sendMessage({message: "hidden", revisions: editingParagraph, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray});
      }
  }
});


const scrollPost = (mutations) =>{
    if (mutations[0].target.style.top != mutations[0].oldValue.substring(22,25)){
        // console.log(mutations);
        console.log("***** scroll *****")
        getEditingText();
        if (EXTENSION_TOGGLE) {
            chrome.runtime.sendMessage({editingFile: filename, message: "scroll", revisions: editingParagraph, text: paragraph, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray});
        }
        paragraph = editingParagraph;
        paragraphArray = edittingArray;
        paragraphLines = edittingLines;
        destroy();
    }
}

// scroll mutation observer setup
let targetNode = undefined;
let config = undefined
targetNode = document.querySelector('.cm-scroller');

config = {attributeFilter: ["style"],attributeOldValue: true};
console.log(targetNode);
const scrollObserver = new MutationObserver(scrollPost);
scrollObserver.observe(targetNode, config);


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function filePost(){
    editingObserver.disconnect();
    file = document.querySelector('[aria-selected = "true"]');
    console.log(file);
    f = file.getAttribute("aria-label");
    console.log(f);

    let loadNode = document.getElementsByClassName("loading-panel ng-hide")[0];
    while (loadNode == undefined) {
        console.log("here")
        await sleep(100); // Adjust the delay time as needed
        loadNode = document.getElementsByClassName("loading-panel ng-hide")[0];
    }
    getEditingText();
    console.log(editingParagraph);
    if (EXTENSION_TOGGLE) {
        chrome.runtime.sendMessage({editingFile: filename, message: "switch", revisions: editingParagraph, text: paragraph, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray});
    }
    filename = f;
    paragraph = editingParagraph;
    paragraphArray = edittingArray;
    paragraphLines = edittingLines;
    destroy();
    editingObserver.observe(file, {attributeFilter: ["aria-selected", "selected"]});
}

const editingObserver = new MutationObserver(filePost);

window.addEventListener("load", async function(){
    paragraph = "";
    paragraphArray = [];
    paragraphLines = [];
    let loadNode = document.getElementsByClassName("loading-panel ng-hide")[0];
    while (loadNode == undefined) {
        console.log("here")
        await sleep(100); // Adjust the delay time as needed
        loadNode = document.getElementsByClassName("loading-panel ng-hide")[0];
    }
    let textarea = document.getElementsByClassName("cm-content cm-lineWrapping");
    let linearea = document.getElementsByClassName("cm-gutter cm-lineNumbers")[0].childNodes;

    // Add event listeners to detect user undo/redo action
    var inputElements = document.querySelectorAll(".cm-content.cm-lineWrapping");
    inputElements[0].addEventListener("beforeinput", function(event) {
        checkUndoOrRevert(inputElements, event);
    });

    lines = textarea[0].childNodes;
    var length = lines.length;
    for (var k = 1; k < length; k++) {
        line = lines[k].innerText;
        if(line === "\n"){
           line = "";
        }
        if(k > 1){
            line = "\n"+line;
        }
        paragraph += line;
        paragraphArray.push(line);
        paragraphLines.push(linearea[k].textContent);
    }
    paragraph = paragraph.replace(reg1, '\\author{anonymous}');
    paragraph = paragraph.replace(reg2, '\\affil{anonymous}');

    console.log(paragraph)
    console.log(paragraphLines)
    // valid for both legacy and non-legacy
    project_id = document.querySelector('meta[name="ol-project_id"]').content
    file = document.querySelector('[aria-selected = "true"]');
    filename = file.getAttribute("aria-label");
    console.log("load");
    chrome.storage.local.get('enabled', function (result) {
        var checking = false
        if (result.enabled != null) {
            checking = result.enabled;
        }
        if (checking){
            EXTENSION_TOGGLE = true
        }
        else if (!checking){
            destroy();
        }
    })
    const fileObserver = new MutationObserver(filePost);
    const fileConfig = {attributeFilter: ["aria-selected", "selected"]};
    fileObserver.observe(file, fileConfig);
});


//remove tooltip
function tooltipClick(event) {
  if (tooltip && !tooltip.contains(event.target)) {
    tooltip.parentNode.removeChild(tooltip);
    tooltip = null;
    document.removeEventListener('click', tooltipClick);
    chrome.runtime.sendMessage({message: "user_selection", accept: false});
  }
  else if (tooltip && tooltip.contains(event.target)){
    console.log("1: ",same_line_before);
    console.log("2: ",tpcontent);
    console.log("3: ",same_line_after);
    lines[idx].innerText = same_line_before+tpcontent+same_line_after;
    tooltip.parentNode.removeChild(tooltip);
    tooltip = null;
    document.removeEventListener('click', tooltipClick);
    chrome.runtime.sendMessage({message: "user_selection", accept: true});
  }
}

let excludedKeys = ["Meta", "Alt", "Tab","Shift","CapsLock","ArrowUp", "Control", "ArrowDown", "ArrowLeft","ArrowRight"];

document.body.onkeyup = function (e) { // save every keystroke
    if (e.key === 'F4') {
        // get selected information such as html element, text, and position relative to viewers' screen
        var selected_element = window.getSelection();
        var selected_text = selected_element.toString();
        var selected_range = selected_element.getRangeAt(0); //get the text range
        var selected_pos = selected_range.getBoundingClientRect();

        // get all the lines and number of lines
        const cm_content = document.getElementsByClassName("cm-content cm-lineWrapping");
        console.log(selected_text);
        console.log("--------------------------------");
        lines = cm_content[0].childNodes;
        var length = lines.length;
        console.log(length)
        console.log(selected_range.startContainer);
        console.log(selected_range.endContainer);
        console.log("--------------------------------");
        console.log(selected_pos);
        var i = 0;
        var j = 0;
        var breakCheck;

        // algorithm to get the selected line.
        // This could help us get the context and feed into Chatgpt
        for (; i<length; i++){
            var line_child = lines[i].childNodes;
            for (var k = 0; k < line_child.length; k++ ){
                var component = line_child[k].textContent;
                console.log(component);
                if (component == ""){
                    k = k + 2;
                }else if (component == undefined){
                    continue;
                }
                if (component === selected_range.startContainer.data){
                    console.log("here");
                    console.log(lines[i]);
                    var found_range = lines[i].ownerDocument.createRange();
                    found_range.selectNodeContents(lines[i]);
                    console.log(found_range.getClientRects());
                    if (found_range.getClientRects()[j].x === selected_pos.x){
                        breakCheck = 1;
                        break;
                    }
                    else{
                        j = j + 1;
                    }
                }
            }
            if(breakCheck == 1){break;}
        }
        // the line user want to help with
        console.log(i+1);
        console.log("----------------------------------");

        // get text comes before and after selection
        var line = "";
        var pre_content = "";
        var pos_content = "";
        for (var k = 0; k < length; k++) {
            line = lines[k].innerText;
            if (line == "\n" && k < length -1){
                line = "\n\n";
            }
            if (k < i){
                pre_content += line;
            }
            else if (k > i){
                pos_content += line;
            }
        }
        pre_content = pre_content.replace(reg1, '\\author{anonymous}');
        pre_content = pre_content.replace(reg2, '\\affil{anonymous}');
        pos_content = pos_content.replace(reg1, '\\author{anonymous}');
        pos_content = pos_content.replace(reg2, '\\affil{anonymous}');

        console.log(pre_content);
        console.log(lines[i].innerText);
        console.log(pos_content);

        tptop = selected_pos.y + selected_pos.height;
        tpleft = selected_pos.x + selected_pos.width;
        idx = i;

        chrome.runtime.sendMessage({editingFile: filename,message: "assist", pre_content: pre_content, pos_content: pos_content,
        selected_text: selected_text, current_line_content: lines[i].innerText, project_id: project_id, line: i+1});

      }
    else if (!excludedKeys.includes(e.key)){
        project_id = document.querySelector('meta[name="ol-project_id"]').content
        destroy();
        if (EXTENSION_TOGGLE) {
            getEditingText();
            if(state == 1){
            console.log(e.key);
            chrome.runtime.sendMessage({editingFile: filename,message: "cut", revisions: editingParagraph, text: paragraph, cutted: pasteData, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray, project_id: project_id, onkey: e.key});
            state = 0
            }
            else if(state == 2){
                console.log(e.key);
                chrome.runtime.sendMessage({editingFile: filename, message: "copy", revisions: editingParagraph, text: paragraph, copied: pasteData, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray, project_id: project_id, onkey: e.key});
                state = 0
            }
            else if(state == 3){
                console.log(e.key);
                chrome.runtime.sendMessage({editingFile: filename, message: "paste", revisions: editingParagraph, text: paragraph, pasted: pasteData, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray, project_id: project_id, onkey: e.key});
                state = 0
            }
            else{
                console.log(e.key);
                chrome.runtime.sendMessage({editingFile: filename, message: "listeners", revisions: editingParagraph, text: paragraph,  edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray, project_id: project_id, onkey: e.key});
            }
            paragraph = editingParagraph;
            paragraphArray = edittingArray;
            paragraphLines = edittingLines;
        }
    }
}

function checkUndoOrRevert(element, event) {
  console.log("Input type: ", event.inputType);
  if (event.inputType === "historyUndo" || event.inputType === "historyRedo") {
    console.log("Undo or revert event detected");
    getEditingText();
    if (EXTENSION_TOGGLE) {
        chrome.runtime.sendMessage({editingFile: filename, message: "undo", revisions: editingParagraph, text: paragraph, edittingLines: edittingLines, edittingArray: edittingArray, paragraphLines: paragraphLines, paragraphArray: paragraphArray});
    }
    paragraph = editingParagraph;
    paragraphArray = edittingArray;
    paragraphLines = edittingLines;
    destroy();
    }
}

function destroy() {
    if (!EXTENSION_TOGGLE) {
        paragraph = "";
        editingParagraph = "";
        paragraphArray = [];
        edittingArray = [];
        project_id = ""
        paragraphLines = [];
        edittingLines = [];
    }
}