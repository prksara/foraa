import re
from typing import List, Dict, Any

class Chunk:
    def __init__(self, content: str, section_title: str = None, metadata: Dict[str, Any] = None):
        self.content = content
        self.section_title = section_title
        self.metadata = metadata or {}

class SemanticChunker:
    """
    Semantic-aware chunker that respects paragraphs and sections (like Markdown headers).
    """
    def __init__(self, max_chunk_size: int = 1500, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        # Regex to detect markdown style headers (e.g., "## Section Title")
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def chunk_text(self, text: str, base_metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Splits text into chunks while preserving section boundaries.
        """
        if not text:
            return []
            
        base_metadata = base_metadata or {}
        
        # Split text into sections based on headers
        # We find all header matches and split the text accordingly
        chunks = []
        
        headers = list(self.header_pattern.finditer(text))
        
        sections = []
        if not headers:
            sections.append(("", text))
        else:
            # First section might be before any header
            if headers[0].start() > 0:
                sections.append(("", text[:headers[0].start()]))
                
            for i in range(len(headers)):
                header_match = headers[i]
                section_title = header_match.group(2).strip()
                start_idx = header_match.end()
                
                if i < len(headers) - 1:
                    end_idx = headers[i+1].start()
                else:
                    end_idx = len(text)
                    
                content = text[start_idx:end_idx].strip()
                if content:
                    sections.append((section_title, content))

        # Now chunk each section based on paragraphs
        for section_title, content in sections:
            paragraphs = re.split(r'\n\s*\n', content)
            
            current_chunk_text = ""
            if section_title:
                current_chunk_text = f"[{section_title}]\n"
                
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                    
                # If a single paragraph is too large, we must hard split it (fallback)
                if len(p) > self.max_chunk_size:
                    # Append current chunk if exists
                    if current_chunk_text.strip() and current_chunk_text.strip() != f"[{section_title}]":
                        chunks.append(Chunk(current_chunk_text.strip(), section_title, base_metadata.copy()))
                        current_chunk_text = f"[{section_title}]\n" if section_title else ""
                        
                    # Hard split paragraph
                    words = p.split(' ')
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 > self.max_chunk_size:
                            chunks.append(Chunk(temp_chunk.strip(), section_title, base_metadata.copy()))
                            # overlapping tail
                            overlap_text = " ".join(temp_chunk.split(' ')[-20:]) # rough word overlap
                            temp_chunk = overlap_text + " " + word + " "
                        else:
                            temp_chunk += word + " "
                    if temp_chunk.strip():
                        chunks.append(Chunk(temp_chunk.strip(), section_title, base_metadata.copy()))
                    continue
                
                # Check if adding this paragraph exceeds max size
                if len(current_chunk_text) + len(p) + 2 > self.max_chunk_size:
                    chunks.append(Chunk(current_chunk_text.strip(), section_title, base_metadata.copy()))
                    
                    # Start new chunk with some overlap from previous if possible
                    overlap_context = ""
                    if current_chunk_text:
                        # Grab last few words of previous chunk
                        overlap_context = " ".join(current_chunk_text.split()[-30:]) + "\n\n"
                        
                    current_chunk_text = (f"[{section_title}]\n" if section_title else "") + overlap_context + p + "\n\n"
                else:
                    current_chunk_text += p + "\n\n"
                    
            if current_chunk_text.strip() and current_chunk_text.strip() != f"[{section_title}]":
                chunks.append(Chunk(current_chunk_text.strip(), section_title, base_metadata.copy()))
                
        # Assign chunk index metadata
        for idx, c in enumerate(chunks):
            c.metadata['chunk_index'] = idx
            
        return chunks
