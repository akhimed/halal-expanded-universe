from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.services.ingestion.models import IngestionRequest, ProviderPlaceRecord


class PlaceIngestionProvider(ABC):
    source_name: str

    @abstractmethod
    def fetch_places(self, request: IngestionRequest) -> list[ProviderPlaceRecord]:
        raise NotImplementedError
