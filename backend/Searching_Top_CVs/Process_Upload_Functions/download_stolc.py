import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv(r"C:\SmartRecruitment\HelpFile\.env")

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

container_name = "datalake"
blob_name = "resume/10202_1670034091Stolc_Resume_GDA.docx"

output_path = r"C:\SmartRecruitment\Stolc_Azure_Resume.docx"

blob_service_client = BlobServiceClient.from_connection_string(
    connection_string
)

blob_client = blob_service_client.get_blob_client(
    container=container_name,
    blob=blob_name
)

print(f"Downloading: {blob_name}")

with open(output_path, "wb") as f:
    f.write(blob_client.download_blob().readall())

print(f"Downloaded successfully:")
print(output_path)