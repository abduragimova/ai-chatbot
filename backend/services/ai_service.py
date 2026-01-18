import google.generativeai as genai
from typing import List
import time


class AIService:
    """
    Handles AI interactions using Google Gemini API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize AI service with Gemini model.
        
        Args:
            api_key: Google API key for Gemini
        """
        genai.configure(api_key=api_key)
        # Updated to use gemini-1.5-flash (gemini-pro is deprecated)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # System prompt for document Q&A
        self.system_prompt = """You are an AI assistant specialized in answering questions about documents.
Your role is to provide accurate, specific answers based ONLY on the information in the provided document.

CRITICAL GUIDELINES:
1. Answer questions ONLY using information from the document provided
2. If the answer is not in the document, clearly state: "I cannot find this information in the document"
3. When providing numbers, dates, or specific details, quote them EXACTLY as they appear in the document
4. Be concise but comprehensive in your answers
5. If asked about budgets, dates, stakeholders, or next steps, extract these PRECISELY from the document
6. Do NOT make assumptions or add information not in the document
7. Structure your answers clearly - use bullet points when listing multiple items
8. If there are multiple pieces of related information, present them all
9. When quoting financial figures, include the currency and full context
10. For dates, provide the complete date format as shown in the document

ANSWER FORMAT:
- For specific facts: Provide the exact information with context
- For lists: Use bullet points or numbered lists
- For summaries: Provide a brief overview followed by key details
- Always maintain a professional and helpful tone"""
    
    def get_answer(self, question: str, document_content: str) -> str:
        """
        Generate an answer to a question based on document content.
        
        Args:
            question: User's question
            document_content: Full document text
            
        Returns:
            AI-generated answer
        """
        try:
            # Construct the prompt with document context
            prompt = f"""{self.system_prompt}

DOCUMENT CONTENT:
{document_content}

USER QUESTION: {question}

ANSWER (based ONLY on the document content above):"""
            
            # Generate response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.2,  # Low temperature for factual responses
                            'top_p': 0.8,
                            'top_k': 40,
                            'max_output_tokens': 1024,
                        }
                    )
                    
                    # Extract text from response
                    if response and response.text:
                        return response.text.strip()
                    else:
                        return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return f"An error occurred while processing your question. Please try again or rephrase your question."
    
    def get_answer_with_chunks(self, question: str, chunks: List[str]) -> str:
        """
        Generate an answer using only relevant chunks (for large documents).
        
        Args:
            question: User's question
            chunks: List of relevant text chunks
            
        Returns:
            AI-generated answer
        """
        try:
            # Combine chunks into context
            context = "\n\n---\n\n".join(chunks)
            
            prompt = f"""{self.system_prompt}

RELEVANT DOCUMENT SECTIONS:
{context}

USER QUESTION: {question}

ANSWER (based ONLY on the document sections above):"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return f"An error occurred while processing your question. Please try again."
    
    def summarize_document(self, document_content: str) -> str:
        """
        Generate a summary of the document.
        
        Args:
            document_content: Full document text
            
        Returns:
            Document summary
        """
        try:
            prompt = f"""Please provide a well-structured summary of this document. Include:

1. **Main Topic/Purpose**: What is this document about?
2. **Key Points**: What are the most important points? (bullet points)
3. **Important Dates/Deadlines**: List any significant dates or timelines
4. **Budget/Financial Information**: Mention any financial figures or budget details
5. **Key Stakeholders**: List important people or organizations mentioned
6. **Action Items/Next Steps**: What needs to be done?

DOCUMENT:
{document_content}

STRUCTURED SUMMARY:"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'max_output_tokens': 1500,
                }
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Could not generate summary."
                
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"An error occurred while generating the summary."
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            response = self.model.generate_content("Hello")
            return response and response.text is not None
        except Exception as e:
            print(f"API key validation failed: {str(e)}")
            return False