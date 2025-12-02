#!/usr/bin/env pwsh
Set-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Path -Parent)/.. 
python main.py
