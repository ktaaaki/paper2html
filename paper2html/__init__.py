# -*- coding:utf-8 -*-
# paper2html/paper2html/__init__.py
# This file is licensed under the MIT license (see LICENSE_MIT for details)
# Copyright (C) 2021 ktaaaki

from .commands import open_paper_htmls, message_for_automator, paper2html
from .convert_service import convert_service_run

name = "paper2html"
__version__ = '0.4.1'
__all__ = ['open_paper_htmls', 'message_for_automator', 'paper2html', 'convert_service_run']

