# paper2html

[![License: GPLv2+](https://img.shields.io/badge/license-GPLv2+-yellow)](https://opensource.org/licenses/GPL-2.0)
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
Please set the `Poppler for Windows` path(ex.`C:\Users\YOUR_NAME\Downloads\poppler-0.68.0\bin`) in the PATH environment variable.

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

NOTE👉 If you are running a paper2html server on Docker, you will not be able to convert PDF file on the host OS with the bookmarklet. See [docker image doc](docker/README.md).

### Conversion local PDF to html with CLI

Run this command, then open the html file in your browser.

```shell
$ python paper2html/commands.py "path-to-paper-file.pdf"
```

In IPython, do it like this.

```pycon
>>> import paper2html
>>> paper2html.open_paper_htmls("path-to-paper-file.pdf")
```

You can use specific browser.

```shell
$ python paper2html/commands.py "path-to-paper-file.pdf" --browser_path="/path/to/browser"
```

You can also only convert without opening a browser.

```pycon
>>> import paper2html
>>> paper2html.paper2html("path-to-paper-file or directory")
```

## External Libraries used by paper2html

Thank to the following libraries used by paper2html.

- Poppler is distributrd under the GPLv2+ license. (Copyright 2005-2020 [The Poppler Developers](http://poppler.freedesktop.org) &
Copyright 1996-2011 Glyph & Cog, LLC)
- Pdfminer.six is distributrd under the MIT license. (Copyright © 2004-2016  Yusuke Shinyama <yusuke at shinyama dot jp>)
- pdf2image is distributrd under the MIT license. (Copyright © 2017 Edouard Belval)
- pillow is distributed under the [PIL](https://github.com/python-pillow/Pillow/blob/master/LICENSE) license. (Copyright © 1997-2011 by Secret Labs AB & Copyright © 1995-2011 by Fredrik Lundh)
- The license of matplotlib is based on the [PSF](https://docs.python.org/3/license.html) license. (Copyright © 2002 - 2012 John Hunter, Darren Dale, Eric Firing, Michael Droettboom and the Matplotlib development team; 2012 - 2021 The Matplotlib development team.)
- Flask is licensed under the 3C BSD license. (Copyright © 2016, opentracing-contrib.)
- Watchdog is licensed under the terms of the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0). (Copyright © 2011 Yesudeep Mangalapilly & Copyright 2012 Google, Inc & contributors.)
- Python Fire is Licensed under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0). (Copyright © 2017 Google Inc. All rights reserved.)


## License
The entire source code of paper2html is compatible with the GPL v3 or later license. (see LICENSE for details)

[comment]: <> (The website content is licensed under CC BY 4.0. &#40;see LICENSE&#41;.)
[comment]: <> (Copyright &#40;C&#41; 2021 eitsupi)
