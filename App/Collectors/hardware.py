import platform
import psutil
import subprocess
import re
import pythoncom

try:
    import GPUtil
except Exception:
    GPUtil = None

try:
    import wmi
except Exception:
    wmi = None


def get_hardware_info():
    """Get detailed hardware information with all fields for frontend"""
    
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
    
    info = {
        "cpu": {},
        "gpu": {},
        "ram": {},
        "disk": [],
        "system": {},
        "bios": {},
        "total_storage": "Unknown"
    }

    try:
        cpu_name = platform.processor()
        cores = psutil.cpu_count(logical=False)
        threads = psutil.cpu_count(logical=True)
        max_clock = 0
        cpu_brand = "Unknown"
        cache = "Unknown"
        architecture = platform.machine()

        if wmi:
            try:
                w = wmi.WMI()
                cpu = w.Win32_Processor()[0]
                
                cpu_name = cpu.Name.strip()
                max_clock = getattr(cpu, "MaxClockSpeed", 0)
                
                if "Intel" in cpu_name:
                    cpu_brand = "Intel"
                elif "AMD" in cpu_name:
                    cpu_brand = "AMD"
                else:
                    cpu_brand = "Unknown"
                
                # Get cache info
                l2 = getattr(cpu, "L2CacheSize", 0)
                l3 = getattr(cpu, "L3CacheSize", 0)
                if l2 or l3:
                    cache_parts = []
                    if l2:
                        cache_parts.append(f"{l2}KB L2")
                    if l3:
                        cache_parts.append(f"{l3}KB L3")
                    cache = ", ".join(cache_parts)
                
                architecture = platform.machine()
                
            except Exception:
                pass

        clock_ghz = round(max_clock / 1000, 2) if max_clock else 0

        info["cpu"] = {
            "name": cpu_name or "Unknown",
            "brand": cpu_brand,
            "cores": cores or 0,
            "threads": threads or 0,
            "base_clock": clock_ghz,
            "cache": cache,
            "architecture": architecture
        }

    except Exception as e:
        print(f"CPU error: {e}")
        info["cpu"] = {
            "name": "Unknown",
            "brand": "Unknown",
            "cores": 0,
            "threads": 0,
            "base_clock": 0,
            "cache": "Unknown",
            "architecture": "Unknown"
        }

    try:
        gpu_name = "Unknown GPU"
        gpu_memory = "Unknown"
        gpu_vendor = "Unknown"
        gpu_driver = "Unknown"

        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_name = gpu.name or "Unknown"
                    gpu_memory = f"{round(gpu.memoryTotal)} MB" if gpu.memoryTotal else "Unknown"
                    
                    if "NVIDIA" in gpu_name:
                        gpu_vendor = "NVIDIA"
                    elif "AMD" in gpu_name or "Radeon" in gpu_name:
                        gpu_vendor = "AMD"
                    elif "Intel" in gpu_name:
                        gpu_vendor = "Intel"
                    else:
                        gpu_vendor = "Unknown"
                    
                    gpu_driver = gpu.driver or "Unknown"
            except Exception:
                pass

        # If GPUtil failed, try WMI
        if wmi and (gpu_name == "Unknown GPU" or not gpu_name):
            try:
                w = wmi.WMI()
                controllers = w.Win32_VideoController()
                
                for controller in controllers:
                    name = controller.Name.strip() if controller.Name else ""
                    if name and "Microsoft" not in name and "Basic" not in name:
                        gpu_name = name
                        
                        if "NVIDIA" in gpu_name:
                            gpu_vendor = "NVIDIA"
                        elif "AMD" in gpu_name or "Radeon" in gpu_name:
                            gpu_vendor = "AMD"
                        elif "Intel" in gpu_name:
                            gpu_vendor = "Intel"
                        else:
                            gpu_vendor = "Unknown"
                        
                        ram = getattr(controller, "AdapterRAM", 0)
                        if ram:
                            gpu_memory = f"{round(ram / (1024**3), 1)} GB"
                        
                        driver = getattr(controller, "DriverVersion", "")
                        if driver:
                            gpu_driver = driver
                        
                        break
            except Exception:
                pass

        info["gpu"] = {
            "name": gpu_name,
            "vendor": gpu_vendor,
            "memory": gpu_memory,
            "driver": gpu_driver
        }

    except Exception as e:
        print(f"GPU error: {e}")
        info["gpu"] = {
            "name": "Unknown",
            "vendor": "Unknown",
            "memory": "Unknown",
            "driver": "Unknown"
        }

    try:
        total_ram = round(psutil.virtual_memory().total / (1024**3), 1)
        ram_type = "Unknown"
        ram_speed = 0
        ram_brand = "Unknown"
        ram_slots = 0
        ram_form_factor = "Unknown"

        if wmi:
            try:
                w = wmi.WMI()
                memories = w.Win32_PhysicalMemory()

                if memories:
                    ram_slots = len(memories)
                    first = memories[0]
                    
                    ram_brand = getattr(first, "Manufacturer", "") or "Unknown"
                    
                    mem_type = getattr(first, "SMBIOSMemoryType", None)
                    type_map = {
                        20: "DDR",
                        21: "DDR2",
                        24: "DDR3",
                        26: "DDR4",
                        34: "DDR5"
                    }
                    ram_type = type_map.get(mem_type, "Unknown")
                    
                    mem_speed = getattr(first, "Speed", None)
                    if mem_speed:
                        ram_speed = mem_speed
                    
                    form_factor = getattr(first, "FormFactor", None)
                    if form_factor == 8:
                        ram_form_factor = "DIMM"
                    elif form_factor == 12:
                        ram_form_factor = "SODIMM"
                    elif form_factor:
                        ram_form_factor = str(form_factor)
                    else:
                        ram_form_factor = "Unknown"

            except Exception as e:
                print(f"WMI RAM error: {e}")

        info["ram"] = {
            "size": f"{total_ram} GB",
            "type": ram_type,
            "speed": ram_speed,
            "brand": ram_brand,
            "form_factor": ram_form_factor,
            "slots": ram_slots
        }

    except Exception as e:
        print(f"RAM error: {e}")
        info["ram"] = {
            "size": "Unknown",
            "type": "Unknown",
            "speed": 0,
            "brand": "Unknown",
            "form_factor": "Unknown",
            "slots": 0
        }

    try:
        total_storage = 0
        seen = set()

        for part in psutil.disk_partitions():
            try:
                if "cdrom" in part.opts.lower() or part.device in seen:
                    continue

                seen.add(part.device)
                usage = psutil.disk_usage(part.mountpoint)

                total_gb = round(usage.total / (1024**3))
                total_storage += total_gb

                disk_type = "Unknown"
                
                if wmi:
                    try:
                        w = wmi.WMI()
                        disk_drives = w.Win32_DiskDrive()
                        for disk in disk_drives:
                            disk_size_gb = round(int(disk.Size) / (1024**3)) if disk.Size else 0
                            if disk_size_gb == total_gb or disk_size_gb > 0:
                                if disk.Model and "SSD" in disk.Model:
                                    disk_type = "SSD"
                                    break
                                elif disk.MediaType and "SSD" in disk.MediaType:
                                    disk_type = "SSD"
                                    break
                                elif disk.Model and "NVMe" in disk.Model:
                                    disk_type = "SSD"
                                    break
                                elif disk_type != "SSD":
                                    disk_type = "HDD"
                    except Exception:
                        pass

                if disk_type == "Unknown":
                    if "ssd" in part.fstype.lower() or "nvme" in part.fstype.lower():
                        disk_type = "SSD"
                    else:
                        disk_type = "HDD"

                info["disk"].append({
                    "name": part.device,
                    "type": disk_type,
                    "total": total_gb,
                    "used": round(usage.used / (1024**3)),
                    "free": round(usage.free / (1024**3)),
                    "percent": round(usage.percent)
                })

            except Exception as e:
                print(f"Disk partition error: {e}")

        info["total_storage"] = f"{round(total_storage)} GB"

    except Exception as e:
        print(f"Storage error: {e}")
        info["disk"] = []

    try:
        kernel = ""
        try:
            if platform.system() == "Windows":
                kernel = platform.version() or ""
            else:
                kernel = platform.release() or ""
        except:
            pass

        info["system"] = {
            "os": f"{platform.system()} {platform.release()}",
            "hostname": platform.node(),
            "arch": platform.machine(),
            "kernel": kernel or "Unknown"
        }

    except Exception as e:
        print(f"System error: {e}")
        info["system"] = {
            "os": "Unknown",
            "hostname": "Unknown",
            "arch": "Unknown",
            "kernel": "Unknown"
        }

    try:
        if wmi:
            w = wmi.WMI()
            board = w.Win32_BaseBoard()[0]
            bios = w.Win32_BIOS()[0]

            info["bios"] = {
                "board": f"{board.Manufacturer} {board.Product}",
                "bios": bios.SMBIOSBIOSVersion,
                "serial": getattr(board, "SerialNumber", "")
            }

    except Exception as e:
        print(f"BIOS error: {e}")
        info["bios"] = {
            "board": "Unknown",
            "bios": "Unknown",
            "serial": "Unknown"
        }

    return info