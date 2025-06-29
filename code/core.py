import os
from abc import ABC, abstractmethod
from typing import Dict, Any

class DataParser(ABC):
    """所有解析器的基类"""
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        pass
        
class DataParserFactory:
    _parsers = {}

    @classmethod
    def register_parser(cls, data_type: str, parser_class):
        cls._parsers[data_type] = parser_class

    @classmethod
    def get_parser(cls, file_path: str) -> DataParser:
        ext = os.path.splitext(file_path)[1].lower()
        for data_type, parser_class in cls._parsers.items():
            if ext in parser_class.supported_extensions():
                return parser_class()
        raise ValueError(f"Unsupported file format: {ext}")