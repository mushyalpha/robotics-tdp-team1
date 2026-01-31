@echo off
REM WSL IP address
set WSL_IP=172.28.57.9

echo Starting goalie...
start /B python main.py --goalie --host %WSL_IP%

timeout /t 1 /nobreak >nul

for /L %%i in (2,1,11) do (
    echo Starting player %%i...
    start /B python main.py --player --host %WSL_IP%
    timeout /t 1 /nobreak >nul
)

timeout /t 2 /nobreak >nul
echo Starting coach...
start /B python main.py --coach --host %WSL_IP%
