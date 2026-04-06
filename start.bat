@echo off 

set Lib=.venv\Lib\
(
    echo set Scripts=.venv\Scripts\
    echo set Lib=.venv\Lib\
    echo set python=%%Scripts%%python.exe
    echo set target=src\__init__.py

    echo call %%Scripts%%activate.bat
    echo %%python%% %%target%%
    echo call %%Scripts%%deactivate.bat
) > %Lib%execute.bat

wscript.exe "%Lib%invisible.vbs" "%Lib%execute.bat"
