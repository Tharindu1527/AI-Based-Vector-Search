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
    """Handle text chunking, embedding, and vector storage using Pinecone with spaces support"""
    
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
    
    def chunk_text(self, text: str, filename: str, space_id: str = "default") -> List[Dict[str, Any]]:
        """Split text into chunks with metadata including space information"""
        chunks = self.text_splitter.split_text(text)
        
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                'id': str(uuid.uuid4()),
                'text': chunk,
                'filename': filename,
                'space_id': space_id,
                'chunk_id': i,
                'total_chunks': len(chunks)
            })
        
        return chunk_metadata
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        print(f"Generating embeddings for {len(texts)} text chunks...")
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def add_documents_to_space(self, text: str, filename: str, space_id: str):
        """Add document chunks to a specific space in the Pinecone index"""
        try:
            print(f"Processing document: {filename} for space: {space_id}")
            
            # Chunk the text with space information
            chunks_metadata = self.chunk_text(text, filename, space_id)
            
            if not chunks_metadata:
                print("No chunks generated from the document")
                return
            
            print(f"Generated {len(chunks_metadata)} chunks for space {space_id}")
            
            # Extract text for embedding
            chunk_texts = [chunk['text'] for chunk in chunks_metadata]
            
            # Generate embeddings
            embeddings = self.embed_texts(chunk_texts)
            
            # Prepare vectors for Pinecone with space metadata
            vectors_to_upsert = []
            for i, (chunk_meta, embedding) in enumerate(zip(chunks_metadata, embeddings)):
                vector = {
                    'id': chunk_meta['id'],
                    'values': embedding.tolist(),
                    'metadata': {
                        'text': chunk_meta['text'],
                        'filename': chunk_meta['filename'],
                        'space_id': chunk_meta['space_id'],
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
                print(f"Uploading batch {batch_num}/{total_batches} to space {space_id}")
                
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            print(f"Successfully added {len(vectors_to_upsert)} chunks from {filename} to space {space_id}")
            
        except Exception as e:
            raise Exception(f"Error adding documents to space {space_id}: {str(e)}")
    
    def add_documents(self, text: str, filename: str):
        """Legacy method - adds document to default space"""
        self.add_documents_to_space(text, filename, "default")
    
    def search(self, query: str, k: int = 5, filter_dict: Dict = None) -> List[Dict[str, Any]]:
        """Search for similar chunks in Pinecone with optional filtering"""
        try:
            print(f"Searching for: '{query}' with filter: {filter_dict}")
            
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
                    'space_id': match['metadata'].get('space_id', 'default'),
                    'chunk_id': match['metadata']['chunk_id'],
                    'total_chunks': match['metadata']['total_chunks']
                }
                results.append(result)
            
            print(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            raise Exception(f"Error searching in Pinecone: {str(e)}")
    
    def delete_by_filename_and_space(self, filename: str, space_id: str):
        """Delete all vectors associated with a specific filename in a specific space"""
        try:
            print(f"Deleting vectors for filename: {filename} in space: {space_id}")
            
            # Query to get all vectors for this filename and space
            filter_dict = {
                "filename": {"$eq": filename},
                "space_id": {"$eq": space_id}
            }
            
            # Get all matching IDs in batches
            ids_to_delete = []
            
            # Query in batches to handle large numbers of vectors
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,  # Dummy vector
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                batch_ids = [match['id'] for match in query_response['matches']]
                if not batch_ids:
                    fetch_more = False
                else:
                    ids_to_delete.extend(batch_ids)
                    
                    # If we got fewer than batch_size, we've got all of them
                    if len(batch_ids) < batch_size:
                        fetch_more = False
            
            # Delete in batches
            if ids_to_delete:
                delete_batch_size = 1000
                for i in range(0, len(ids_to_delete), delete_batch_size):
                    batch = ids_to_delete[i:i + delete_batch_size]
                    self.index.delete(ids=batch)
                    print(f"Deleted batch {i//delete_batch_size + 1} of {(len(ids_to_delete) + delete_batch_size - 1)//delete_batch_size}")
                
                print(f"Deleted {len(ids_to_delete)} vectors for file: {filename} in space: {space_id}")
            else:
                print(f"No vectors found for filename: {filename} in space: {space_id}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors for {filename} in space {space_id}: {str(e)}")
    
    def delete_by_filename(self, filename: str):
        """Delete all vectors associated with a specific filename across all spaces"""
        try:
            print(f"Deleting vectors for filename: {filename} across all spaces")
            
            # Query to get all vectors for this filename
            filter_dict = {"filename": {"$eq": filename}}
            
            # Get all matching IDs in batches
            ids_to_delete = []
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,  # Dummy vector
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                batch_ids = [match['id'] for match in query_response['matches']]
                if not batch_ids:
                    fetch_more = False
                else:
                    ids_to_delete.extend(batch_ids)
                    
                    if len(batch_ids) < batch_size:
                        fetch_more = False
            
            # Delete in batches
            if ids_to_delete:
                delete_batch_size = 1000
                for i in range(0, len(ids_to_delete), delete_batch_size):
                    batch = ids_to_delete[i:i + delete_batch_size]
                    self.index.delete(ids=batch)
                    print(f"Deleted batch {i//delete_batch_size + 1} of {(len(ids_to_delete) + delete_batch_size - 1)//delete_batch_size}")
                
                print(f"Deleted {len(ids_to_delete)} vectors for file: {filename}")
            else:
                print(f"No vectors found for filename: {filename}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors for {filename}: {str(e)}")
    
    def delete_by_space(self, space_id: str):
        """Delete all vectors associated with a specific space"""
        try:
            print(f"Deleting all vectors for space: {space_id}")
            
            # Query to get all vectors for this space
            filter_dict = {"space_id": {"$eq": space_id}}
            
            # Get all matching IDs in batches
            ids_to_delete = []
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,  # Dummy vector
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                batch_ids = [match['id'] for match in query_response['matches']]
                if not batch_ids:
                    fetch_more = False
                else:
                    ids_to_delete.extend(batch_ids)
                    
                    if len(batch_ids) < batch_size:
                        fetch_more = False
            
            # Delete in batches
            if ids_to_delete:
                delete_batch_size = 1000
                for i in range(0, len(ids_to_delete), delete_batch_size):
                    batch = ids_to_delete[i:i + delete_batch_size]
                    self.index.delete(ids=batch)
                    print(f"Deleted batch {i//delete_batch_size + 1} of {(len(ids_to_delete) + delete_batch_size - 1)//delete_batch_size}")
                
                print(f"Deleted {len(ids_to_delete)} vectors for space: {space_id}")
            else:
                print(f"No vectors found for space: {space_id}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors for space {space_id}: {str(e)}")
    
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
        """Get list of unique filenames across all spaces"""
        try:
            # Query with a dummy vector to get metadata
            all_filenames = set()
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    # Extract unique filenames from this batch
                    for match in query_response['matches']:
                        if 'filename' in match['metadata']:
                            all_filenames.add(match['metadata']['filename'])
                    
                    # If we got fewer than batch_size, we've got all of them
                    if len(query_response['matches']) < batch_size:
                        fetch_more = False
            
            return list(all_filenames)
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def list_files_by_space(self, space_id: str) -> List[str]:
        """Get list of unique filenames in a specific space"""
        try:
            # Query with a dummy vector to get metadata for specific space
            filter_dict = {"space_id": {"$eq": space_id}}
            
            all_filenames = set()
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    # Extract unique filenames from this batch
                    for match in query_response['matches']:
                        if 'filename' in match['metadata']:
                            all_filenames.add(match['metadata']['filename'])
                    
                    # If we got fewer than batch_size, we've got all of them
                    if len(query_response['matches']) < batch_size:
                        fetch_more = False
            
            return list(all_filenames)
            
        except Exception as e:
            print(f"Error listing files for space {space_id}: {str(e)}")
            return []
    
    def list_spaces(self) -> List[str]:
        """Get list of unique space IDs"""
        try:
            # Query with a dummy vector to get metadata
            all_space_ids = set()
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    # Extract unique space IDs from this batch
                    for match in query_response['matches']:
                        if 'space_id' in match['metadata']:
                            all_space_ids.add(match['metadata']['space_id'])
                    
                    # If we got fewer than batch_size, we've got all of them
                    if len(query_response['matches']) < batch_size:
                        fetch_more = False
            
            return list(all_space_ids)
            
        except Exception as e:
            print(f"Error listing spaces: {str(e)}")
            return []
    
    def get_space_stats(self, space_id: str) -> Dict[str, Any]:
        """Get statistics for a specific space"""
        try:
            # Query to get all vectors for this space
            filter_dict = {"space_id": {"$eq": space_id}}
            
            total_chunks = 0
            filenames = set()
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    # Count chunks and collect filenames from this batch
                    batch_matches = query_response['matches']
                    total_chunks += len(batch_matches)
                    
                    for match in batch_matches:
                        if 'filename' in match['metadata']:
                            filenames.add(match['metadata']['filename'])
                    
                    # If we got fewer than batch_size, we've got all of them
                    if len(batch_matches) < batch_size:
                        fetch_more = False
            
            return {
                'space_id': space_id,
                'total_chunks': total_chunks,
                'total_documents': len(filenames),
                'documents': list(filenames)
            }
            
        except Exception as e:
            return {
                'space_id': space_id,
                'error': f"Error getting stats for space {space_id}: {str(e)}",
                'total_chunks': 0,
                'total_documents': 0,
                'documents': []
            }
    
    def get_all_spaces_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all spaces"""
        try:
            spaces = self.list_spaces()
            spaces_stats = {}
            
            for space_id in spaces:
                spaces_stats[space_id] = self.get_space_stats(space_id)
            
            # Calculate overall statistics
            total_chunks = sum(stats['total_chunks'] for stats in spaces_stats.values())
            total_documents = sum(stats['total_documents'] for stats in spaces_stats.values())
            
            return {
                'total_spaces': len(spaces),
                'total_chunks': total_chunks,
                'total_documents': total_documents,
                'spaces': spaces_stats,
                'embedding_model': self.embedding_model_name,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
            
        except Exception as e:
            return {
                'error': f"Error getting all spaces stats: {str(e)}",
                'total_spaces': 0,
                'total_chunks': 0,
                'total_documents': 0,
                'spaces': {}
            }
    
    def migrate_documents_to_space(self, filename: str, from_space: str, to_space: str):
        """Migrate a document from one space to another"""
        try:
            print(f"Migrating document {filename} from space {from_space} to {to_space}")
            
            # Get all vectors for this document in the source space
            filter_dict = {
                "filename": {"$eq": filename},
                "space_id": {"$eq": from_space}
            }
            
            vectors_to_migrate = []
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    vectors_to_migrate.extend(query_response['matches'])
                    
                    if len(query_response['matches']) < batch_size:
                        fetch_more = False
            
            if not vectors_to_migrate:
                print(f"No vectors found for {filename} in space {from_space}")
                return False
            
            # Update space_id in metadata and re-upsert
            updated_vectors = []
            for vector in vectors_to_migrate:
                updated_vector = {
                    'id': vector['id'],
                    'values': vector['values'],
                    'metadata': {
                        **vector['metadata'],
                        'space_id': to_space
                    }
                }
                updated_vectors.append(updated_vector)
            
            # Upsert updated vectors in batches
            upsert_batch_size = 100
            for i in range(0, len(updated_vectors), upsert_batch_size):
                batch = updated_vectors[i:i + upsert_batch_size]
                self.index.upsert(vectors=batch)
                print(f"Migrated batch {i//upsert_batch_size + 1} of {(len(updated_vectors) + upsert_batch_size - 1)//upsert_batch_size}")
            
            print(f"Successfully migrated {len(updated_vectors)} vectors for {filename} from {from_space} to {to_space}")
            return True
            
        except Exception as e:
            raise Exception(f"Error migrating document {filename} from {from_space} to {to_space}: {str(e)}")
    
    def check_document_exists(self, filename: str, space_id: str = None) -> bool:
        """Check if a document exists in the index (optionally in a specific space)"""
        try:
            filter_dict = {"filename": {"$eq": filename}}
            if space_id:
                filter_dict["space_id"] = {"$eq": space_id}
            
            query_response = self.index.query(
                vector=[0] * self.embedding_dim,
                top_k=1,
                include_metadata=True,
                filter=filter_dict
            )
            
            return len(query_response['matches']) > 0
            
        except Exception as e:
            print(f"Error checking document existence: {str(e)}")
            return False
    
    def get_document_chunks_count(self, filename: str, space_id: str = None) -> int:
        """Get the number of chunks for a specific document"""
        try:
            filter_dict = {"filename": {"$eq": filename}}
            if space_id:
                filter_dict["space_id"] = {"$eq": space_id}
            
            total_chunks = 0
            batch_size = 1000
            fetch_more = True
            
            while fetch_more:
                query_response = self.index.query(
                    vector=[0] * self.embedding_dim,
                    top_k=batch_size,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                if not query_response['matches']:
                    fetch_more = False
                else:
                    total_chunks += len(query_response['matches'])
                    
                    if len(query_response['matches']) < batch_size:
                        fetch_more = False
            
            return total_chunks
            
        except Exception as e:
            print(f"Error getting document chunks count: {str(e)}")
            return 0