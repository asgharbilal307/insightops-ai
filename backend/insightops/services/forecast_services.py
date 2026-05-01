import pandas as pd
import numpy as np
from cachetools import TTLCache


# Cache for 5 minutes
forecast_cache = TTLCache(maxsize=10, ttl=300)


def generate_forecast(incidents):

    if "forecast" in forecast_cache:
        return forecast_cache["forecast"]

    if len(incidents) == 0:

        result = {
            "message": "No incidents available"
        }

        forecast_cache["forecast"] = result

        return result

    df = pd.DataFrame([
        {
            "date": incident.created_at.date(),
            "severity": incident.severity
        }
        for incident in incidents
    ])


    daily_counts = df.groupby("date").size()

    values = daily_counts.values

    moving_avg = np.mean(values)

    forecast = [round(moving_avg)] * 7

    result = {
        "historical_counts": daily_counts.to_dict(),
        "forecast_next_7_days": forecast,
        "average_daily_incidents": round(float(moving_avg), 2)
    }

    forecast_cache["forecast"] = result

    return result