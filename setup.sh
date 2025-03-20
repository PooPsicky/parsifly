#!/bin/bash
pip install --upgrade pip
pip install playwright
playwright install --with-deps chromium
playwright install-deps
