import logging
import io
import json
import base64
from abc import ABC, abstractmethod
import pymupdf as fitz  # PyMuPDF (replaces deprecated `import fitz`)
from PIL import Image
import pytesseract
from multimodal.schemas import DocumentExtractionResult

logger = logging.getLogger("foraa.document_processing")

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        pass

class TesseractOCRProvider(OCRProvider):
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR Failed: {e}")
            return ""

class DocumentExtractor:
    def __init__(self, ocr_provider: OCRProvider = TesseractOCRProvider()):
        self.ocr_provider = ocr_provider

    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        if mime_type == "application/pdf":
            try:
                text_content = []
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Get text
                    page_text = page.get_text("text")
                    
                    # Extract tables to preserve structure
                    tables_text = ""
                    tables = page.find_tables()
                    if tables and tables.tables:
                        for idx, tab in enumerate(tables.tables):
                            tables_text += f"\n--- TABLE {idx + 1} ---\n"
                            # Extract as a markdown-like grid
                            df = tab.to_pandas()
                            if df is not None:
                                tables_text += df.to_markdown(index=False) + "\n"

                    combined_text = page_text
                    if tables_text:
                        combined_text += "\n" + tables_text

                    if combined_text.strip():
                        text_content.append(f"--- PAGE {page_num + 1} ---\n{combined_text}")
                    else:
                        # Fallback to OCR for this page if it's an image
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        ocr_text = self.ocr_provider.extract_text(img_bytes, "image/png")
                        if ocr_text.strip():
                            text_content.append(f"--- PAGE {page_num + 1} (OCR) ---\n{ocr_text}")
                
                full_text = "\n".join(text_content)
                if not full_text.strip():
                    return self.ocr_provider.extract_text(file_bytes, mime_type)
                return full_text
            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
                raise ValueError("Failed to extract text from PDF.")
                
        elif mime_type in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
            text = self.ocr_provider.extract_text(file_bytes, mime_type)
            if text:
                return f"--- IMAGE (OCR) ---\n{text}"
            return ""
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

class ReportExtractionService:
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.extractor = DocumentExtractor()

    async def process_document_text(self, text: str) -> dict:
        """
        Sends extracted text to the AI Service to generate a structured JSON payload
        containing summary and structured extraction entities.
        """
        schema_json = json.dumps(DocumentExtractionResult.model_json_schema(), indent=2)
        
        system_prompt = f"""
You are a highly precise medical extraction system.
Your job is to read the provided medical document text and extract structured information.

CRITICAL RULES:
1. Do NOT invent or hallucinate any values, diagnoses, reference ranges, dates or medications.
2. Only extract information explicitly present in the text.
3. If unsure about a value or its context, do NOT include it as a structured extraction.
4. You must distinguish between the report's text and your own summary. Do NOT make clinical diagnoses.
5. For lab measurements, you MUST extract the reference range (or normal range) exactly as printed on the user's report if present.
6. Extract the page number from the text markers (e.g. --- PAGE 2 ---) if available.

Output your response strictly as a JSON object matching this JSON schema:
{schema_json}

Return ONLY valid JSON matching this schema. Do not include markdown codeblocks like ```json, just the raw JSON.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract information from this report:\n\n{text}"}
        ]

        try:
            full_response = ""
            for chunk in self.ai_service.generate_stream(messages):
                full_response += chunk

            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            # Validate with pydantic
            result = DocumentExtractionResult.model_validate_json(cleaned.strip())
            return result.model_dump()
        except Exception as e:
            logger.error(f"Failed to extract structured data from AI: {e}")
            logger.debug(f"AI Response was: {full_response}")
            raise ValueError("AI failed to return valid extraction schema.")
