from enum import auto

from app.schema_types.base import BaseEnum


class ActorType(BaseEnum):
    Application = auto()
    Group = auto()
    Organization = auto()
    Person = auto()
    Service = auto()

    @classmethod
    def _missing_(cls, value):
        # https://stackoverflow.com/a/68311691/295606
        for member in cls:
            if member.value.upper() == value.upper():
                return member
            # SPECIAL CASES
            if member.value.upper() == "PERSON" and value.upper() == "CREATOR":
                return member
            if member.value.upper() == "SERVICE" and value.upper() == "WORK":
                return member

    @property
    def as_uri(self):
        terms = {
            "Person": "creator",
            "Service": "work",
        }
        return terms.get(self.value, self.value.lower())
