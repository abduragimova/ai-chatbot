import PyPDF2
import re
from typing import List, Tuple


class PDFProcessor:
    """
    Handles PDF text extraction and processing.
    """
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Initialize PDF processor with chunking parameters.
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text += page_text + "\n\n"
            
            # Clean up text
            text = self.clean_text(text)
            
            return text
            
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and special characters.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\$\%\@\#\&\*\+\=\/\\]', '', text)
        
        # Remove multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better context retrieval.
        
        Args:
            text: Full document text
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence
            if end < text_length:
                # Look for sentence boundaries (., !, ?) near the end
                for i in range(end, max(start + self.chunk_size - 200, start), -1):
                    if i < text_length and text[i] in '.!?' and i + 1 < text_length and text[i + 1] == ' ':
                        end = i + 1
                        break
            
            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def find_relevant_chunks(self, chunks: List[str], query: str, top_k: int = 3) -> List[str]:
        """
        Find most relevant chunks for a given query using simple keyword matching.
        In production, use embeddings and vector similarity.
        
        Args:
            chunks: List of text chunks
            query: User query
            top_k: Number of top chunks to return
            
        Returns:
            List of most relevant chunks
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_chunks: List[Tuple[str, float]] = []
        
        for chunk in chunks:
            chunk_lower = chunk.lower()
            chunk_words = set(chunk_lower.split())
            
            # Calculate overlap score
            overlap = len(query_words.intersection(chunk_words))
            
            # Bonus for exact phrase match
            if query_lower in chunk_lower:
                overlap += 5
            
            # Bonus for key terms
            key_terms = ['budget', 'deadline', 'stakeholder', 'next steps', 'date', 'cost', 'timeline']
            for term in key_terms:
                if term in query_lower and term in chunk_lower:
                    overlap += 2
            
            scored_chunks.append((chunk, overlap))
        
        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [chunk for chunk, score in scored_chunks[:top_k] if score > 0]
    
    def extract_metadata(self, pdf_path: str) -> dict:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.title if pdf_reader.metadata else None,
                    'author': pdf_reader.metadata.author if pdf_reader.metadata else None,
                }
                
                return metadata
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
            return {'num_pages': 0}