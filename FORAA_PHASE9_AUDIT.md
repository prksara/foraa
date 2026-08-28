# FORAA.AI - PHASE 9 AUDIT (MULTIMODAL HEALTH INTELLIGENCE)

This document maps the Phase 9 Multimodal requirements against the existing codebase.

## 1. Existing Systems vs Multimodal Needs

| Feature | Status | Notes / Location |
|---|---|---|
| **Storage & Security** | `[~]` | Supabase private bucket `health_documents` used via `StorageService`. File size (5MB limit) and MIME type validation exist in `reports.py`. Needs magic bytes validation and user isolation testing. |
| **Document Lifecycle** | `[✓]` | `HealthDocument` model has `status` field (`uploaded`, `processing`, `processed`, `needs_review`, `failed`). |
| **User Isolation** | `[✓]` | APIs check `doc.user_id != user.id`. Signed URLs are scoped to paths. |
| **PDF Extraction** | `[~]` | Basic `pdfplumber` text extraction exists in `DocumentExtractor`. **Lacks** page preservation, table extraction, and precise bounding boxes. |
| **OCR & Images** | `[ ]` | Only a `DummyOCRProvider` exists. Image support is unimplemented. |
| **Table Extraction** | `[ ]` | Not implemented. Text is currently flattened. |
| **Classification** | `[ ]` | Document classification (Lab, Prescription, etc.) is missing. |
| **Structured Extraction** | `[~]` | `ReportExtractionService` uses an LLM to generate JSON, but lacks strict reference range enforcement, confidence mapping, and specific schemas for Labs/Prescriptions. |
| **Timeline Integration** | `[✓]` | `confirm_extraction` correctly creates a `HealthEvent` from confirmed extractions. |
| **Human Review UI** | `[✓]` | `Reports.jsx` implements the "Confirm/Reject" flow perfectly. |
| **Chat Attachments** | `[ ]` | Assistant composer lacks the ability to attach files directly or reference multiple attachments. |
| **Comparison & Trends** | `[ ]` | Not implemented in reasoning engine. |
| **Cost Control** | `[ ]` | Entire text is passed to LLM. No smart selection or chunking. |

## 2. Missing Multimodal Modules

| Module | Status | Requirement |
|---|---|---|
| **File Policy & Magic Bytes** | `[ ]` | Secure file validation beyond just HTTP headers. |
| **Document Classification** | `[ ]` | Routing document to correct extraction strategy based on type. |
| **OCR Integration** | `[ ]` | A real OCR provider (e.g. Tesseract or cloud vision). |
| **Table parser** | `[ ]` | Recognizing structured rows/columns in PDFs. |
| **Image Understanding** | `[ ]` | Vision model integration for image analysis. |
| **Structured Schemas** | `[ ]` | Specific `LabFinding` and `Prescription` schemas. |
| **Source Preservation** | `[ ]` | Mapping findings to `page` and original text. |
| **Multiple Attachments UI** | `[ ]` | Chat composer needs an attachment chip system. |
| **Multimodal RAG** | `[ ]` | Injecting document context safely into chat reasoning. |
| **Reference Range Protection**| `[ ]` | Explicit system prompt bounds to prevent hallucinated ranges. |
| **Safety Integration** | `[ ]` | Validating extracted data against Phase 8 safety constraints. |

## Conclusion
The foundation for Phase 9 is surprisingly solid. The upload plumbing, database relations, and most importantly, the Human-in-the-Loop review UI are already functioning. 

The primary work for Phase 9 is to:
1. Upgrade the extraction pipeline (OCR, Tables, Page Mapping, Vision).
2. Create strict structured schemas for medical findings.
3. Integrate attachments directly into the Chat UI (`Assistant.jsx`).
4. Upgrade the Reasoning Engine to handle document context alongside existing history.
