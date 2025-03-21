import os

def process_folders(parent_folder):
    files_paths = []
    exec_commands = []
    
    # Convert parent_folder to an absolute path
    parent_folder = os.path.abspath(parent_folder)
    
    for folder_name in os.listdir(parent_folder):
        folder_path = os.path.join(parent_folder, folder_name)
        
        if os.path.isdir(folder_path):
            readme_path = os.path.join(folder_path, 'readme.txt')
            
            if os.path.isfile(readme_path):
                with open(readme_path, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    if line.startswith("Name: "):
                        file_name = line.split("Name: ")[1].strip()
                        full_file_path = os.path.join(folder_path, file_name)
                        files_paths.append(full_file_path)
                        exec_command = f'powershell -noexit -ExecutionPolicy bypass -File "{full_file_path}"'
                        exec_commands.append(exec_command)
    
    # Write file_paths to output.txt
    with open("output.txt", "w") as output_file:
        for path in exec_commands:
            output_file.write(path + "\n")
    
    return files_paths, exec_commands

parent_folder = "..\\Commands"  # Relative path to your folder location
files_paths, exec_commands = process_folders(parent_folder)
print("Execution Commands:", exec_commands)