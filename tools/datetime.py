from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from core.tool import Tool, ToolResult


class DateInput(BaseModel):
    pass


class DateTool(Tool[DateInput]):
    name = "current_date"
    description = (
        "Get the current date and calendar information."
    )
    input_model = DateInput

    def execute(self, input: DateInput) -> ToolResult:
        now = datetime.now().astimezone()
        date = now.date()

        return ToolResult(
            success=True,
            output={
                "date": date.isoformat(),
                "day": date.day,
                "month": date.month,
                "year": date.year,
                "day_name": date.strftime("%A"),
                "month_name": date.strftime("%B"),
                "day_of_year": date.timetuple().tm_yday,
                "week_number": date.isocalendar().week,
                "is_leap_year": (
                    date.year % 4 == 0
                    and (
                        date.year % 100 != 0
                        or date.year % 400 == 0
                    )
                ),
            },
        )