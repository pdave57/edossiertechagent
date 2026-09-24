import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document as LangchainDocument

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
        )
    
    def load_markdown(self, file_path: str) -> List[LangchainDocument]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [LangchainDocument(
            page_content=content,
            metadata={"source": file_path, "doc_type": "user_manual"}
        )]
    
    def load_pdf(self, file_path: str) -> List[LangchainDocument]:
        documents = []
        
        # Try pdfplumber first (fast, works for text-based PDFs)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        documents.append(LangchainDocument(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "doc_type": "national_policy",
                                "page": i + 1
                            }
                        ))
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        
        # If no text extracted, try PyMuPDF (fitz) with OCR fallback
        if not documents:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for i, page in enumerate(doc):
                    text = page.get_text()
                    if text and text.strip():
                        documents.append(LangchainDocument(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "doc_type": "national_policy",
                                "page": i + 1
                            }
                        ))
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")
        
        # If still no text, try OCR with pytesseract (requires tesseract-ocr system package)
        if not documents:
            try:
                from pdf2image import convert_from_path
                import pytesseract
                logger.info("Attempting OCR with pytesseract...")
                images = convert_from_path(file_path, dpi=200)
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(image)
                    if text and text.strip():
                        documents.append(LangchainDocument(
                            page_content=text,
                            metadata={
                                "source": file_path,
                                "doc_type": "national_policy",
                                "page": i + 1,
                                "extraction_method": "ocr"
                            }
                        ))
                logger.info(f"OCR extracted text from {len(documents)} pages")
            except Exception as e:
                logger.warning(f"OCR not available (install tesseract-ocr): {e}")
        
        if not documents:
            logger.warning(f"No text extracted from PDF: {file_path}. May be image-based. Install tesseract-ocr for OCR.")
        
        return documents
    
    def load_document(self, file_path: str) -> List[LangchainDocument]:
        ext = Path(file_path).suffix.lower()
        
        if ext == '.md':
            return self.load_markdown(file_path)
        elif ext == '.pdf':
            return self.load_pdf(file_path)
        elif ext == '.txt':
            return self.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def load_text(self, file_path: str) -> List[LangchainDocument]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Infer doc_type from filename
        filename = Path(file_path).stem.lower()
        if "architecture" in filename:
            doc_type = "architecture"
        elif "user_manual" in filename:
            doc_type = "user_manual"
        else:
            doc_type = "text"
        
        return [LangchainDocument(
            page_content=content,
            metadata={"source": file_path, "doc_type": doc_type}
        )]
    
    def chunk_documents(self, documents: List[LangchainDocument]) -> List[LangchainDocument]:
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.embeddings.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        documents = self.load_document(file_path)
        
        if not documents:
            return {"chunks": [], "embeddings": [], "metadata": {}}
        
        chunks = self.chunk_documents(documents)
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        
        metadata = {
            "source": file_path,
            "doc_type": documents[0].metadata.get("doc_type", "unknown"),
            "total_chunks": len(chunks),
            "original_docs": len(documents),
        }
        
        return {
            "chunks": texts,
            "embeddings": embeddings,
            "metadata": metadata,
            "langchain_chunks": chunks
        }


document_processor = DocumentProcessor()