import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Import with the correct class name from your indexer.py
try:
    from indexer import PineconeVectorIndexer
except ImportError:
    print("Warning: Could not import PineconeVectorIndexer, make sure indexer.py exists")

load_dotenv('.env', override=True)

class EnhancedSemanticSearcher:
    """Enhanced semantic search with multi-document support and rich content extraction"""
    
    def __init__(self):
        # Initialize Google Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            self.model = None
        
        # Initialize Pinecone vector indexer
        try:
            self.indexer = PineconeVectorIndexer()
        except Exception as e:
            print(f"Error initializing Pinecone indexer: {e}")
            self.indexer = None
            
        self.max_results = int(os.getenv('MAX_RESULTS', 10))
    
    def search_documents(self, query: str, filename_filter: str = None, max_results: int = None) -> Dict[str, Any]:
        """Enhanced search with multi-document support and rich content extraction"""
        try:
            if not self.indexer:
                return {
                    'answer': "Search system not properly initialized. Please check your configuration.",
                    'sources': [],
                    'query': query,
                    'filename_filter': filename_filter,
                    'document_summary': {},
                    'cross_document_insights': []
                }
                
            search_limit = max_results or self.max_results
            
            # Prepare filter for specific filename if provided
            filter_dict = None
            if filename_filter:
                filter_dict = {"filename": {"$eq": filename_filter}}
            
            # Get similar chunks from Pinecone with higher limit for better coverage
            search_results = self.indexer.search(query, k=search_limit * 2, filter_dict=filter_dict)
            
            if not search_results:
                return {
                    'answer': "I couldn't find any relevant information in the uploaded documents for your query.",
                    'sources': [],
                    'query': query,
                    'filename_filter': filename_filter,
                    'document_summary': {},
                    'cross_document_insights': [],
                    'total_results': 0,
                    'documents_searched': 0,
                    'search_scope': 'single_document' if filename_filter else 'all_documents'
                }
            
            # Group results by document for better organization
            documents_data = self._group_results_by_document(search_results)
            
            # Extract comprehensive content and context
            enriched_sources = self._enrich_source_information(search_results[:search_limit])
            
            # Prepare context from search results with document separation
            context_sections = self._prepare_enhanced_context(documents_data, query)
            
            # Generate comprehensive answer using Gemini
            answer = self._generate_enhanced_answer(query, context_sections, documents_data)
            
            # Generate cross-document insights
            cross_insights = self._generate_cross_document_insights(documents_data, query)
            
            # Create document summary
            doc_summary = self._create_document_summary(documents_data)
            
            return {
                'answer': answer,
                'sources': enriched_sources,
                'query': query,
                'total_results': len(search_results),
                'documents_searched': len(documents_data),
                'filename_filter': filename_filter,
                'document_summary': doc_summary,
                'cross_document_insights': cross_insights,
                'search_scope': 'single_document' if filename_filter else 'all_documents'
            }
            
        except Exception as e:
            return {
                'answer': f"An error occurred while searching: {str(e)}",
                'sources': [],
                'query': query,
                'filename_filter': filename_filter,
                'document_summary': {},
                'cross_document_insights': [],
                'total_results': 0,
                'documents_searched': 0,
                'search_scope': 'single_document' if filename_filter else 'all_documents'
            }
    
    def _group_results_by_document(self, search_results: List[Dict]) -> Dict[str, Dict]:
        """Group search results by document for better analysis"""
        documents = {}
        
        for result in search_results:
            filename = result['filename']
            if filename not in documents:
                documents[filename] = {
                    'filename': filename,
                    'chunks': [],
                    'max_similarity': 0,
                    'total_chunks': result.get('total_chunks', 0)
                }
            
            documents[filename]['chunks'].append(result)
            documents[filename]['max_similarity'] = max(
                documents[filename]['max_similarity'], 
                result['similarity_score']
            )
        
        # Sort documents by relevance
        return dict(sorted(documents.items(), 
                          key=lambda x: x[1]['max_similarity'], 
                          reverse=True))
    
    def _enrich_source_information(self, search_results: List[Dict]) -> List[Dict]:
        """Enrich source information with additional context"""
        enriched_sources = []
        
        for result in search_results:
            # Calculate estimated page number (rough estimation)
            estimated_page = (result['chunk_id'] // 3) + 1  # Assuming ~3 chunks per page
            
            enriched_source = {
                'id': result['id'],
                'filename': result['filename'],
                'chunk_id': result['chunk_id'],
                'similarity_score': result['similarity_score'],
                'text_preview': result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
                'full_text': result['text'],
                'estimated_page': estimated_page,
                'total_chunks_in_document': result.get('total_chunks', 0),
                'relevance_category': self._categorize_relevance(result['similarity_score']),
                'content_length': len(result['text']),
                'keywords_found': self._extract_keywords_from_chunk(result['text'])
            }
            enriched_sources.append(enriched_source)
        
        return enriched_sources
    
    def _categorize_relevance(self, score: float) -> str:
        """Categorize relevance based on similarity score"""
        if score >= 0.8:
            return "highly_relevant"
        elif score >= 0.6:
            return "moderately_relevant"
        elif score >= 0.4:
            return "somewhat_relevant"
        else:
            return "low_relevance"
    
    def _extract_keywords_from_chunk(self, text: str) -> List[str]:
        """Extract key terms from text chunk"""
        words = text.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word.strip('.,!?;:"()[]') for word in words 
                   if len(word) > 3 and word.lower() not in stop_words]
        return list(set(keywords))[:10]
    
    def _prepare_enhanced_context(self, documents_data: Dict, query: str) -> str:
        """Prepare enhanced context with document organization"""
        context_sections = []
        
        for doc_name, doc_data in documents_data.items():
            doc_context = f"\n=== DOCUMENT: {doc_name} ===\n"
            doc_context += f"Relevance Score: {doc_data['max_similarity']:.3f}\n"
            doc_context += f"Total Chunks Found: {len(doc_data['chunks'])}\n\n"
            
            for i, chunk in enumerate(doc_data['chunks'][:5]):
                doc_context += f"Chunk {chunk['chunk_id'] + 1} (Similarity: {chunk['similarity_score']:.3f}):\n"
                doc_context += f"{chunk['text']}\n\n"
            
            context_sections.append(doc_context)
        
        return "\n".join(context_sections)
    
    def _generate_enhanced_answer(self, query: str, context: str, documents_data: Dict) -> str:
        """Generate comprehensive answer using enhanced context"""
        
        if not self.model:
            return "AI response generation is not available. Please check your Google API key configuration."
        
        doc_list = list(documents_data.keys())
        doc_count = len(doc_list)
        
        prompt = f"""
You are an expert document analyst providing comprehensive answers based on multiple documents.

SEARCH QUERY: {query}

DOCUMENTS ANALYZED ({doc_count} documents):
{', '.join(doc_list)}

CONTENT FROM DOCUMENTS:
{context}

INSTRUCTIONS:
1. Provide a comprehensive answer that synthesizes information from ALL relevant documents
2. When referencing information, specify which document it came from
3. If information appears in multiple documents, mention this for validation
4. Highlight any contradictions or different perspectives between documents
5. Structure your response with clear sections if the topic is complex
6. Include specific details, numbers, examples, or quotes when available
7. If the query asks for a comparison, compare findings across documents
8. Conclude with a summary of key insights from your multi-document analysis

FORMAT YOUR RESPONSE:
- Start with a direct answer to the query
- Provide detailed explanation with document references
- Include any cross-document patterns or insights
- End with a concise summary

Remember: Base your response ONLY on the provided document content. If information is limited, state this clearly.

COMPREHENSIVE ANSWER:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating comprehensive response: {str(e)}"
    
    def _generate_cross_document_insights(self, documents_data: Dict, query: str) -> List[Dict]:
        """Generate insights that span across multiple documents"""
        if len(documents_data) < 2:
            return []
        
        insights = []
        
        try:
            # Generate cross-document insights
            insights.append({
                "type": "multi_document_analysis",
                "insight": f"Analysis across {len(documents_data)} documents reveals interconnected information about: {query}",
                "documents": list(documents_data.keys())
            })
            
        except Exception as e:
            print(f"Error generating cross-document insights: {e}")
        
        return insights
    
    def _create_document_summary(self, documents_data: Dict) -> Dict:
        """Create summary statistics about the documents searched"""
        summary = {
            'total_documents': len(documents_data),
            'documents_list': [],
            'relevance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'total_chunks_analyzed': 0
        }
        
        for doc_name, doc_data in documents_data.items():
            doc_info = {
                'filename': doc_name,
                'chunks_found': len(doc_data['chunks']),
                'max_relevance': doc_data['max_similarity'],
                'total_chunks_in_doc': doc_data['total_chunks']
            }
            summary['documents_list'].append(doc_info)
            summary['total_chunks_analyzed'] += len(doc_data['chunks'])
            
            # Categorize relevance
            if doc_data['max_similarity'] >= 0.7:
                summary['relevance_distribution']['high'] += 1
            elif doc_data['max_similarity'] >= 0.5:
                summary['relevance_distribution']['medium'] += 1
            else:
                summary['relevance_distribution']['low'] += 1
        
        return summary
    
    # Keep existing methods for compatibility
    def add_document(self, text: str, filename: str):
        """Add a document to the search index"""
        if self.indexer:
            self.indexer.add_documents(text, filename)
    
    def get_index_stats(self):
        """Get statistics about the current search index"""
        if self.indexer:
            return self.indexer.get_stats()
        return {'error': 'Indexer not initialized', 'total_vectors': 0}
    
    def delete_document(self, filename: str):
        """Delete a specific document from the index"""
        if self.indexer:
            self.indexer.delete_by_filename(filename)
    
    def list_documents(self) -> List[str]:
        """Get list of documents in the index"""
        if self.indexer:
            return self.indexer.list_files()
        return []
    
    def reset_index(self):
        """Reset the entire Pinecone index"""
        if self.indexer:
            self.indexer.reset_index()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if all components are working properly"""
        try:
            # Test Gemini API
            if self.model:
                test_response = self.model.generate_content("Hello, this is a test.")
                gemini_status = "working" if test_response else "error"
            else:
                gemini_status = "error: not initialized"
        except Exception as e:
            gemini_status = f"error: {str(e)}"
        
        # Check Pinecone index
        index_stats = self.get_index_stats()
        
        # Test Pinecone connectivity
        try:
            if self.indexer and self.indexer.index:
                self.indexer.index.describe_index_stats()
                pinecone_status = "connected"
            else:
                pinecone_status = "error: not initialized"
        except Exception as e:
            pinecone_status = f"error: {str(e)}"
        
        return {
            'gemini_api_status': gemini_status,
            'pinecone_status': pinecone_status,
            'index_stats': index_stats,
            'embedding_model': self.indexer.embedding_model_name if self.indexer else 'N/A'
        }

# Keep the old class name for backward compatibility
SemanticSearcher = EnhancedSemanticSearcher