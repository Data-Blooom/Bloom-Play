import subprocess
import re

def get_fps(process_name="game.exe"):
    try:
        cmd = ["libs/PresentMon.exe", "-process_name", process_name]
        output = subprocess.check_output(cmd, text=True, timeout=1)

        match = re.search(r"(\d+)\s+fps", output)
        if match:
            return int(match.group(1))

    except:
        return None