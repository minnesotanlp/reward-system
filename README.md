# Decoding the End-to-end Writing Trajectory in Scholarly Manuscripts

This repository provides Chrome extension and annotation code of the following paper:

> [Decoding the End-to-end Writing Trajectory in Scholarly Manuscripts](https://arxiv.org/pdf/2304.00121.pdf) <br>
> Ryan Hyunkyo Koo, 
Anna Martin, 
Linghe Wang, Dongyeop Kang <br>
> [The Second Workshop on Intelligent and Interactive Writing Assistants (In2writing)](https://in2writing.glitch.me/) <br>
> [Demo](https://minnesotanlp.github.io/REWARD_demo/)

### Future Development
This repository will no longer have any new commits. For all future updates of Chrome extension and server application, please checkout this repository link: [https://github.com/minnesotanlp/scholawrite](https://github.com/minnesotanlp/scholawrite)

### Requirements
You will need to install flask==2.1.3, werkzeug==2.1.2, and flask-restx. Installing flask may automatically install a newer version of werkzeug. Werkzeug can be downgraded by running `pip install werkzeug==2.1.2`.

### Installation Instructions

* To run the development environment, run `FLASK_APP=App.py flask run` in the root directory
* Then make sure the chrome extension is loaded. 
* If problems are seen with some packages not being seen, `npm install` all packages in the `package.json` in the `/extension` folder

### Loading and Using the Chrome Extension

Once the server is running, you can load the Chrome extension, open Overleaf in Chrome, start writing in a document, and watch the extension capture writer actions in your terminal.
* To load the Chrome extension, go to [chrome://extensions/](chrome://extensions/) in your Chrome browser. Make sure `Developer mode` is toggled on in the upper right corner. In the upper left, select `Load unpacked`. This will bring up a directory listing. Select the folder called `extension` inside your `REWARD` directory.
* Once you have loaded the extension from your directory, you can use it. Open a document in Overleaf, then click the `extensions` button in the upper right corner of your Chrome browser (the button looks like a puzzle piece). Choose ReWARD from the drop down list. Once you have selected the extension, changes you make to the document will be logged in the terminal you are running the server from. 


## Contributors

* [Ryan Koo](mailto:koo00017@umn.edu)
* [Anna Martin](mailto:mart5877@umn.edu)
* [Linghe Wang](mailto:wang9257@umn.edu)
* [Dongyeop Kang](mailto:dongyeop@umn.edu)


## Citation

```
@inproceedings{
  koo2023decoding,
    title={Decoding the End-to-end Writing Trajectory in Scholarly Manuscripts},
    author={Ryan Hyunkyo Koo and Anna Martin and Linghe Wang and Dongyeop Kang},
    booktitle={The Second Workshop on Intelligent and Interactive Writing Assistants},
    year={2023},
  }
```
