from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import shutil
from typing import List, Optional
from loader import DocumentLoader
from search import EnhancedSemanticSearcher
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

print("=== DEBUGGING IMPORTS ===")

try:
    from search import EnhancedSemanticSearcher
    print("✅ Successfully imported EnhancedSemanticSearcher")
    
    try:
        semantic_searcher = EnhancedSemanticSearcher()
        print("✅ Successfully created semantic_searcher instance")
    except Exception as e:
        print(f"❌ Error creating semantic_searcher: {e}")
        semantic_searcher = None
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    try:
        from search import SemanticSearcher
        print("✅ Fallback: imported SemanticSearcher")
        semantic_searcher = SemanticSearcher()
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")
        semantic_searcher = None

print(f"semantic_searcher status: {semantic_searcher is not None}")
print("=== END DEBUG ===")

# Initialize FastAPI app
app = FastAPI(
    title="Semantic Search System with Pinecone",
    description="A semantic search system using Pinecone vector database, open-source embeddings and Google Gemini 2.5-flash",
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

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt']

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Semantic Search API with Pinecone",
        "version": "1.0.0",
        "description": "Upload documents and perform semantic search using Pinecone and Google Gemini 2.5-flash",
        "endpoints": {
            "upload": "/upload - Upload documents for indexing",
            "search": "/search - Search through uploaded documents",
            "documents": "/documents - List all indexed documents",
            "documents/{filename}": "DELETE - Remove specific document",
            "health": "/health - Check system health",
            "stats": "/stats - Get index statistics",
            "reset": "DELETE /reset - Reset entire index"
        },
        "supported_formats": SUPPORTED_EXTENSIONS
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process documents for semantic search"""
    try:
        # Validate file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Check file size (limit to 50MB)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum allowed size is 50MB."
            )
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' already exists. Please rename the file or delete the existing one first."
            )
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from document
        try:
            extracted_text = document_loader.extract_text(file_path)
            if not extracted_text.strip():
                # Clean up uploaded file if no text extracted
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the document"
                )
        except Exception as e:
            # Clean up uploaded file if text extraction fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Error extracting text: {str(e)}"
            )
        
        # Add document to Pinecone index
        try:
            semantic_searcher.add_document(extracted_text, file.filename)
        except Exception as e:
            # Clean up uploaded file if indexing fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error indexing document: {str(e)}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded and processed successfully",
                "filename": file.filename,
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

@app.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    filename: Optional[str] = Query(None, description="Filter by specific filename"),
    max_results: Optional[int] = Query(10, description="Maximum number of results to return", ge=1, le=50)
):
    """Enhanced search through uploaded documents with rich content extraction"""
    try:
        if not q.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Validate filename exists if provided
        if filename:
            documents = semantic_searcher.list_documents()
            if filename not in documents:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document '{filename}' not found in index"
                )
        
        # Perform enhanced semantic search
        results = semantic_searcher.search_documents(q, filename_filter=filename, max_results=max_results)
        
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

@app.get("/documents")
async def list_documents():
    """Get list of all indexed documents"""
    try:
        documents = semantic_searcher.list_documents()
        
        # Get uploaded files info
        uploaded_files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    uploaded_files.append({
                        "filename": filename,
                        "size_bytes": os.path.getsize(file_path),
                        "indexed": filename in documents
                    })
        
        return JSONResponse(
            status_code=200,
            content={
                "indexed_documents": documents,
                "uploaded_files": uploaded_files,
                "total_indexed": len(documents),
                "total_uploaded": len(uploaded_files)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document from the index"""
    try:
        # Check if document exists in index
        documents = semantic_searcher.list_documents()
        if filename not in documents:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{filename}' not found in index"
            )
        
        # Delete from Pinecone index
        semantic_searcher.delete_document(filename)
        
        # Delete uploaded file if it exists
        file_path = os.path.join(UPLOAD_DIR, filename)
        file_deleted = False
        if os.path.exists(file_path):
            os.remove(file_path)
            file_deleted = True
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Document '{filename}' deleted successfully",
                "filename": filename,
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
        
        # Check upload directory
        upload_dir_status = "exists" if os.path.exists(UPLOAD_DIR) else "missing"
        
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
                    "upload_directory": upload_dir_status
                },
                "timestamp": "2025-01-18T00:00:00Z"  # You might want to use datetime.now()
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-01-18T00:00:00Z"
            }
        )

@app.get("/stats")
async def get_stats():
    """Get statistics about the Pinecone index"""
    try:
        stats = semantic_searcher.get_index_stats()
        documents = semantic_searcher.list_documents()
        
        # Get uploaded files info with detailed stats
        uploaded_files = []
        total_upload_size = 0
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    total_upload_size += file_size
                    uploaded_files.append({
                        "filename": filename,
                        "size_bytes": file_size,
                        "extension": os.path.splitext(filename)[1].lower(),
                        "indexed": filename in documents
                    })
        
        # Group files by extension
        extensions_count = {}
        for file_info in uploaded_files:
            ext = file_info["extension"]
            extensions_count[ext] = extensions_count.get(ext, 0) + 1
        
        return JSONResponse(
            status_code=200,
            content={
                "pinecone_stats": stats,
                "document_stats": {
                    "indexed_documents": documents,
                    "total_indexed": len(documents),
                    "total_uploaded": len(uploaded_files),
                    "total_upload_size_bytes": total_upload_size,
                    "extensions_count": extensions_count
                },
                "uploaded_files": uploaded_files,
                "system_info": {
                    "supported_formats": SUPPORTED_EXTENSIONS,
                    "max_file_size_mb": 50,
                    "upload_directory": UPLOAD_DIR
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

@app.delete("/reset")
async def reset_index():
    """Reset the Pinecone index and remove all uploaded files"""
    try:
        # Get current stats before reset
        documents_before = semantic_searcher.list_documents()
        files_before = []
        if os.path.exists(UPLOAD_DIR):
            files_before = [f for f in os.listdir(UPLOAD_DIR) 
                          if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
        
        # Reset Pinecone index
        semantic_searcher.reset_index()
        
        # Remove uploaded files
        files_removed = 0
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_removed += 1
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Pinecone index and uploaded files have been reset successfully",
                "reset_stats": {
                    "documents_removed": len(documents_before),
                    "files_removed": files_removed,
                    "documents_before": documents_before,
                    "files_before": files_before
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting index: {str(e)}"
        )

@app.get("/docs-interactive")
async def get_interactive_docs():
    """Redirect to interactive API documentation"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Interactive API documentation available",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    )

# Additional utility endpoints

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return JSONResponse(
        status_code=200,
        content={
            "supported_extensions": SUPPORTED_EXTENSIONS,
            "format_details": {
                ".pdf": "Portable Document Format - extracted using PyMuPDF",
                ".docx": "Microsoft Word Document - extracted using python-docx",
                ".pptx": "Microsoft PowerPoint Presentation - extracted using python-pptx",
                ".txt": "Plain Text File - read directly with UTF-8 encoding"
            },
            "max_file_size_mb": 50
        }
    )

@app.get("/search-suggestions")
async def get_search_suggestions():
    """Get example search queries and tips"""
    return JSONResponse(
        status_code=200,
        content={
            "search_tips": [
                "Use specific keywords related to your documents",
                "Ask questions in natural language",
                "Use the filename parameter to search within specific documents",
                "Try different phrasings if you don't get good results"
            ],
            "example_queries": [
                "What is machine learning?",
                "How does renewable energy work?",
                "Explain the main concepts",
                "What are the benefits of this approach?",
                "Summarize the key findings"
            ],
            "advanced_features": {
                "filename_filtering": "Add ?filename=document.pdf to search only in that document",
                "result_limiting": "Add ?max_results=10 to get more results (max 20)",
                "combined_search": "Use both filename and max_results parameters together"
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting Semantic Search API with Pinecone")
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        reload=debug,
        log_level="info"
    )