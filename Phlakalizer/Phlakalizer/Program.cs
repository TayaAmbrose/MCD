using System;
using System.Diagnostics;
using System.Diagnostics.Eventing.Reader;
using System.IO;
using System.Threading; // Required for Thread.Sleep

namespace LogGetter
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                FindAndExecuteScriptsInSubfolders(); // If no arguments, find and execute scripts in subfolders
            }
            else
            {
                string scriptFileName = args[0];
                ExecutePowerShellScript(scriptFileName); // Otherwise, execute the script from the argument
            }
        }

        static void FindAndExecuteScriptsInSubfolders()
        {
            string currentDirectory = Directory.GetCurrentDirectory();
            string[] subDirectories = Directory.GetDirectories(currentDirectory);

            if (subDirectories.Length == 0)
            {
                Console.WriteLine("No subfolders found in the current directory.");
                return;
            }

            Console.WriteLine("Searching for PowerShell scripts in subfolders...");

            foreach (string subDirectory in subDirectories)
            {
                string[] scriptFiles = Directory.GetFiles(subDirectory, "*.ps1");
                if (scriptFiles.Length > 0)
                {
                    Console.WriteLine($"\nFound PowerShell scripts in subfolder: {subDirectory}");
                    foreach (string scriptFile in scriptFiles)
                    {
                        Console.WriteLine($"Executing script: {scriptFile}");
                        ExecutePowerShellScript(scriptFile);
                        Console.WriteLine($"Finished executing script: {scriptFile}\n");
                    }
                }
                else
                {
                    Console.WriteLine($"No PowerShell scripts found in subfolder: {subDirectory}");
                }
            }

            Console.WriteLine("Finished searching and executing scripts in subfolders.");
        }


        static void GetPowerShellLogs(DateTime startTime, DateTime endTime, string logBaseFileName, string scriptDirectory)
        {
            string logPath = @"%SystemRoot%\System32\Winevt\Logs\Microsoft-Windows-PowerShell%4Operational.evtx";
            //Adjust the time window to capture logs during the script execution and a bit after.
            //Using UTC time for consistency in query.
            string startTimeUTC = startTime.ToUniversalTime().ToString("o");
            string endTimeUTC = endTime.ToUniversalTime().ToString("o");
            string query = $"*[System[TimeCreated[@SystemTime >= '{startTimeUTC}' and @SystemTime <= '{endTimeUTC}']]]";


            EventLogQuery eventsQuery = new EventLogQuery(logPath, PathType.FilePath, query);
            EventLogReader logReader = new EventLogReader(eventsQuery);

            string logFilePath = Path.Combine(scriptDirectory, $"{logBaseFileName}_powershell_event_log.txt");
            try
            {
                Console.WriteLine(logFilePath);
                using (StreamWriter logWriter = new StreamWriter(logFilePath, true))
                {
                    logWriter.WriteLine($"--- PowerShell Event Log started at {DateTime.Now} ---");
                    for (EventRecord eventInstance = logReader.ReadEvent(); eventInstance != null; eventInstance = logReader.ReadEvent())
                    {
                        logWriter.WriteLine($"Event ID: {eventInstance.Id}");
                        logWriter.WriteLine($"Level: {eventInstance.LevelDisplayName}");
                        logWriter.WriteLine($"Time Created: {eventInstance.TimeCreated}");
                        logWriter.WriteLine($"Message: {eventInstance.FormatDescription()}");
                        logWriter.WriteLine("---------------------------------------------------");
                    }
                    logWriter.WriteLine($"--- PowerShell Event Log ended at {DateTime.Now} ---");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading PowerShell event logs: {ex.Message}");
                // Optionally log the error to a separate error log file.
            }
        }

        static void ExecutePowerShellScript(string scriptFileName)
        {
            DateTime scriptStartTime = DateTime.Now; // Record start time before process starts.
            string logBaseFileName = $"script_log_{DateTime.Now.ToString("yyyyMMdd_HHmmss")}";

            string scriptDirectory = Path.GetDirectoryName(scriptFileName);
            if (string.IsNullOrEmpty(scriptDirectory))
            {
                scriptDirectory = Directory.GetCurrentDirectory(); // Default to current directory if script path is just filename.
            }

            string processLogFilePath = Path.Combine(scriptDirectory, $"{logBaseFileName}_process_log.txt");

            ProcessStartInfo startInfo = new ProcessStartInfo()
            {
                FileName = "powershell.exe",
                Arguments = $"-NoProfile -ExecutionPolicy Bypass -File \"{scriptFileName}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (Process process = new Process())
            {
                process.StartInfo = startInfo;

                try
                {
                    using (StreamWriter processLogWriter = new StreamWriter(processLogFilePath, true))
                    {
                        processLogWriter.WriteLine($"--- Process Log started at {DateTime.Now} ---");
                        processLogWriter.WriteLine($"User: {Environment.UserName}");
                        processLogWriter.WriteLine($"Machine: {Environment.MachineName}");
                        processLogWriter.WriteLine($"Script: {scriptFileName}");
                        processLogWriter.WriteLine($"PID (LogGetter): {Process.GetCurrentProcess().Id}");
                        processLogWriter.WriteLine($"Command Line: {startInfo.FileName} {startInfo.Arguments}"); // Log the command line
                        processLogWriter.WriteLine($"Start Time (Script Execution): {scriptStartTime}");

                        process.OutputDataReceived += (sender, e) =>
                        {
                            if (!string.IsNullOrEmpty(e.Data))
                            {
                                Console.WriteLine(e.Data);
                                processLogWriter.WriteLine(e.Data);
                            }
                        };
                        process.ErrorDataReceived += (sender, e) =>
                        {
                            if (!string.IsNullOrEmpty(e.Data))
                            {
                                Console.WriteLine("ERROR: " + e.Data);
                                processLogWriter.WriteLine("ERROR: " + e.Data);
                            }
                        };

                        process.Start();

                        process.BeginOutputReadLine();
                        process.BeginErrorReadLine();

                        if (!process.WaitForExit(60000)) // Wait for 1 minute (60000 milliseconds)
                        {
                            process.Kill();
                            Console.WriteLine("Process terminated due to timeout.");
                            processLogWriter.WriteLine("Process terminated due to timeout.");
                        }

                        Thread.Sleep(1000); // Wait for 1 second between script executions
                        DateTime scriptEndTime = DateTime.Now; // Record end time after process exits.
                        processLogWriter.WriteLine($"End Time (Script Execution): {scriptEndTime}");
                        processLogWriter.WriteLine($"Exit Code: {process.ExitCode}"); // Log the exit code
                        processLogWriter.WriteLine($"--- Process Log ended at {DateTime.Now} ---");

                        GetPowerShellLogs(scriptStartTime, scriptEndTime, logBaseFileName, scriptDirectory); // Pass script directory to log function
                        Phlakalizer.CuckooIOCGetter getter = new Phlakalizer.CuckooIOCGetter();
                        getter.Getter(scriptFileName); // Fetch the cuckooLogs using the script name
                    }

                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error executing PowerShell script: {ex.Message}");
                    // Optionally log the error to a separate error log file.
                }
            }
        }
    }
}