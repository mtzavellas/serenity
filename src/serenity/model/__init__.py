from abc import ABC


class TypeCode(ABC):
    def __init__(self, type_id: int, type_code: str):
        self.type_id = type_id
        self.type_code = type_code

    def get_type_id(self) -> int:
        return self.type_id

    def get_type_code(self) -> str:
        return self.type_code

    def __str__(self):
        return f'{self.type_code}'
