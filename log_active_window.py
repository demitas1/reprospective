import subprocess
import time
from datetime import datetime

def get_active_window_info():
    try:
        active_window_id = subprocess.check_output(
            ["xdotool", "getactivewindow"],
            universal_newlines=True
        ).strip()

        xprop_output = subprocess.check_output(
            ["xprop", "-id", active_window_id, "WM_NAME", "WM_CLASS"],
            universal_newlines=True
        ).strip()

        title = ""
        app_name = ""
        for line in xprop_output.split("\n"):
            if "WM_NAME" in line:
                title = line.split("=", 1)[-1].strip().strip('"')
            elif "WM_CLASS" in line:
                app_name = line.split("=", 1)[-1].strip().split(",")[-1].strip().strip('"')

        return title, app_name
    except subprocess.CalledProcessError as e:
        return f"Error: {e}", ""

def write_to_file(data):
    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"log/active_window_{current_date}.txt"

    with open(filename, "a") as f:
        f.write(data + "\n")

def main():
    try:
        while True:
            epoch_time = int(time.time())
            title, app_name = get_active_window_info()

            # Escape commas in app_name and title
            app_name = app_name.replace(",", "\\,")
            title = title.replace(",", "\\,")

            output_line = f'{epoch_time},"{app_name}","{title}"'
            print(output_line)
            write_to_file(output_line)

            time.sleep(10)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")

if __name__ == "__main__":
    main()
