#### For Prompting the LLM ####


from openai import OpenAI
import os

def use_existing_assistant(assistant_id):
    # Initialize the OpenAI client with your API key
    client = OpenAI(api_key="API KEY HERE")
    
    try:
        # Create a thread to interact with the existing assistant
        thread = client.beta.threads.create()
        
        # PowerShell function to analyze (directly in the script)
        powershell_function = """ ADD FUNCTION HERE                    ADD FUNCTION HERE                    ADD FUNCTION HERE
        """
        
        # Send the PowerShell function to be analyzed
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Please analyze this command: {powershell_function}"
        )
        
        # Run the assistant on this thread
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        print(f"PowerShell function sent to assistant {assistant_id} for analysis.")
        print(f"Thread ID: {thread.id}")
        print(f"Run ID: {run.id}")
        print("Check the OpenAI dashboard to view results, or use the API to retrieve the assistant's response.")
        
        return thread.id, run.id
    
    except Exception as e:
        print(f"Error using assistant: {str(e)}")
        return None, None

if __name__ == "__main__":
    # Use your existing assistant ID
    EXISTING_ASSISTANT_ID = "ASSISTANT ID HERE"
    
    thread_id, run_id = use_existing_assistant(EXISTING_ASSISTANT_ID)
    if thread_id and run_id:
        print(f"You can check the analysis results using the thread and run IDs above.")
        print(f"The assistant will analyze the PowerShell function.")








#### For Reading the Results ####

# from openai import OpenAI
# import time

# def get_assistant_response(thread_id, run_id):
#     # Initialize the OpenAI client
#     client = OpenAI(api_key="API KEY HERE")  # Replace with API key
    
#     # Check the run status and wait for completion
#     while True:
#         run = client.beta.threads.runs.retrieve(
#             thread_id=thread_id,
#             run_id=run_id
#         )
        
#         if run.status == "completed":
#             break
#         elif run.status == "failed":
#             print(f"Run failed with error: {run.last_error}")
#             return None
        
#         print(f"Run status: {run.status}. Waiting...")
#         time.sleep(2)  # Wait 2 seconds before checking again
    
#     # Retrieve messages after the run is complete
#     messages = client.beta.threads.messages.list(
#         thread_id=thread_id
#     )
    
#     # Filter for assistant messages (responses)
#     assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
    
#     # Print the most recent response
#     if assistant_messages:
#         latest_response = assistant_messages[0]
#         print("\n=== ASSISTANT RESPONSE ===\n")
        
#         for content_item in latest_response.content:
#             if content_item.type == "text":
#                 print(content_item.text.value)
                
#         return latest_response
#     else:
#         print("No assistant responses found.")
#         return None

# if __name__ == "__main__":
#     # Replace these with your actual thread and run IDs
#     THREAD_ID = "THREAD ID HERE"  # Your thread ID
#     RUN_ID = "RUN ID HERE"  # Your run ID
    
#     response = get_assistant_response(THREAD_ID, RUN_ID)

    