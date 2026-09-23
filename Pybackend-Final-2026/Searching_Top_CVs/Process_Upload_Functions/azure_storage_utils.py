"""
/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment(Python)
 *                          Description: Handles the different operations conducted with the Azure Bolb storage system(list the file contents and downloading the binary data 
 *                          of the files into the stream).
 *                          Created Date: March 28, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 31, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
"""
from azure.storage.blob import BlobServiceClient
from io import BytesIO

def get_blob_container_client(connection_string, container_name):
    """
    Initialize and return the container client for the specified container.
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        print(f"Initialized container client for container: {container_name}")
        return container_client
    except Exception as e:
        print(f"Error initializing container client: {e}")
        return None
    
def list_blobs_in_container(container_client, prefix="resume/"):
    """
    List all blobs in the specified container with the given prefix.
    """
    try:
        blob_list = container_client.list_blobs(name_starts_with=prefix)
        
        # blobs = [blob.name for blob in blob_list]
        
        blobs = []
        print(f"Blobs in Azure Blob Storage under '{prefix}':")
        
        for blob in blob_list:
            blob_info = {
                "name": blob.name,
                "last_modified": blob.last_modified  # Get the last modified date
            }
            blobs.append(blob_info)
            print(f"- {blob.name}, Last Modified: {blob.last_modified}")
        
        # for blob in blobs:
        #     print(f"- {blob}")
        
        return blobs
    except Exception as e:
        print(f"Error listing blobs in Azure Blob Storage: {e}")
        return []

# Function that downloads the files from the blob storage into a local folder(this is kept here provided the application needs to fallback on this)

# def download_blob_content(container_client, blob_name):
#     """
#     Download the content of a blob from Azure Blob Storage.
#     :param container_client: The container client.
#     :param blob_name: The name of the blob to download.
#     """
#     try:
#         print(f"Attempting to download blob: {blob_name}")
#         blob_client = container_client.get_blob_client(blob_name)
#         print(f"Blob client created for: {blob_name}")

#         blob_data = blob_client.download_blob().readall()
#         print(f"Successfully downloaded content of {blob_name}.")
#         return blob_data
#     except Exception as e:
#         print(f"Error downloading blob {blob_name} from Azure Blob Storage: {e}")
#         return None
    
def download_blob_to_stream(container_client, blob_name):
    """
    Downloads the files from the storage and inserts their binary data into the stream
    """
    try:
        print(f"Downloading blob into stream: {blob_name}")
        blob_client = container_client.get_blob_client(blob_name)
        stream = BytesIO()
        blob_client.download_blob().readinto(stream)
        stream.seek(0)
        return stream
    except Exception as e:
        print(f"Error streaming blob {blob_name}: {e}")
        return None
