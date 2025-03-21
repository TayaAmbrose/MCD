import requests
import json
import os
from datetime import datetime

api_key = "dd401e188b8d9e8c7a26416e92a2c2820cfe3591"  # Replace with your actual API key if needed
analyses_url = "http://127.0.0.1:8090/analyses/"
analysis_report_url_base = "http://127.0.0.1:8090/analysis/"
task_post_url_base = "http://127.0.0.1:8090/analysis/"

headers = {
    "Authorization": f"token {api_key}",
    "Content-Type": "application/json"
}

task_post_payload = {
    "settings": {
        "dump_memory": False,
        "platforms": [
            {
                "os_version": "10",
                "tags": [],
                "platform": "windows"
            }
        ],
        "enforce_timeout": True,
        "options": {},
        "manual": True,
        "timeout": 300,
        "machines": [],
        "priority": 1,
        "extrpath": []
    },
    "state": "finished"
}


try:
    # --- Fetch Analyses List (same as before) ---
    response_analyses_list = requests.get(analyses_url, headers=headers)
    response_analyses_list.raise_for_status()
    analyses_data = response_analyses_list.json()

    finished_analyses = {}
    for analysis in analyses_data.get("analyses", []):
        if analysis.get("state") == "finished":
            target_item = analysis.get("target", {}).get("target")
            created_on_str = analysis.get("created_on")
            if target_item and created_on_str:
                created_on = datetime.fromisoformat(created_on_str.replace("Z", "+00:00"))

                if target_item not in finished_analyses or created_on > finished_analyses[target_item]["created_on"]:
                    finished_analyses[target_item] = {
                        "id": analysis.get("id"),
                        "created_on": created_on,
                        "target_item": target_item
                    }

    unique_analysis_ids = [analysis_info["id"] for analysis_info in finished_analyses.values()]

    print("Unique and Latest Finished Analysis IDs:")
    for analysis_id in unique_analysis_ids:
        print(analysis_id)

    print("\nExecuting POST requests and saving output for tasks in each analysis...")

    # --- Fetch Analysis Report and Process Tasks, now making POST requests and saving output ---
    for analysis_id in unique_analysis_ids:
        analysis_report_url = f"{analysis_report_url_base}{analysis_id}"
        response_analysis_report = requests.get(analysis_report_url, headers=headers)
        response_analysis_report.raise_for_status()
        analysis_report_data = response_analysis_report.json()

        tasks = analysis_report_data.get("tasks", [])
        if tasks:
            # Find the analysis info that matches the current analysis_id to get target_item
            analysis_info_for_id = None
            for info in finished_analyses.values():
                if info["id"] == analysis_id:
                    analysis_info_for_id = info
                    break
            if analysis_info_for_id:
                analysis_target_item = analysis_info_for_id["target_item"]
                # Sanitize filename - replace invalid characters with underscore
                output_filename_base = "".join(c if c.isalnum() or c in ['.', '-', '_'] else '_' for c in analysis_target_item)
                output_filename = f"{output_filename_base}.txt"
                output_filepath = output_filename # Save in the current directory

                print(f"\nTasks for analysis ID: {analysis_id}, Target: {analysis_target_item}")
                with open(output_filepath, "w") as outfile:
                    for task in tasks:
                        task_id = task.get("id")
                        if task_id:
                            task_post_url = f"{task_post_url_base}{analysis_id}/task/{task_id}/post"

                            try:
                                response_task_post = requests.get(task_post_url, headers=headers, json=task_post_payload)
                                response_task_post.raise_for_status()
                                print(f"  POST request for task ID: {task_id} successful!")
                                response_json = response_task_post.json()
                                outfile.write(f"Task ID: {task_id}\n")
                                outfile.write(json.dumps(response_json, indent=2))
                                outfile.write("\n--------------------\n")
                                print("  Response content written to file.")

                            except requests.exceptions.RequestException as post_error:
                                print(f"  Error during POST request for task ID: {task_id}")
                                print(f"  Error: {post_error}")
                                if hasattr(post_error.response, 'text'):
                                    print("  Response content (if available):")
                                    print(post_error.response.text)
                                    outfile.write(f"Task ID: {task_id} - Error\n")
                                    outfile.write(f"  Error: {post_error}\n")
                                    outfile.write("  Response content (if available):\n")
                                    outfile.write(post_error.response.text)
                                    outfile.write("\n--------------------\n")
                                else:
                                    print("  No response content available due to request exception.")
                                    outfile.write(f"Task ID: {task_id} - Error\n")
                                    outfile.write(f"  Error: {post_error}\n")
                                    outfile.write("  No response content available due to request exception.\n")
                                    outfile.write("\n--------------------\n")


                        else:
                            print(f"  Warning: Task ID not found for a task in analysis {analysis_id}")
                            outfile.write(f"Warning: Task ID not found for a task in analysis {analysis_id}\n")
                            outfile.write("\n--------------------\n")

                print(f"  Output for analysis ID: {analysis_id} saved to: {output_filepath}")
            else:
                print(f"Error: Could not find analysis info for ID: {analysis_id} in finished_analyses dictionary. This should not happen.")


        else:
            print(f"  No tasks found for analysis ID: {analysis_id}")


except requests.exceptions.RequestException as e:
    print(f"An error occurred during the initial GET request (analyses list or report): {e}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON response: {e}")
    print("Response text:")
    print(response.text)