import pytest
import io
import fitz
from pydantic import ValidationError
from multimodal.schemas import DocumentExtractionResult
from services.document_processing import DocumentExtractor

def test_document_extraction_result_schema_validation():
    # Valid data
    valid_data = {
        "document_type": "LAB_REPORT",
        "summary": "Patient has elevated Hemoglobin.",
        "extractions": [
            {
                "entity_type": "measurement",
                "data": {
                    "type": "Hemoglobin",
                    "value": "15.5",
                    "unit": "g/dL",
                    "reference_range": "13.0 - 17.0",
                    "flag": "NORMAL"
                },
                "source_text": "Hemoglobin 15.5 g/dL",
                "page": 1,
                "confidence": "high"
            }
        ]
    }
    result = DocumentExtractionResult(**valid_data)
    assert result.document_type == "LAB_REPORT"
    assert result.extractions[0].data.flag == "NORMAL"

def test_document_extraction_result_schema_invalid():
    invalid_data = {
        "document_type": "INVALID_TYPE", # Not in literal
        "summary": "Summary",
        "extractions": []
    }
    with pytest.raises(ValidationError):
        DocumentExtractionResult(**invalid_data)

def test_document_extractor_pdf_no_text():
    # Mock OCR provider
    class MockOCR:
        def extract_text(self, b, m):
            return "OCR TEXT"

    extractor = DocumentExtractor(ocr_provider=MockOCR())
    
    # Create an empty PDF using fitz
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.write()
    doc.close()

    text = extractor.extract_text(pdf_bytes, "application/pdf")
    # Empty page should trigger OCR fallback
    assert "OCR" in text or "OCR TEXT" in text

def test_document_extractor_pdf_with_text():
    extractor = DocumentExtractor()
    
    # Create PDF with text
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Blood Test Result: Glucose 95 mg/dL")
    pdf_bytes = doc.write()
    doc.close()

    text = extractor.extract_text(pdf_bytes, "application/pdf")
    assert "Glucose 95" in text
    assert "PAGE 1" in text
