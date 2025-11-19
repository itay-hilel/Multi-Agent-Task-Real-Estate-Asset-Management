"""
File Upload Handler for Real Estate Agent
Handles uploading documents to Google GenAI File API and updating configuration.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from google import genai
from io import BytesIO


def get_config_path() -> str:
    """Get the path to the file_search_config.json file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'file_search_config.json')


def get_current_files() -> List[Dict[str, Any]]:
    """
    Read current uploaded files from config.
    
    Returns:
        List of file info dictionaries
    """
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        return []
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('uploaded_files', [])
    except Exception as e:
        print(f"Error reading config: {e}")
        return []


def upload_file_to_genai(file_obj, filename: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Upload a single file to Google GenAI File API.
    
    Args:
        file_obj: File object or BytesIO object
        filename: Original filename
        api_key: Google API key
    
    Returns:
        Dictionary with file info (name, uri, display_name, mime_type) or None on failure
    """
    client = genai.Client(api_key=api_key)
    
    try:
        # Determine mime type based on file extension
        upload_config = None
        if filename.endswith('.md'):
            upload_config = {'mime_type': 'text/markdown'}
        elif filename.endswith('.txt'):
            upload_config = {'mime_type': 'text/plain'}
        elif filename.endswith('.pdf'):
            upload_config = {'mime_type': 'application/pdf'}
        elif filename.endswith('.docx'):
            upload_config = {'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        elif filename.endswith('.pages'):
            upload_config = {'mime_type': 'application/vnd.apple.pages'}
        
        # Save to temporary file (Google GenAI expects file path)
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, filename)
        
        # Write file content to temp location
        with open(temp_path, 'wb') as f:
            f.write(file_obj.read())
        
        try:
            # Upload file
            file_obj_result = client.files.upload(file=temp_path, config=upload_config)
            
            return {
                'name': file_obj_result.name,
                'uri': file_obj_result.uri,
                'display_name': filename,
                'mime_type': file_obj_result.mime_type
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"Upload error for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_file_search_config(new_files: List[Dict[str, Any]]) -> bool:
    """
    Update file_search_config.json with new uploaded files.
    
    Args:
        new_files: List of new file info dictionaries
    
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()
    
    try:
        # Read existing config
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Get existing files
        uploaded_files = existing_config.get('uploaded_files', [])
        
        # Add new files (avoid duplicates by URI)
        existing_uris = {f['uri'] for f in uploaded_files}
        for new_file in new_files:
            if new_file['uri'] not in existing_uris:
                uploaded_files.append(new_file)
        
        # Update config
        config = {
            'created_at': existing_config.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S')),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'uploaded_files': uploaded_files,
            # Keep backward compatibility - use the last file
            'file_uri': uploaded_files[-1]['uri'] if uploaded_files else None,
            'file_name': uploaded_files[-1]['display_name'] if uploaded_files else None
        }
        
        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Config update error: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_text_as_document(text_content: str, document_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Upload text content as a document to Google GenAI File API.
    
    Args:
        text_content: The text content to upload
        document_name: Name to give the document
        api_key: Google API key
    
    Returns:
        Dictionary with file info or None on failure
    """
    if not text_content.strip():
        return None
    
    # Create a temporary text file
    filename = f"{document_name}.txt"
    file_obj = BytesIO(text_content.encode('utf-8'))
    
    return upload_file_to_genai(file_obj, filename, api_key)


def upload_files(uploaded_files, api_key: str) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Upload multiple files to Google GenAI and update config.
    
    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        api_key: Google API key
    
    Returns:
        Tuple of (successful_uploads, error_messages)
    """
    successful_uploads = []
    error_messages = []
    
    for uploaded_file in uploaded_files:
        # Validate file type
        allowed_extensions = ['.pdf', '.md', '.txt', '.docx', '.pages']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            error_messages.append(f"{uploaded_file.name}: Unsupported file type. Please use PDF, MD, TXT, DOCX, or Pages files.")
            continue
        
        # Upload to Google GenAI
        file_info = upload_file_to_genai(uploaded_file, uploaded_file.name, api_key)
        
        if file_info:
            successful_uploads.append(file_info)
        else:
            error_messages.append(f"{uploaded_file.name}: Upload failed. Please try again.")
    
    # Update config if we have successful uploads
    if successful_uploads:
        if not update_file_search_config(successful_uploads):
            error_messages.append("Failed to update configuration file.")
    
    return successful_uploads, error_messages
