"""Shared pydantic validators."""

import datetime
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


def _not_future(value: datetime.date) -> datetime.date:
    today = datetime.datetime.now(datetime.timezone.utc).date()
    if value > today:
        raise ValueError("date cannot be in the future")
    return value


class TodayOrPastDate(datetime.date):
    """Date that must be today or in the past.

    Unlike ``pydantic.PastDate`` (strictly before today), today is allowed.
    The check is baked into the core schema so it runs for FastAPI ``Form``/
    ``Query`` scalar params, where ``AfterValidator`` metadata is dropped.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            _not_future, handler(datetime.date)
        )
