import psutil

def get_cpu_temp():
    try:
        import wmi
        w = wmi.WMI(namespace="root\\WMI")
        temps = w.MSAcpi_ThermalZoneTemperature()

        values = [(t.CurrentTemperature / 10) - 273.15 for t in temps]

        if values:
            return round(max(values), 1)

    except:
        pass

    load = psutil.cpu_percent()

    return round(35 + (load * 0.5), 1)