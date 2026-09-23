"""
/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment(Python)
 *                          Description: Handles the parsing, adding, and updating of the resumes metadata and text on to the ChromaDB collection(using regex expressions alongside AI)
 *                          Created Date: March 27, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 31, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
"""
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from Process_Upload_Functions.upload_file_regex import process_resumes_regex_from_stream, print_collection_summary, collection
from Process_Upload_Functions.azure_storage_utils import (
    get_blob_container_client,
    list_blobs_in_container,
    download_blob_to_stream
)

load_dotenv()

test_data_folder = os.getenv('TEST_SAMPLE_DATA_FOLDER')
run_process_with_AI = os.getenv('USE_AI_FUNCTION', 'True').lower() == 'true'
run_process_with_regex = os.getenv('USE_REGEX_FUNCTION', 'False').lower() == 'true'
share_name = os.getenv('AZURE_SHARE_NAME')
batch_amount = int(os.getenv('AZURE_STORAGE_BATCH_SIZE'))


def load_saved_file_list(file_path):
    """Load the saved file list from the BlobStorage_File_List.txt file."""
    if os.path.exists(file_path):
        # Check if the file is empty
        if os.stat(file_path).st_size == 0:
            return {}  # Return an empty dictionary if the file is empty
        with open(file_path, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
            # Convert ISO 8601 strings back to datetime objects
            return {
                key: datetime.fromisoformat(value) if isinstance(value, str) else value
                for key, value in file_list.items()
            }
    return {}

def save_file_list(file_path, file_list):
    """Save the updated file list to the BlobStorage_File_List.txt file."""
    # Convert datetime objects to ISO 8601 strings
    serializable_file_list = {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in file_list.items()
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_file_list, f, indent=4)

class ResumeProcessor:
    def __init__(self, resumes_folder):
        self.resumes_folder = resumes_folder

    def process_with_AI(self, enabled=True):
        """
        Process resumes using the `process_resumes` function from `upload_file_AI.py`.
        """
        if enabled:
            print("\n--- Processing Resumes with AI ---")
            # process_resumes_AI(self.resumes_folder)
            print("--- Finished Processing with AI ---\n")
    
    def process_with_regex(self, batch_size, enabled=True):
        """
        Process resumes using the `process_resumes` function from `upload_file_regex.py`.
        """
        if enabled:
            print("\n--- Processing Resumes with Blob Storage Stream in Batches ---")
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            container_name = os.getenv('AZURE_BLOB_NAME')
            container_client = get_blob_container_client(connection_string, container_name)

            if not container_client:
                print("Failed to initialize container client.")
                return

            # Path to the saved file list
            # saved_file_list_path = "Process_Upload_Functions/BlobStorage_File_List.txt"
            saved_file_list_path = os.getenv('AZURE_BLOB_STORAGE_LOGS')

            # Load the saved file list or initialize it if the file doesn't exist or is empty
            saved_file_list = load_saved_file_list(saved_file_list_path)

            # Generate the full list of files from the storage
            blob_list = list_blobs_in_container(container_client, prefix="resume/")
            total_files = len(blob_list)
            print(f"Total files to process: {total_files}")

            # Process files in batches
            for i in range(0, total_files, batch_size):
                batch = blob_list[i:i + batch_size]  # Get the current batch of files
                print(f"\nProcessing batch {i // batch_size + 1} (files {i + 1} to {min(i + batch_size, total_files)})...")

                for index, blob_info in enumerate(batch):
                    blob_name = blob_info["name"]
                    last_modified = blob_info["last_modified"]
                    file_number = i + index + 1
                    try:
                        # Ensure last_modified is a datetime object
                        if isinstance(last_modified, str):
                            last_modified_date = datetime.fromisoformat(last_modified)
                        elif isinstance(last_modified, datetime):
                            last_modified_date = last_modified
                        else:
                            raise ValueError(f"Unexpected type for last_modified: {type(last_modified)}")

                        # Check if the file needs to be processed
                        saved_last_modified = saved_file_list.get(blob_name)
                        if saved_last_modified:
                            if isinstance(saved_last_modified, str):
                                saved_last_modified_date = datetime.fromisoformat(saved_last_modified)
                            elif isinstance(saved_last_modified, datetime):
                                saved_last_modified_date = saved_last_modified
                            else:
                                raise ValueError(f"Unexpected type for saved_last_modified: {type(saved_last_modified)}")
                            
                            # Debug print statements to check the values
                            print(f"DEBUG: Comparing saved_last_modified_date ({saved_last_modified_date}) "
                                f"with last_modified_date ({last_modified_date}) for {blob_name}")

                            # Compare the dates
                            if saved_last_modified_date == last_modified_date:
                                print(f"Skipping {blob_name}: Last modified date matches the saved date.")
                                continue

                        # If saved_last_modified is None, process the file
                        print(f"Processing file {file_number}/{total_files}: {blob_name}...")

                        # Download the blob as a stream
                        stream = download_blob_to_stream(container_client, blob_name)
                        if stream:
                            file_name = blob_name[len("resume/"):]  # Extract the file name

                            # Pass the last_modified date and the filename to the processing function
                            process_resumes_regex_from_stream(stream, file_name, last_modified_date)

                            # Update the saved file list incrementally
                            saved_file_list[blob_name] = last_modified_date.isoformat()
                            save_file_list(saved_file_list_path, saved_file_list)  # Save after each processed file
                            print(f"Processed and added {blob_name} to the saved file list.")
                        else:
                            print(f"Skipped {blob_name}: Unable to read blob into stream.")
                    except Exception as e:
                        print(f"Error processing {blob_name}: {e}")

                print(f"Finished processing batch {i // batch_size + 1}.\n")

        print("--- Finished Processing All Batches ---\n")

# with open('upload_chromadb.txt', 'w', encoding='utf-8') as f:
#     sys.stdout = f
if __name__ == "__main__":
        # Set the folder containing resumes
        resumes_folder = test_data_folder

        # Initialize the ResumeProcessor
        processor = ResumeProcessor(test_data_folder)

        # Flags to enable or disable specific processing methods
        use_AI = run_process_with_AI
        use_regex = run_process_with_regex

        # Call the processing functions based on the flags
        processor.process_with_AI(enabled=use_AI)
        processor.process_with_regex(batch_amount, enabled=use_regex)
        print_collection_summary(collection)
# sys.stdout = sys.__stdout__