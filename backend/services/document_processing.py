import logging
import io
import json
from abc import ABC, abstractmethod
import pdfplumber

logger = logging.getLogger("foraa.document_processing")

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        pass

class DummyOCRProvider(OCRProvider):
    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        logger.info("DummyOCRProvider invoked - OCR is not configured in this environment.")
        return "[OCR Not Configured. Unable to extract text from images.]"

class DocumentExtractor:
    def __init__(self, ocr_provider: OCRProvider = DummyOCRProvider()):
        self.ocr_provider = ocr_provider

    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        if mime_type == "application/pdf":
            try:
                text_content = []
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text(layout=True)
                        if extracted:
                            text_content.append(extracted)
                
                full_text = "\n".join(text_content)
                if not full_text.strip():
                    # Fallback to OCR if PDF contains no selectable text (scanned PDF)
                    return self.ocr_provider.extract_text(file_bytes, mime_type)
                return full_text
            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
                raise ValueError("Failed to extract text from PDF.")
                
        elif mime_type in ["image/png", "image/jpeg", "image/jpg"]:
            return self.ocr_provider.extract_text(file_bytes, mime_type)
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
        system_prompt = """
You are a highly precise medical extraction system.
Your job is to read the provided medical document text and extract structured information.

CRITICAL RULES:
1. Do NOT invent or hallucinate any values, diagnoses, reference ranges, or medications.
2. Only extract information explicitly present in the text.
3. If unsure about a value or its context, do NOT include it as a structured extraction.
4. You must distinguish between the report's text and your own summary. Do NOT make clinical diagnoses.

Output your response strictly as a JSON object matching this schema:
{
  "summary": "A human-readable summary of the report. State key findings clearly. Use phrasing like 'The report indicates...'",
  "extractions": [
    {
      "entity_type": "measurement", // Can be: measurement, medication, condition, allergy
      "data": {
         // for measurement: "type" (e.g. "Hemoglobin"), "value" (number), "unit", "reference_range", "notes"
         // for medication: "name", "dose", "frequency"
         // for condition: "name", "status"
         // for allergy: "substance", "reaction"
      },
      "source_text": "The exact snippet from the document proving this extraction",
      "confidence": "high" // high, medium, low
    }
  ]
}
Return only valid JSON. Do not include markdown codeblocks, just the raw JSON.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract information from this report:\n\n{text}"}
        ]

        try:
            # We don't have a JSON mode specifically exposed in AIService yet, but we can ask the LLM.
            # We will gather the full response stream.
            full_response = ""
            for chunk in self.ai_service.generate_stream(messages):
                full_response += chunk

            # Attempt to parse JSON (strip possible markdown formatting)
            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Failed to extract structured data from AI: {e}")
            logger.debug(f"AI Response was: {full_response}")
            raise ValueError("AI failed to return valid extraction schema.")
