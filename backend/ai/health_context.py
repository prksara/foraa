from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, HealthProfile, HealthCondition, Allergy, Medication, Lifestyle, HealthGoal, Measurement, HealthDocument, HealthEvent
from services.evidence_retrieval import EvidencePack

class HealthContextBuilder:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def build_context(self, user_message: str, attachment_ids: Optional[list[str]] = None, evidence_pack: Optional[EvidencePack] = None, intent: Optional[dict] = None) -> str:
        """
        Builds a structured XML-delimited health context based on the user's data.
        In the future, this can use keyword/topic relevance matching based on `user_message`.
        For now, we fetch the active/relevant data and format it.
        """
        needs_profile = True
        if intent:
            needs_profile = intent.get("needs_profile", True)

        xml_parts = ["<health_context>"]
        xml_parts.append("<guidelines>")
        xml_parts.append("State information as user-provided context, not absolute medical truth. Do not treat incomplete or unverified records as clinical diagnoses. Use this context to personalize your responses safely.")
        xml_parts.append("</guidelines>")

        if needs_profile:
            # Fetch data
            profile_stmt = select(HealthProfile).where(HealthProfile.user_id == self.user.id)
            profile_res = await self.db.execute(profile_stmt)
            profile: Optional[HealthProfile] = profile_res.scalar_one_or_none()

            conditions_stmt = select(HealthCondition).where(HealthCondition.user_id == self.user.id, HealthCondition.status == 'active')
            conditions_res = await self.db.execute(conditions_stmt)
            conditions = conditions_res.scalars().all()

            allergies_stmt = select(Allergy).where(Allergy.user_id == self.user.id, Allergy.status == 'active')
            allergies_res = await self.db.execute(allergies_stmt)
            allergies = allergies_res.scalars().all()

            meds_stmt = select(Medication).where(Medication.user_id == self.user.id, Medication.status == 'active')
            meds_res = await self.db.execute(meds_stmt)
            meds = meds_res.scalars().all()
            
            goals_stmt = select(HealthGoal).where(HealthGoal.user_id == self.user.id, HealthGoal.status == 'active')
            goals_res = await self.db.execute(goals_stmt)
            goals = goals_res.scalars().all()
            
            measurements_stmt = select(Measurement).where(Measurement.user_id == self.user.id).order_by(Measurement.created_at.desc()).limit(20)
            measurements_res = await self.db.execute(measurements_stmt)
            measurements = measurements_res.scalars().all()
            
            events_stmt = select(HealthEvent).where(HealthEvent.user_id == self.user.id).order_by(HealthEvent.event_date.desc()).limit(15)
            events_res = await self.db.execute(events_stmt)
            events = events_res.scalars().all()
            
            if profile:
                xml_parts.append("<profile>")
                if profile.sex: xml_parts.append(f"  <sex>{profile.sex}</sex>")
                if profile.blood_type: xml_parts.append(f"  <blood_type>{profile.blood_type}</blood_type>")
                if profile.height and profile.height_unit: xml_parts.append(f"  <height>{profile.height} {profile.height_unit}</height>")
                if profile.weight and profile.weight_unit: xml_parts.append(f"  <weight>{profile.weight} {profile.weight_unit}</weight>")
                xml_parts.append("</profile>")
            
            if conditions:
                xml_parts.append("<active_conditions>")
                for c in conditions:
                    xml_parts.append(f"  <condition name=\"{c.name}\" source=\"{c.source}\"/>")
                xml_parts.append("</active_conditions>")
                
            if allergies:
                xml_parts.append("<allergies>")
                for a in allergies:
                    xml_parts.append(f"  <allergy substance=\"{a.substance}\" severity=\"{a.severity or 'unknown'}\" source=\"{a.source}\"/>")
                xml_parts.append("</allergies>")
                
            if meds:
                xml_parts.append("<active_medications>")
                for m in meds:
                    xml_parts.append(f"  <medication name=\"{m.name}\" dose=\"{m.dose or ''} {m.dose_unit or ''}\" source=\"{m.source}\"/>")
                xml_parts.append("</active_medications>")
                
            if goals:
                xml_parts.append("<active_goals>")
                for g in goals:
                    xml_parts.append(f"  <goal title=\"{g.title}\" category=\"{g.category or 'general'}\"/>")
                xml_parts.append("</active_goals>")

            if measurements:
                xml_parts.append("<past_measurements>")
                for m in measurements:
                    date_str = m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown"
                    xml_parts.append(f"  <measurement type=\"{m.type}\" value=\"{m.value}\" unit=\"{m.unit}\" date=\"{date_str}\" source=\"{m.source}\"/>")
                xml_parts.append("</past_measurements>")

            if events:
                xml_parts.append("<recent_health_events>")
                for e in events:
                    date_str = e.event_date.strftime("%Y-%m-%d") if e.event_date else "unknown date"
                    xml_parts.append(f"  <event type=\"{e.event_type}\" date=\"{date_str}\" source=\"{e.source_type}\">")
                    xml_parts.append(f"    <title>{e.title}</title>")
                    if e.description:
                        xml_parts.append(f"    <description>{e.description}</description>")
                    if e.structured_data:
                        xml_parts.append(f"    <data>{e.structured_data}</data>")
                    xml_parts.append(f"  </event>")
                xml_parts.append("</recent_health_events>")
                
        if attachment_ids:
            from database.models import DocumentExtraction
            
            for attachment_id in attachment_ids:
                report_stmt = select(HealthDocument).where(HealthDocument.id == attachment_id, HealthDocument.user_id == self.user.id)
                report_res = await self.db.execute(report_stmt)
                report = report_res.scalar_one_or_none()
                
                if report:
                    xml_parts.append("<active_report>")
                    xml_parts.append(f"  <filename>{report.filename}</filename>")
                    if report.summary:
                        xml_parts.append(f"  <summary>{report.summary}</summary>")
                        
                    # Also load extractions for this document to give the LLM structured data
                    ext_stmt = select(DocumentExtraction).where(DocumentExtraction.document_id == report.id)
                    ext_res = await self.db.execute(ext_stmt)
                    extractions = ext_res.scalars().all()
                    
                    if extractions:
                        xml_parts.append("  <extracted_data>")
                        for ext in extractions:
                            xml_parts.append(f"    <entity type=\"{ext.entity_type}\" confidence=\"{ext.confidence}\">")
                            import json
                            xml_parts.append(f"      {json.dumps(ext.data)}")
                            xml_parts.append(f"    </entity>")
                        xml_parts.append("  </extracted_data>")
                    
                    xml_parts.append("</active_report>")

        if evidence_pack and evidence_pack.retrieved_items:
            xml_parts.append("<medical_evidence>")
            xml_parts.append("The following medical evidence was retrieved based on the user's query. USE THIS EVIDENCE to answer medical questions. Always cite the provided [citation_reference].")
            for item in evidence_pack.retrieved_items:
                xml_parts.append(f"  <evidence source=\"{item.source_name}\" quality=\"{item.source_quality}\" citation=\"{item.citation_reference}\">")
                xml_parts.append(f"    <title>{item.title}</title>")
                if item.section: xml_parts.append(f"    <section>{item.section}</section>")
                xml_parts.append(f"    <content>{item.content}</content>")
                xml_parts.append("  </evidence>")
            xml_parts.append("</medical_evidence>")

        xml_parts.append("</health_context>")
        return "\n".join(xml_parts)
