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
    """Enhanced semantic search with spaces support and multi-document analysis"""
    
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
    
    def add_document_to_space(self, text: str, filename: str, space_id: str):
        """Add a document to a specific space"""
        if self.indexer:
            # Add space_id as metadata to the document
            self.indexer.add_documents_to_space(text, filename, space_id)
    
    def search_documents_in_spaces(self, query: str, space_ids: List[str] = None, filename_filter: str = None, max_results: int = None) -> Dict[str, Any]:
        """Enhanced search with space filtering support"""
        try:
            if not self.indexer:
                return {
                    'answer': "Search system not properly initialized. Please check your configuration.",
                    'sources': [],
                    'query': query,
                    'space_ids': space_ids,
                    'filename_filter': filename_filter,
                    'document_summary': {},
                    'cross_document_insights': []
                }
                
            search_limit = max_results or self.max_results
            
            # Prepare filter for spaces and filename
            filter_dict = {}
            
            # Add space filter if specified
            if space_ids:
                if len(space_ids) == 1:
                    filter_dict["space_id"] = {"$eq": space_ids[0]}
                else:
                    filter_dict["space_id"] = {"$in": space_ids}
            
            # Add filename filter if specified
            if filename_filter:
                filter_dict["filename"] = {"$eq": filename_filter}
            
            # Get similar chunks from Pinecone with higher limit for better coverage
            search_results = self.indexer.search(query, k=search_limit * 2, filter_dict=filter_dict if filter_dict else None)
            
            if not search_results:
                search_scope = self._determine_search_scope(space_ids, filename_filter)
                return {
                    'answer': f"I couldn't find any relevant information in the {'selected spaces' if space_ids else 'documents'} for your query.",
                    'sources': [],
                    'query': query,
                    'space_ids': space_ids,
                    'filename_filter': filename_filter,
                    'document_summary': {},
                    'cross_document_insights': [],
                    'total_results': 0,
                    'documents_searched': 0,
                    'spaces_searched': len(space_ids) if space_ids else 0,
                    'search_scope': search_scope
                }
            
            # Group results by document and space for better organization
            documents_data, spaces_data = self._group_results_by_space_and_document(search_results)
            
            # Extract comprehensive content and context
            enriched_sources = self._enrich_source_information_with_spaces(search_results[:search_limit])
            
            # Prepare context from search results with space and document separation
            context_sections = self._prepare_enhanced_context_with_spaces(spaces_data, query)
            
            # Generate comprehensive answer using Gemini
            answer = self._generate_enhanced_answer_with_spaces(query, context_sections, spaces_data)
            
            # Generate cross-document and cross-space insights
            cross_insights = self._generate_cross_space_insights(spaces_data, query)
            
            # Create document and space summary
            doc_summary = self._create_space_document_summary(spaces_data, documents_data)
            
            search_scope = self._determine_search_scope(space_ids, filename_filter)
            
            return {
                'answer': answer,
                'sources': enriched_sources,
                'query': query,
                'total_results': len(search_results),
                'documents_searched': len(documents_data),
                'spaces_searched': len(spaces_data),
                'space_ids': space_ids,
                'filename_filter': filename_filter,
                'document_summary': doc_summary,
                'cross_document_insights': cross_insights,
                'search_scope': search_scope
            }
            
        except Exception as e:
            return {
                'answer': f"An error occurred while searching: {str(e)}",
                'sources': [],
                'query': query,
                'space_ids': space_ids,
                'filename_filter': filename_filter,
                'document_summary': {},
                'cross_document_insights': [],
                'total_results': 0,
                'documents_searched': 0,
                'spaces_searched': 0,
                'search_scope': 'error'
            }
    
    def _determine_search_scope(self, space_ids: List[str], filename_filter: str) -> str:
        """Determine the scope of the search for UI display"""
        if filename_filter:
            return 'single_document'
        elif space_ids and len(space_ids) == 1:
            return 'single_space'
        elif space_ids and len(space_ids) > 1:
            return 'multi_space'
        else:
            return 'all_spaces'
    
    def _group_results_by_space_and_document(self, search_results: List[Dict]) -> tuple:
        """Group search results by space and document for better analysis"""
        spaces_data = {}
        documents_data = {}
        
        for result in search_results:
            space_id = result.get('space_id', 'default')
            filename = result['filename']
            
            # Group by space
            if space_id not in spaces_data:
                spaces_data[space_id] = {
                    'space_id': space_id,
                    'documents': {},
                    'max_similarity': 0,
                    'total_chunks': 0
                }
            
            # Group by document within space
            if filename not in spaces_data[space_id]['documents']:
                spaces_data[space_id]['documents'][filename] = {
                    'filename': filename,
                    'chunks': [],
                    'max_similarity': 0,
                    'total_chunks': result.get('total_chunks', 0)
                }
            
            spaces_data[space_id]['documents'][filename]['chunks'].append(result)
            spaces_data[space_id]['documents'][filename]['max_similarity'] = max(
                spaces_data[space_id]['documents'][filename]['max_similarity'],
                result['similarity_score']
            )
            
            spaces_data[space_id]['max_similarity'] = max(
                spaces_data[space_id]['max_similarity'],
                result['similarity_score']
            )
            spaces_data[space_id]['total_chunks'] += 1
            
            # Also maintain document-level grouping for compatibility
            if filename not in documents_data:
                documents_data[filename] = {
                    'filename': filename,
                    'chunks': [],
                    'max_similarity': 0,
                    'total_chunks': result.get('total_chunks', 0),
                    'space_id': space_id
                }
            
            documents_data[filename]['chunks'].append(result)
            documents_data[filename]['max_similarity'] = max(
                documents_data[filename]['max_similarity'],
                result['similarity_score']
            )
        
        # Sort by relevance
        spaces_data = dict(sorted(spaces_data.items(), 
                                key=lambda x: x[1]['max_similarity'], 
                                reverse=True))
        documents_data = dict(sorted(documents_data.items(),
                                   key=lambda x: x[1]['max_similarity'],
                                   reverse=True))
        
        return documents_data, spaces_data
    
    def _enrich_source_information_with_spaces(self, search_results: List[Dict]) -> List[Dict]:
        """Enrich source information with space context"""
        enriched_sources = []
        
        for result in search_results:
            estimated_page = (result['chunk_id'] // 3) + 1
            space_id = result.get('space_id', 'default')
            
            enriched_source = {
                'id': result['id'],
                'filename': result['filename'],
                'space_id': space_id,
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
    
    def _prepare_enhanced_context_with_spaces(self, spaces_data: Dict, query: str) -> str:
        """Prepare enhanced context with space and document organization"""
        context_sections = []
        
        for space_id, space_data in spaces_data.items():
            space_context = f"\n=== SPACE: {space_id} ===\n"
            space_context += f"Max Relevance Score: {space_data['max_similarity']:.3f}\n"
            space_context += f"Total Chunks Found: {space_data['total_chunks']}\n"
            space_context += f"Documents in Space: {len(space_data['documents'])}\n\n"
            
            for doc_name, doc_data in space_data['documents'].items():
                space_context += f"--- DOCUMENT: {doc_name} ---\n"
                space_context += f"Document Relevance: {doc_data['max_similarity']:.3f}\n"
                space_context += f"Chunks from Document: {len(doc_data['chunks'])}\n\n"
                
                for i, chunk in enumerate(doc_data['chunks'][:3]):  # Limit chunks per document
                    space_context += f"Chunk {chunk['chunk_id'] + 1} (Similarity: {chunk['similarity_score']:.3f}):\n"
                    space_context += f"{chunk['text']}\n\n"
            
            context_sections.append(space_context)
        
        return "\n".join(context_sections)
    
    def _generate_enhanced_answer_with_spaces(self, query: str, context: str, spaces_data: Dict) -> str:
        """Generate comprehensive answer using enhanced context with space awareness"""
        
        if not self.model:
            return "AI response generation is not available. Please check your Google API key configuration."
        
        space_count = len(spaces_data)
        total_docs = sum(len(space_data['documents']) for space_data in spaces_data.values())
        space_names = list(spaces_data.keys())
        
        prompt = f"""
You are an expert document analyst providing comprehensive answers based on documents from multiple organized spaces.

SEARCH QUERY: {query}

ANALYSIS SCOPE:
- Spaces Analyzed: {space_count} spaces ({', '.join(space_names)})
- Total Documents: {total_docs} documents
- Cross-space analysis enabled

CONTENT FROM SPACES:
{context}

INSTRUCTIONS:
1. Provide a comprehensive answer that synthesizes information from ALL relevant spaces and documents
2. When referencing information, specify both the space and document it came from
3. If information appears across multiple spaces/documents, mention this for validation
4. Highlight any patterns, contradictions, or complementary information across spaces
5. Structure your response with clear sections if the topic is complex
6. Include specific details, numbers, examples, or quotes when available
7. If the query asks for comparisons, compare findings across spaces and documents
8. Conclude with a summary of key insights from your cross-space analysis

FORMAT YOUR RESPONSE:
- Start with a direct answer to the query
- Provide detailed explanation with space and document references
- Include any cross-space patterns or insights
- End with a concise summary

Remember: Base your response ONLY on the provided content from the spaces. If information is limited, state this clearly and specify which spaces were searched.

COMPREHENSIVE ANSWER:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating comprehensive response: {str(e)}"
    
    def _generate_cross_space_insights(self, spaces_data: Dict, query: str) -> List[Dict]:
        """Generate insights that span across multiple spaces"""
        insights = []
        
        if len(spaces_data) < 2:
            return insights
        
        try:
            # Analyze patterns across spaces
            insights.append({
                "type": "cross_space_analysis",
                "insight": f"Analysis across {len(spaces_data)} spaces reveals interconnected information about: {query}",
                "spaces": list(spaces_data.keys()),
                "total_documents": sum(len(space_data['documents']) for space_data in spaces_data.values())
            })
            
            # Find common themes across spaces
            all_keywords = []
            for space_data in spaces_data.values():
                for doc_data in space_data['documents'].values():
                    for chunk in doc_data['chunks']:
                        all_keywords.extend(self._extract_keywords_from_chunk(chunk['text']))
            
            if all_keywords:
                from collections import Counter
                common_keywords = [word for word, count in Counter(all_keywords).most_common(5)]
                insights.append({
                    "type": "common_themes",
                    "insight": f"Common themes across spaces: {', '.join(common_keywords)}",
                    "keywords": common_keywords
                })
            
        except Exception as e:
            print(f"Error generating cross-space insights: {e}")
        
        return insights
    
    def _create_space_document_summary(self, spaces_data: Dict, documents_data: Dict) -> Dict:
        """Create summary statistics about the spaces and documents searched"""
        summary = {
            'total_spaces': len(spaces_data),
            'total_documents': len(documents_data),
            'spaces_list': [],
            'documents_list': [],
            'relevance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'total_chunks_analyzed': 0
        }
        
        # Space-level summary
        for space_id, space_data in spaces_data.items():
            space_info = {
                'space_id': space_id,
                'documents_count': len(space_data['documents']),
                'chunks_found': space_data['total_chunks'],
                'max_relevance': space_data['max_similarity']
            }
            summary['spaces_list'].append(space_info)
            summary['total_chunks_analyzed'] += space_data['total_chunks']
            
            # Categorize space relevance
            if space_data['max_similarity'] >= 0.7:
                summary['relevance_distribution']['high'] += 1
            elif space_data['max_similarity'] >= 0.5:
                summary['relevance_distribution']['medium'] += 1
            else:
                summary['relevance_distribution']['low'] += 1
        
        # Document-level summary
        for doc_name, doc_data in documents_data.items():
            doc_info = {
                'filename': doc_name,
                'space_id': doc_data.get('space_id', 'unknown'),
                'chunks_found': len(doc_data['chunks']),
                'max_relevance': doc_data['max_similarity'],
                'total_chunks_in_doc': doc_data['total_chunks']
            }
            summary['documents_list'].append(doc_info)
        
        return summary
    
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
    
    # Legacy methods for backward compatibility
    def search_documents(self, query: str, filename_filter: str = None, max_results: int = None) -> Dict[str, Any]:
        """Legacy search method - redirects to space-aware search"""
        return self.search_documents_in_spaces(query, None, filename_filter, max_results)
    
    def add_document(self, text: str, filename: str):
        """Legacy method - adds document to default space"""
        self.add_document_to_space(text, filename, "default")
    
    def delete_document(self, filename: str):
        """Legacy method - deletes document from all spaces"""
        if self.indexer:
            self.indexer.delete_by_filename(filename)
    
    def delete_document_from_space(self, filename: str, space_id: str):
        """Delete a specific document from a specific space"""
        if self.indexer:
            self.indexer.delete_by_filename_and_space(filename, space_id)
    
    def list_documents(self) -> List[str]:
        """Get list of all documents across all spaces"""
        if self.indexer:
            return self.indexer.list_files()
        return []
    
    def list_documents_by_space(self, space_id: str) -> List[str]:
        """Get list of documents in a specific space"""
        if self.indexer:
            return self.indexer.list_files_by_space(space_id)
        return []
    
    def get_index_stats(self):
        """Get statistics about the current search index"""
        if self.indexer:
            return self.indexer.get_stats()
        return {'error': 'Indexer not initialized', 'total_vectors': 0}
    
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