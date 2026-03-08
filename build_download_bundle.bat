@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0build_download_bundle.ps1" %*
