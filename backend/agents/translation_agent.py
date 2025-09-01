"""
Autonomous Translation Agent - Handles document processing and translation directly
"""

import logging
from pathlib import Path
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class TranslationAgent:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.stats = {"documents_processed": 0, "characters_translated": 0, "errors": 0}
        logger.info("Autonomous Translation Agent initialized")

    async def process_document(self, document_path: str, source_language: str = "ja", target_language: str = "en") -> dict:
        """Process document directly - extract text and translate in one workflow"""
        try:
            file_path = Path(document_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document not found: {document_path}")

            # Step 1: Extract text based on file type
            logger.info(f"Processing document: {file_path.name}")
            extracted_text = await self._extract_text_from_document(document_path)

            if not extracted_text:
                raise ValueError("No text could be extracted from document")

            # Step 2: Split into chunks for translation
            chunks = self._split_into_translation_chunks(extracted_text)
            logger.info(f"Split document into {len(chunks)} chunks for translation")

            # Step 3: Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Translating chunk {i+1}/{len(chunks)}")
                translated_chunk = await self._translate_chunk(chunk, source_language, target_language)
                translated_chunks.append(translated_chunk)

            full_translation = "\n\n".join(translated_chunks)

            # Update statistics
            self.stats["documents_processed"] += 1
            self.stats["characters_translated"] += len(full_translation)

            return {
                "success": True,
                "original_text": extracted_text,
                "translated_text": full_translation,
                "source_language": source_language,
                "target_language": target_language,
                "chunks_processed": len(chunks),
                "character_count": len(full_translation),
                "word_count": len(full_translation.split()),
                "document_type": file_path.suffix,
                "processing_stats": self.stats.copy()
            }

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Translation processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "translated_text": f"Translation failed: {str(e)}",
                "processing_stats": self.stats.copy()
            }

    async def _extract_text_from_document(self, document_path: str) -> str:
        """Extract text directly from various document formats"""
        file_ext = Path(document_path).suffix.lower()

        if file_ext == '.txt':
            return await self._extract_from_txt(document_path)
        elif file_ext == '.pdf':
            return await self._extract_from_pdf(document_path)
        elif file_ext in ['.docx', '.doc']:
            return await self._extract_from_docx(document_path)
        else:
            raise ValueError(f"Unsupported document format: {file_ext}")

    async def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files with proper encoding handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Extracted {len(content)} characters from TXT")
            return content
        except UnicodeDecodeError:
            # Try Japanese encoding
            try:
                with open(file_path, 'r', encoding='shift_jis') as f:
                    content = f.read()
                logger.info(f"Extracted {len(content)} characters from TXT (Shift-JIS)")
                return content
            except:
                # Final fallback
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                logger.info(f"Extracted {len(content)} characters from TXT (UTF-8 with errors ignored)")
                return content

    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                content = "\n".join(text_parts)
            logger.info(f"Extracted {len(content)} characters from PDF")
            return content
        except ImportError:
            logger.warning("PyPDF2 not available, using fallback")
            return f"Demo PDF content from {Path(file_path).name}\n\nThis is demonstration Japanese text that would be extracted from the PDF document."

    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files using mammoth"""
        try:
            import mammoth

            def extract_mammoth():
                with open(file_path, "rb") as docx_file:
                    result = mammoth.extract_raw_text(docx_file)
                    return result.value

            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_mammoth)
            logger.info(f"Extracted {len(content)} characters from DOCX using Mammoth")
            return content
        except ImportError:
            logger.warning("Mammoth not available, using fallback")
            return f"Demo DOCX content from {Path(file_path).name}\n\nThis is demonstration Japanese text that would be extracted from the DOCX document."

    def _split_into_translation_chunks(self, text: str, max_chunk_size: int = 1500) -> list:
        """Split text into chunks suitable for translation"""
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            if current_length + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
            else:
                current_chunk.append(paragraph)
                current_length += len(paragraph)

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    async def _translate_chunk(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate a single text chunk"""
        if not self.gemini_client or not self.gemini_client.is_available():
            return f"[DEMO TRANSLATION] {text[:200]}... (Configure GEMINI_API_KEY for real translation)"

        translation_prompt = f"""Translate this Japanese technical document text to English.
        Preserve all technical terms, specifications, part numbers, and measurements exactly.
        Maintain original structure and formatting.

        Japanese text:
        {text}

        English translation:"""

        try:
            response = await self.gemini_client.generate_content(
                translation_prompt, 
                temperature=0.1, 
                max_tokens=2000
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[TRANSLATION ERROR: {str(e)}] {text}"

    def get_stats(self) -> dict:
        """Get processing statistics"""
        return self.stats.copy()
