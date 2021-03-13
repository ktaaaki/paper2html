# paper2html

[![License: AGPL](https://img.shields.io/badge/license-AGPL-yellow)](https://opensource.org/licenses/AGPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.6|3.7|3.8|3.9-blue)](https://github.com/ktaaaki/paper2html)
[![Platform](https://img.shields.io/badge/platform-windows|macos|linux-blue)](https://github.com/ktaaaki/paper2html)

Convert a PDF paper to html page.  
You can translate the paper easily by browser functions, and you can view the original document and the translated document at the same time.

![work_on_edge](https://user-images.githubusercontent.com/50911393/110310478-f2d3d600-8045-11eb-9f97-4f8bbfd5ec3a.gif)

Albanie, Samuel, Sébastien Ehrhardt, and Joao F. Henriques. "Stopping gan violence: Generative unadversarial networks." arXiv preprint arXiv:1703.02528 (2017).

## Features

- Convert PDF files on the Internet easily by using a bookmarklet.
- Support for double-column papers.

## Installing and running paper2html server

### Docker

```shell
$ docker run --rm -it -p 5000:5000 ghcr.io/ktaaaki/paper2html
```

Use with care as it opens up the port.

### Debian GNU/Linux, Ubuntu

```shell
$ sudo apt install poppler-utils poppler-data
$ git clone https://github.com/ktaaaki/paper2html.git
$ pip install -e paper2html
$ python3 ./paper2html/main.py
```

### macOS

```shell
$ brew install poppler
$ git clone https://github.com/ktaaaki/paper2html.git
$ pip install -e paper2html
$ python3 ./paper2html/main.py
```

### Windows

Download `Poppler for Windows` binary file from <http://blog.alivate.com.au/poppler-windows/>  
Please set the `Poppler for Windows` path(ex.`C:¥Users¥YOUR_NAME¥Downloads¥poppler-0.68.0¥bin`) in the PATH environment variable.

Verify that the path is displayed with the following command.

```powershell
> where.exe pdfinfo
```

Download the zip file or use `git clone` command to save the paper2html code locally, and then install it using the following command.

```powershell
> py -m pip -e paper2html
> python .\paper2html\main.py
```

## Usage

### Conversion PDF on the web to html with paper2html server

Upload a PDF file to the server by using this bookmarklet.

```js
javascript:var esc=encodeURIComponent;var d=document;var subw=window.open('http://localhost:5000/paper2html/convert?url='+esc(location.href)).document;
```

Click on the bookmarklet when you open a PDF paper in your browser.  
Then the conversion will start and the generated html will be opened after a while.

You can see the list of converted documents in the index page `localhost:5000/paper2html/index.html`

NOTE👉 If you are running a paper2html server on Docker, you will not be able to convert PDF file on the host OS in a browser.(#19)

### Conversion local PDF to html with CLI

Run this command, then open the html file in your browser.

```shell
$ python paper2html/commands.py "path-to-paper-file.pdf"
```

In IPython, do it like this.

```py
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```

You can use specific browser.

```shell
$ python paper2html/commands.py "path-to-paper-file.pdf" --browser_path="/path/to/browser"
```

You can also only convert without opening a browser.

```py
>>> import paper2html
>>> paper2html.paper2html("path-to-paper-file or directory")
```
