from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union

class ExtractedMeasurement(BaseModel):
    type: str = Field(..., description="The name of the test or measurement (e.g., Hemoglobin, Glucose)")
    value: str = Field(..., description="The exact value extracted")
    unit: Optional[str] = Field(None, description="The unit of measurement (e.g., g/dL, mg/dL)")
    reference_range: Optional[str] = Field(None, description="The reference range EXACTLY as printed on the report. Do NOT invent a range.")
    flag: Optional[Literal["LOW", "NORMAL", "HIGH", "CRITICAL_REPORTED", "UNKNOWN"]] = Field("UNKNOWN", description="Abnormality flag based strictly on the report's own indicators")
    notes: Optional[str] = Field(None, description="Any specific notes or comments attached to this result")

class ExtractedMedication(BaseModel):
    name: str = Field(..., description="The name of the medication")
    dose: Optional[str] = Field(None, description="The strength or dose (e.g., 500mg)")
    frequency: Optional[str] = Field(None, description="How often to take it (e.g., twice daily)")
    route: Optional[str] = Field(None, description="The route of administration (e.g., oral)")
    instructions: Optional[str] = Field(None, description="Specific instructions for taking the medication")

class ExtractedCondition(BaseModel):
    name: str = Field(..., description="The name of the diagnosed condition or symptom")
    status: Optional[str] = Field("unknown", description="active, resolved, or unknown")

class ExtractedAllergy(BaseModel):
    substance: str = Field(..., description="The allergen substance")
    reaction: Optional[str] = Field(None, description="The allergic reaction")

class ExtractionEntity(BaseModel):
    entity_type: Literal["measurement", "medication", "condition", "allergy"] = Field(..., description="The type of the extracted entity")
    data: Union[ExtractedMeasurement, ExtractedMedication, ExtractedCondition, ExtractedAllergy] = Field(..., description="The structured data for this entity")
    source_text: str = Field(..., description="The exact snippet of text from the document proving this extraction")
    page: Optional[int] = Field(None, description="The page number where this was found (1-indexed)")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence in the extraction reliability, not medical certainty")

class DocumentExtractionResult(BaseModel):
    document_type: Literal["LAB_REPORT", "PRESCRIPTION", "MEDICATION_LABEL", "DISCHARGE_SUMMARY", "DOCTOR_NOTE", "IMAGING_REPORT", "VACCINATION_RECORD", "HEALTH_SCREENSHOT", "GENERAL_HEALTH_DOCUMENT", "UNKNOWN"] = Field(..., description="The classified type of the document")
    summary: str = Field(..., description="A human-readable summary of the document. State key findings clearly. Do NOT make clinical diagnoses.")
    extractions: List[ExtractionEntity] = Field(default_factory=list, description="A list of structured extractions found in the document")
