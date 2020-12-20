from typing import Any
import pydantic
from pydantic import BaseModel, Field, validator  # exposing to the top
from pydantic.utils import GetterDict
from django.db.models import QuerySet, Manager
from django.db.models.fields.files import FieldFile


pydantic_version = list(map(int, pydantic.VERSION.split(".")))[:2]
assert pydantic_version >= [1, 6], "Pydantic 1.6+ required"


# Since "Model" word would be very confusing when used in django context
# this module basically makes alias for it named "Schema"
# and ads extra whistles to be able to work with django querysets and managers


class DjangoGetter(GetterDict):
    def get(self, key: Any, default: Any = None) -> Any:
        result = super().get(key, default)

        print(key, result, type(result))

        if isinstance(result, Manager):
            return list(result.all())

        elif isinstance(result, QuerySet):
            return list(result)
        
        elif isinstance(result, FieldFile):
            if not result:
                return None
            return result.url

        return result


class Schema(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = DjangoGetter
