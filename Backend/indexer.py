import os
import uuid
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, PodSpec
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

class PineconeVectorIndexer:
    """Handle text chunking, embedding, and vector storage using Pinecone"""
    
    def __init__(self):
        # Load configuration
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 500))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 50))
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'semantic-search-index')
        
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        print(f"Embedding model loaded. Dimension: {self.embedding_dim}")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        
        # Initialize or connect to Pinecone index
        self.index = self._get_or_create_index()
    
    def _get_or_create_index(self):
        """Get existing index or create a new one"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            if self.index_name in existing_indexes:
                print(f"Connecting to existing index: {self.index_name}")
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                print(f"Creating new index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dim,
                    metric='cosine',
                    spec=PodSpec(
                        environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws'),
                        pod_type='p1.x1'
                    )
                )
                # Wait for index to be ready
                import time
                print("Waiting for index to be ready...")
                time.sleep(10)
                return self.pc.Index(self.index_name)
        except Exception as e:
            raise Exception(f"Error connecting to Pinecone: {str(e)}")
    
    def chunk_text(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        chunks = self.text_splitter.split_text(text)
        
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                'id': str(uuid.uuid4()),
                'text': chunk,
                'filename': filename,
                'chunk_id': i,
                'total_chunks': len(chunks)
            })
        
        return chunk_metadata
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        print(f"Generating embeddings for {len(texts)} text chunks...")
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def add_documents(self, text: str, filename: str):
        """Add document chunks to the Pinecone index"""
        try:
            print(f"Processing document: {filename}")
            
            # Chunk the text
            chunks_metadata = self.chunk_text(text, filename)
            
            if not chunks_metadata:
                print("No chunks generated from the document")
                return
            
            print(f"Generated {len(chunks_metadata)} chunks")
            
            # Extract text for embedding
            chunk_texts = [chunk['text'] for chunk in chunks_metadata]
            
            # Generate embeddings
            embeddings = self.embed_texts(chunk_texts)
            
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for i, (chunk_meta, embedding) in enumerate(zip(chunks_metadata, embeddings)):
                vector = {
                    'id': chunk_meta['id'],
                    'values': embedding.tolist(),
                    'metadata': {
                        'text': chunk_meta['text'],
                        'filename': chunk_meta['filename'],
                        'chunk_id': chunk_meta['chunk_id'],
                        'total_chunks': chunk_meta['total_chunks']
                    }
                }
                vectors_to_upsert.append(vector)
            
            # Upsert vectors to Pinecone in batches
            batch_size = 100
            total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch_num = (i // batch_size) + 1
                print(f"Uploading batch {batch_num}/{total_batches}")
                
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            print(f"Successfully added {len(vectors_to_upsert)} chunks from {filename}")
            
        except Exception as e:
            raise Exception(f"Error adding documents to Pinecone: {str(e)}")
    
    def search(self, query: str, k: int = 5, filter_dict: Dict = None) -> List[Dict[str, Any]]:
        """Search for similar chunks in Pinecone"""
        try:
            print(f"Searching for: '{query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Search in Pinecone
            search_response = self.index.query(
                vector=query_embedding[0].tolist(),
                top_k=k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            results = []
            for match in search_response['matches']:
                result = {
                    'id': match['id'],
                    'similarity_score': match['score'],
                    'text': match['metadata']['text'],
                    'filename': match['metadata']['filename'],
                    'chunk_id': match['metadata']['chunk_id'],
                    'total_chunks': match['metadata']['total_chunks']
                }
                results.append(result)
            
            print(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            raise Exception(f"Error searching in Pinecone: {str(e)}")
    
    def delete_by_filename(self, filename: str):
        """Delete all vectors associated with a specific filename"""
        try:
            print(f"Deleting vectors for filename: {filename}")
            
            # Query to get all vectors for this filename
            filter_dict = {"filename": {"$eq": filename}}
            
            # Get all matching IDs
            query_response = self.index.query(
                vector=[0] * self.embedding_dim,  # Dummy vector
                top_k=10000,  # Large number to get all matches
                include_metadata=True,
                filter=filter_dict
            )
            
            # Extract IDs and delete
            ids_to_delete = [match['id'] for match in query_response['matches']]
            
            if ids_to_delete:
                self.index.delete(ids=ids_to_delete)
                print(f"Deleted {len(ids_to_delete)} vectors for file: {filename}")
            else:
                print(f"No vectors found for filename: {filename}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors for {filename}: {str(e)}")
    
    def get_stats(self):
        """Get statistics about the current Pinecone index"""
        try:
            index_stats = self.index.describe_index_stats()
            
            return {
                'total_vectors': index_stats['total_vector_count'],
                'embedding_dimension': self.embedding_dim,
                'index_name': self.index_name,
                'namespaces': index_stats.get('namespaces', {}),
                'index_fullness': index_stats.get('index_fullness', 0)
            }
        except Exception as e:
            return {
                'error': f"Error getting Pinecone stats: {str(e)}",
                'total_vectors': 0,
                'embedding_dimension': self.embedding_dim,
                'index_name': self.index_name
            }
    
    def reset_index(self):
        """Delete all vectors from the index"""
        try:
            print("Resetting Pinecone index...")
            self.index.delete(delete_all=True)
            print("Successfully reset Pinecone index")
        except Exception as e:
            raise Exception(f"Error resetting Pinecone index: {str(e)}")
    
    def list_files(self) -> List[str]:
        """Get list of unique filenames in the index"""
        try:
            # Query with a dummy vector to get metadata
            query_response = self.index.query(
                vector=[0] * self.embedding_dim,
                top_k=10000,
                include_metadata=True
            )
            
            # Extract unique filenames
            filenames = set()
            for match in query_response['matches']:
                if 'filename' in match['metadata']:
                    filenames.add(match['metadata']['filename'])
            
            return list(filenames)
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []