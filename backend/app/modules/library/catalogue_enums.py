"""Book catalogue enumerations."""

from enum import Enum


class CatalogueSortField(str, Enum):
    TITLE = "title"
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
    PUBLICATION_YEAR = "publication_year"


class CatalogueSortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"