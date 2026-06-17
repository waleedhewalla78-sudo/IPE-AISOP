from pydantic import BaseModel


def disaggregate_weekly_forecast(
    weekly_forecast: list[float],
    historical_daily_pattern: list[float],
) -> list[float]:
    if not weekly_forecast or not historical_daily_pattern:
        return []

    pattern = historical_daily_pattern[:7]
    if not pattern:
        return []

    pattern_total = sum(pattern)
    if pattern_total <= 0:
        equal_share = 1.0 / len(pattern)
        pattern = [equal_share] * len(pattern)
    else:
        pattern = [p / pattern_total for p in pattern]

    result = []
    for week_total in weekly_forecast:
        daily = [round(week_total * p, 2) for p in pattern]
        diff = round(week_total - sum(daily), 2)
        if diff != 0:
            daily[0] = round(daily[0] + diff, 2)
        result.extend(daily)

    return result


class SenseRequest(BaseModel):
    weekly_forecasts: list[float]
    historical_daily_pattern: list[float]


class SenseResponse(BaseModel):
    daily_schedule: list[float]
    weeks_processed: int
    days_generated: int
