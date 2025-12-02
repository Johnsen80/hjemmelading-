#!/usr/bin/env pwsh
Set-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Path -Parent)/.. 
python -m pip install -r requirements-dev.txt
python -m pytest -q
