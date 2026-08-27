import os
import aiohttp
from typing import List
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

class HuggingFaceAPIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, token: str, model_id: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.token = token
        self.model_id = model_id
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_id}"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def _request(self, payload) -> List:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"HuggingFace API Error: {response.status} - {text}")
                return await response.json()

    async def embed_text(self, text: str) -> List[float]:
        result = await self._request({"inputs": [text]})
        # Result is typically a list of lists of floats
        return result[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        result = await self._request({"inputs": texts})
        return result

class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dim: int = 384):
        self.dim = dim

    async def embed_text(self, text: str) -> List[float]:
        import random
        return [random.uniform(-1.0, 1.0) for _ in range(self.dim)]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]

def get_embedding_provider() -> EmbeddingProvider:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("WARNING: HF_TOKEN not set. Using MockEmbeddingProvider.")
        return MockEmbeddingProvider(dim=384)
    return HuggingFaceAPIEmbeddingProvider(token=token)
