:LOOP
if exist new.exe (
    del process.exe
    move new.exe process.exe
)
process.exe
goto LOOP
