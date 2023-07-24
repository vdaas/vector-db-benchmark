from typing import Any, List, Optional
from engine.base_client import IncompatibilityError
from engine.base_client.parser import BaseConditionParser, FieldValue


class ValdParser(BaseConditionParser):
    def build_condition(self, and_subfilters: List[Any] | None, or_subfilters: List[Any] | None) -> Any | None:
        raise IncompatibilityError
    
    def build_exact_match_filter(self, field_name: str, value: FieldValue) -> Any:
        raise IncompatibilityError
    
    def build_range_filter(self, field_name: str, lt: FieldValue | None, gt: FieldValue | None, lte: FieldValue | None, gte: FieldValue | None) -> Any:
        raise IncompatibilityError
    
    def build_geo_filter(self, field_name: str, lat: float, lon: float, radius: float) -> Any:
        raise IncompatibilityError
