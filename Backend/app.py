from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import List, Optional
from loader import DocumentLoader
from search import EnhancedSemanticSearcher
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Semantic Search System with Spaces",
    description="A semantic search system with spaces organization using Pinecone vector database and Google Gemini",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_loader = DocumentLoader()
semantic_searcher = EnhancedSemanticSearcher()

# Create necessary directories
UPLOAD_DIR = "uploads"
SPACES_DIR = "spaces"
SPACES_CONFIG_FILE = "spaces_config.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SPACES_DIR, exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt']

# Pydantic models
class SpaceCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#3B82F6"  # Default blue color

class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

# Helper functions for spaces management
def load_spaces_config():
    """Load spaces configuration from JSON file"""
    if os.path.exists(SPACES_CONFIG_FILE):
        try:
            with open(SPACES_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_spaces_config(spaces_config):
    """Save spaces configuration to JSON file"""
    with open(SPACES_CONFIG_FILE, 'w') as f:
        json.dump(spaces_config, f, indent=2)

def get_space_upload_dir(space_id: str):
    """Get the upload directory for a specific space"""
    space_dir = os.path.join(SPACES_DIR, space_id)
    os.makedirs(space_dir, exist_ok=True)
    return space_dir

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Semantic Search API with Spaces",
        "version": "1.0.0",
        "description": "Upload documents to spaces and perform semantic search using Pinecone and Google Gemini",
        "endpoints": {
            "spaces": "/spaces - Manage spaces",
            "upload": "/spaces/{space_id}/upload - Upload documents to a space",
            "search": "/search - Search through documents in selected spaces",
            "health": "/health - Check system health",
            "stats": "/stats - Get system statistics"
        },
        "supported_formats": SUPPORTED_EXTENSIONS
    }

# Spaces endpoints
@app.get("/spaces")
async def list_spaces():
    """Get list of all spaces with document counts"""
    try:
        spaces_config = load_spaces_config()
        spaces_with_stats = []
        
        for space_id, space_info in spaces_config.items():
            # Get document count for this space
            space_documents = semantic_searcher.list_documents_by_space(space_id)
            document_count = len(space_documents)
            
            # Get total file size
            space_dir = get_space_upload_dir(space_id)
            total_size = 0
            if os.path.exists(space_dir):
                for filename in os.listdir(space_dir):
                    file_path = os.path.join(space_dir, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
            
            space_with_stats = {
                **space_info,
                "id": space_id,
                "document_count": document_count,
                "total_size_bytes": total_size,
                "documents": space_documents
            }
            spaces_with_stats.append(space_with_stats)
        
        return JSONResponse(
            status_code=200,
            content={
                "spaces": spaces_with_stats,
                "total_spaces": len(spaces_with_stats)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing spaces: {str(e)}"
        )

@app.post("/spaces")
async def create_space(space: SpaceCreate):
    """Create a new space"""
    try:
        spaces_config = load_spaces_config()
        
        # Check if space name already exists
        for existing_space in spaces_config.values():
            if existing_space.get("name", "").lower() == space.name.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Space with name '{space.name}' already exists"
                )
        
        # Generate unique space ID
        space_id = str(uuid.uuid4())
        
        # Create space configuration
        space_config = {
            "name": space.name,
            "description": space.description,
            "color": space.color,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add to spaces config
        spaces_config[space_id] = space_config
        save_spaces_config(spaces_config)
        
        # Create space directory
        get_space_upload_dir(space_id)
        
        return JSONResponse(
            status_code=201,
            content={
                "message": f"Space '{space.name}' created successfully",
                "space_id": space_id,
                "space": {**space_config, "id": space_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating space: {str(e)}"
        )

@app.get("/spaces/{space_id}")
async def get_space(space_id: str):
    """Get details of a specific space"""
    try:
        spaces_config = load_spaces_config()
        
        if space_id not in spaces_config:
            raise HTTPException(
                status_code=404,
                detail=f"Space with ID '{space_id}' not found"
            )
        
        space_info = spaces_config[space_id]
        documents = semantic_searcher.list_documents_by_space(space_id)
        
        # Get file details
        space_dir = get_space_upload_dir(space_id)
        file_details = []
        total_size = 0
        
        if os.path.exists(space_dir):
            for filename in os.listdir(space_dir):
                file_path = os.path.join(space_dir, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_details.append({
                        "filename": filename,
                        "size_bytes": file_size,
                        "extension": os.path.splitext(filename)[1].lower(),
                        "indexed": filename in documents
                    })
        
        return JSONResponse(
            status_code=200,
            content={
                **space_info,
                "id": space_id,
                "document_count": len(documents),
                "total_size_bytes": total_size,
                "documents": documents,
                "file_details": file_details
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting space: {str(e)}"
        )

@app.put("/spaces/{space_id}")
async def update_space(space_id: str, space_update: SpaceUpdate):
    """Update space information"""
    try:
        spaces_config = load_spaces_config()
        
        if space_id not in spaces_config:
            raise HTTPException(
                status_code=404,
                detail=f"Space with ID '{space_id}' not found"
            )
        
        # Check if new name conflicts with existing spaces
        if space_update.name:
            for existing_id, existing_space in spaces_config.items():
                if (existing_id != space_id and 
                    existing_space.get("name", "").lower() == space_update.name.lower()):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Space with name '{space_update.name}' already exists"
                    )
        
        # Update space configuration
        space_config = spaces_config[space_id]
        if space_update.name is not None:
            space_config["name"] = space_update.name
        if space_update.description is not None:
            space_config["description"] = space_update.description
        if space_update.color is not None:
            space_config["color"] = space_update.color
        
        space_config["updated_at"] = datetime.now().isoformat()
        
        spaces_config[space_id] = space_config
        save_spaces_config(spaces_config)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Space updated successfully",
                "space": {**space_config, "id": space_id}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating space: {str(e)}"
        )

@app.delete("/spaces/{space_id}")
async def delete_space(space_id: str):
    """Delete a space and all its documents"""
    try:
        spaces_config = load_spaces_config()
        
        if space_id not in spaces_config:
            raise HTTPException(
                status_code=404,
                detail=f"Space with ID '{space_id}' not found"
            )
        
        space_name = spaces_config[space_id].get("name", "Unknown")
        
        # Delete all documents from the index for this space
        documents = semantic_searcher.list_documents_by_space(space_id)
        for doc in documents:
            semantic_searcher.delete_document_from_space(doc, space_id)
        
        # Delete space directory and files
        space_dir = get_space_upload_dir(space_id)
        if os.path.exists(space_dir):
            shutil.rmtree(space_dir)
        
        # Remove from spaces config
        del spaces_config[space_id]
        save_spaces_config(spaces_config)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Space '{space_name}' and all its documents deleted successfully",
                "space_id": space_id,
                "documents_deleted": len(documents)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting space: {str(e)}"
        )

# Document upload to space
@app.post("/spaces/{space_id}/upload")
async def upload_file_to_space(space_id: str, file: UploadFile = File(...)):
    """Upload and process documents for a specific space"""
    try:
        # Check if space exists
        spaces_config = load_spaces_config()
        if space_id not in spaces_config:
            raise HTTPException(
                status_code=404,
                detail=f"Space with ID '{space_id}' not found"
            )
        
        # Validate file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Check file size (limit to 50MB)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum allowed size is 50MB."
            )
        
        # Save uploaded file to space directory
        space_dir = get_space_upload_dir(space_id)
        file_path = os.path.join(space_dir, file.filename)
        
        # Check if file already exists in this space
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' already exists in this space. Please rename the file or delete the existing one first."
            )
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from document
        try:
            extracted_text = document_loader.extract_text(file_path)
            if not extracted_text.strip():
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the document"
                )
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Error extracting text: {str(e)}"
            )
        
        # Add document to Pinecone index with space information
        try:
            semantic_searcher.add_document_to_space(extracted_text, file.filename, space_id)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error indexing document: {str(e)}"
            )
        
        space_name = spaces_config[space_id].get("name", "Unknown")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"File uploaded to space '{space_name}' successfully",
                "filename": file.filename,
                "space_id": space_id,
                "space_name": space_name,
                "file_size_bytes": file_size,
                "extracted_text_length": len(extracted_text),
                "status": "indexed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Enhanced search with space selection
@app.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    space_ids: Optional[str] = Query(None, description="Comma-separated space IDs to search in"),
    filename: Optional[str] = Query(None, description="Filter by specific filename"),
    max_results: Optional[int] = Query(10, description="Maximum number of results to return", ge=1, le=50)
):
    """Enhanced search through documents in selected spaces"""
    try:
        if not q.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Parse space IDs
        selected_spaces = []
        if space_ids:
            selected_spaces = [s.strip() for s in space_ids.split(',') if s.strip()]
            
            # Validate that all spaces exist
            spaces_config = load_spaces_config()
            for space_id in selected_spaces:
                if space_id not in spaces_config:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Space '{space_id}' not found"
                    )
        
        # Validate filename exists if provided
        if filename:
            if selected_spaces:
                # Check if filename exists in any of the selected spaces
                filename_found = False
                for space_id in selected_spaces:
                    documents = semantic_searcher.list_documents_by_space(space_id)
                    if filename in documents:
                        filename_found = True
                        break
                if not filename_found:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Document '{filename}' not found in selected spaces"
                    )
            else:
                # Check if filename exists in any space
                all_documents = semantic_searcher.list_documents()
                if filename not in all_documents:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Document '{filename}' not found"
                    )
        
        # Perform enhanced semantic search with space filtering
        results = semantic_searcher.search_documents_in_spaces(
            query=q, 
            space_ids=selected_spaces, 
            filename_filter=filename, 
            max_results=max_results
        )
        
        return JSONResponse(
            status_code=200,
            content=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )

# Delete document from space
@app.delete("/spaces/{space_id}/documents/{filename}")
async def delete_document_from_space(space_id: str, filename: str):
    """Delete a specific document from a space"""
    try:
        # Check if space exists
        spaces_config = load_spaces_config()
        if space_id not in spaces_config:
            raise HTTPException(
                status_code=404,
                detail=f"Space with ID '{space_id}' not found"
            )
        
        # Check if document exists in space
        documents = semantic_searcher.list_documents_by_space(space_id)
        if filename not in documents:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{filename}' not found in this space"
            )
        
        # Delete from Pinecone index
        semantic_searcher.delete_document_from_space(filename, space_id)
        
        # Delete uploaded file if it exists
        space_dir = get_space_upload_dir(space_id)
        file_path = os.path.join(space_dir, filename)
        file_deleted = False
        if os.path.exists(file_path):
            os.remove(file_path)
            file_deleted = True
        
        space_name = spaces_config[space_id].get("name", "Unknown")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Document '{filename}' deleted from space '{space_name}' successfully",
                "filename": filename,
                "space_id": space_id,
                "space_name": space_name,
                "file_deleted": file_deleted,
                "index_deleted": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Check system health and component status"""
    try:
        health_status = semantic_searcher.health_check()
        
        # Check spaces directory
        spaces_dir_status = "exists" if os.path.exists(SPACES_DIR) else "missing"
        
        # Check spaces config
        spaces_config = load_spaces_config()
        spaces_count = len(spaces_config)
        
        # Overall health determination
        overall_health = "healthy"
        if "error" in health_status.get('gemini_api_status', ''):
            overall_health = "degraded"
        if "error" in health_status.get('pinecone_status', ''):
            overall_health = "unhealthy"
        
        return JSONResponse(
            status_code=200 if overall_health == "healthy" else 503,
            content={
                "status": overall_health,
                "components": {
                    **health_status,
                    "spaces_directory": spaces_dir_status,
                    "spaces_count": spaces_count
                },
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/stats")
async def get_stats():
    """Get statistics about the system including spaces"""
    try:
        stats = semantic_searcher.get_index_stats()
        spaces_config = load_spaces_config()
        
        # Calculate space statistics
        space_stats = []
        total_documents = 0
        total_upload_size = 0
        
        for space_id, space_info in spaces_config.items():
            documents = semantic_searcher.list_documents_by_space(space_id)
            space_dir = get_space_upload_dir(space_id)
            
            space_size = 0
            file_count = 0
            if os.path.exists(space_dir):
                for filename in os.listdir(space_dir):
                    file_path = os.path.join(space_dir, filename)
                    if os.path.isfile(file_path):
                        space_size += os.path.getsize(file_path)
                        file_count += 1
            
            space_stat = {
                "space_id": space_id,
                "name": space_info.get("name", "Unknown"),
                "document_count": len(documents),
                "file_count": file_count,
                "size_bytes": space_size
            }
            space_stats.append(space_stat)
            total_documents += len(documents)
            total_upload_size += space_size
        
        return JSONResponse(
            status_code=200,
            content={
                "pinecone_stats": stats,
                "spaces_stats": {
                    "total_spaces": len(spaces_config),
                    "total_documents": total_documents,
                    "total_upload_size_bytes": total_upload_size,
                    "spaces": space_stats
                },
                "system_info": {
                    "supported_formats": SUPPORTED_EXTENSIONS,
                    "max_file_size_mb": 50,
                    "spaces_directory": SPACES_DIR
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting Semantic Search API with Spaces")
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(app, host=host, port=port, reload=debug, log_level="info")