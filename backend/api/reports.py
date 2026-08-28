from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import datetime
import magic

from database.database import get_db
from database.models import User, HealthDocument, DocumentExtraction, HealthCondition, Allergy, Medication, Measurement, HealthEvent
from auth.security import get_current_user
from services.storage import storage_service
from services.document_processing import ReportExtractionService

router = APIRouter(prefix="/reports", tags=["reports"])

async def process_document_background(
    document_id: str, 
    user_id: str, 
    file_bytes: bytes, 
    mime_type: str, 
    db: AsyncSession
):
    try:
        # Mark processing
        doc = await db.get(HealthDocument, document_id)
        if not doc or doc.user_id != user_id:
            return
        doc.status = "processing"
        await db.commit()

        # Process
        from main import _get_ai_service
        ai_service = _get_ai_service()
        extraction_service = ReportExtractionService(ai_service=ai_service)
        
        # Extract text (this is sync but we're running it in a background task thread pool by FastAPI)
        text = extraction_service.extractor.extract_text(file_bytes, mime_type)
        
        # Get structured JSON via LLM
        result = await extraction_service.process_document_text(text)
        
        # Update Document
        doc.summary = result.get("summary", "No summary generated.")
        doc.status = "needs_review"
        doc.processed_at = datetime.datetime.utcnow()

        # Create Extractions
        extractions = result.get("extractions", [])
        for ext in extractions:
            db_ext = DocumentExtraction(
                document_id=doc.id,
                user_id=user_id,
                entity_type=ext.get("entity_type", "unknown"),
                data=ext.get("data", {}),
                source_text=ext.get("source_text"),
                confidence=ext.get("confidence", "low"),
                status="pending_review"
            )
            db.add(db_ext)
            
        await db.commit()

    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        doc = await db.get(HealthDocument, document_id)
        if doc:
            doc.status = "failed"
            await db.commit()


@router.post("/upload")
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Validate mime type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    file_bytes = await file.read()
    
    # 5MB limit
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB).")

    # Validate true mime type using python-magic
    try:
        true_mime = magic.from_buffer(file_bytes, mime=True)
    except Exception as e:
        print(f"Magic byte validation failed: {e}")
        raise HTTPException(status_code=400, detail="Could not validate file contents.")

    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
    if true_mime not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file content type: {true_mime}")

    try:
        # 1. Upload to storage
        storage_path = storage_service.upload_document(user.id, file.filename, file_bytes, file.content_type)
        
        # 2. Create DB Record
        doc = HealthDocument(
            user_id=user.id,
            filename=file.filename,
            mime_type=file.content_type,
            file_size=len(file_bytes),
            storage_path=storage_path,
            status="uploaded"
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        # 3. Queue processing
        background_tasks.add_task(process_document_background, doc.id, user.id, file_bytes, file.content_type, db)
        
        return {"id": doc.id, "status": doc.status, "message": "Upload successful, processing started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(HealthDocument).where(HealthDocument.user_id == user.id).order_by(HealthDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return [{"id": d.id, "filename": d.filename, "status": d.status, "created_at": d.created_at} for d in docs]


@router.get("/{document_id}")
async def get_report(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    doc = await db.get(HealthDocument, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Get extractions
    ext_result = await db.execute(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    )
    extractions = ext_result.scalars().all()

    # Get download URL
    download_url = storage_service.get_signed_url(doc.storage_path)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "summary": doc.summary,
        "created_at": doc.created_at,
        "download_url": download_url,
        "extractions": [
            {
                "id": e.id,
                "entity_type": e.entity_type,
                "data": e.data,
                "source_text": e.source_text,
                "confidence": e.confidence,
                "status": e.status
            } for e in extractions
        ]
    }


@router.delete("/{document_id}")
async def delete_report(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    doc = await db.get(HealthDocument, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    # 1. Delete from storage
    storage_service.delete_document(doc.storage_path)
    
    # 2. Delete from DB (cascade deletes extractions)
    await db.delete(doc)
    await db.commit()
    
    return {"status": "deleted"}


@router.post("/{document_id}/extractions/{extraction_id}/confirm")
async def confirm_extraction(
    document_id: str,
    extraction_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Verify ownership
    ext = await db.get(DocumentExtraction, extraction_id)
    if not ext or ext.user_id != user.id or ext.document_id != document_id:
        raise HTTPException(status_code=404, detail="Extraction not found.")
    
    if ext.status != "pending_review":
        raise HTTPException(status_code=400, detail="Only pending extractions can be confirmed.")

    # Map to real model
    try:
        source_ref = f"Document: {document_id}"
        if ext.entity_type == "condition":
            record = HealthCondition(
                user_id=user.id,
                name=ext.data.get("name", "Unknown Condition"),
                status=ext.data.get("status", "unknown"),
                source="document",
                source_reference=source_ref
            )
        elif ext.entity_type == "allergy":
            record = Allergy(
                user_id=user.id,
                substance=ext.data.get("substance", "Unknown"),
                reaction=ext.data.get("reaction"),
                source="document",
                source_reference=source_ref
            )
        elif ext.entity_type == "medication":
            record = Medication(
                user_id=user.id,
                name=ext.data.get("name", "Unknown Medication"),
                dose=ext.data.get("dose"),
                frequency=ext.data.get("frequency"),
                source="document",
                source_reference=source_ref
            )
        elif ext.entity_type == "measurement":
            # Attempt to safely cast value
            raw_val = ext.data.get("value", 0)
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                val = 0.0

            record = Measurement(
                user_id=user.id,
                type=ext.data.get("type", "unknown"),
                value=val,
                unit=ext.data.get("unit", ""),
                notes=ext.data.get("notes"),
                source="document"
            )
        else:
            raise ValueError(f"Unknown entity type {ext.entity_type}")

        db.add(record)
        
        # Phase 5: Also create a timeline HealthEvent
        event_title = f"Report Extraction: {ext.entity_type.capitalize()}"
        if ext.entity_type == "condition":
            event_title = f"Condition: {ext.data.get('name', 'Unknown')}"
        elif ext.entity_type == "allergy":
            event_title = f"Allergy: {ext.data.get('substance', 'Unknown')}"
        elif ext.entity_type == "medication":
            event_title = f"Medication: {ext.data.get('name', 'Unknown')}"
        elif ext.entity_type == "measurement":
            event_title = f"Measurement: {ext.data.get('type', 'Unknown')} {ext.data.get('value', '')} {ext.data.get('unit', '')}"

        event = HealthEvent(
            user_id=user.id,
            event_type=ext.entity_type,
            title=event_title,
            description=f"Extracted from report {doc.filename if 'doc' in locals() and hasattr(doc, 'filename') else ''}",
            source_type="report",
            source_id=document_id,
            confidence=1.0, # confirmed
            structured_data=ext.data
        )
        db.add(event)
        
        ext.status = "confirmed"

        # Check if all extractions for this document are processed
        # If so, maybe mark document as processed (optional, UI can handle)
        doc = await db.get(HealthDocument, document_id)
        if doc.status == "needs_review":
            # Check remaining
            res = await db.execute(select(DocumentExtraction).where(
                DocumentExtraction.document_id == document_id,
                DocumentExtraction.status == "pending_review",
                DocumentExtraction.id != extraction_id
            ))
            if len(res.scalars().all()) == 0:
                doc.status = "processed"

        await db.commit()
        return {"status": "confirmed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/extractions/{extraction_id}/reject")
async def reject_extraction(
    document_id: str,
    extraction_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ext = await db.get(DocumentExtraction, extraction_id)
    if not ext or ext.user_id != user.id or ext.document_id != document_id:
        raise HTTPException(status_code=404, detail="Extraction not found.")
    
    ext.status = "rejected"
    
    # Check if doc is fully processed
    doc = await db.get(HealthDocument, document_id)
    if doc.status == "needs_review":
        res = await db.execute(select(DocumentExtraction).where(
            DocumentExtraction.document_id == document_id,
            DocumentExtraction.status == "pending_review",
            DocumentExtraction.id != extraction_id
        ))
        if len(res.scalars().all()) == 0:
            doc.status = "processed"

    await db.commit()
    return {"status": "rejected"}
