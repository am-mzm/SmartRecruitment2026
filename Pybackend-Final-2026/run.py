import uvicorn
import subprocess
import os
from dotenv import load_dotenv
# from fastapi.middleware.wsgi import WSGIMiddleware
# from app.server import app  # Import the FastAPI app

load_dotenv()
# wsgi_app = WSGIMiddleware(app)

def upload_resumes():
    """
    Run the upload_to_chromadb.py script and forward its output to the console.
    """
    print("Starting the resume upload process...") 
    # Path to the script that uploads resumes to ChromaDB
    upload_script_path = "Searching_Top_CVs/upload_to_chromadb.py"
    
    # Execute the Python script with unbuffered output (-u flag)
    result = subprocess.run(['python', '-u', upload_script_path])
    
    # Check the return code to determine success or failure
    if result.returncode == 0:
        print("Resume upload completed successfully.")
    else:
        print("Error in uploading resumes. Check the script for issues.")

if __name__ == "__main__":
    
    # Run the upload process first
    # print("Uploading Resumes...")
    upload_resumes()
    
    # Start the FastAPI server
    uvicorn_host = os.getenv('UVICORN_HOST', '0.0.0.0')  # Default to 0.0.0.0 for Docker
    uvicorn_port = int(os.getenv('UVICORN_PORT', 8002))  # Default to 8002 for Docker
    uvicorn.run("app.server:app", host=uvicorn_host, port=uvicorn_port, reload=True)