import psutil

def get_battery_stats():

    battery = psutil.sensors_battery()

    if battery is None:
        return {
            "percent": "N/A",
            "health": "Desktop PC"
        }

    percent = round(battery.percent)

    if percent >= 80:
        health = "Excellent"

    elif percent >= 60:
        health = "Good"

    elif percent >= 40:
        health = "Fair"

    else:
        health = "Poor"

    return {
        "percent": percent,
        "health": health
    }