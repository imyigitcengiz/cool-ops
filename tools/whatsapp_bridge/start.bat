@echo off
cd /d "%~dp0"
if not exist node_modules (
  echo npm install calistiriliyor...
  call npm install
)
echo WhatsApp koprusu baslatiliyor: http://127.0.0.1:3939
node server.js
