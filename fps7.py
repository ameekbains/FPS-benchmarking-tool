import win32gui
import win32ui
import win32con
import time
import csv
import threading

# Function to enumerate active windows and return a list of window titles
def enumerate_windows():
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows

# Function to allow the user to choose the active window from a list
def choose_active_window(windows):
    print("Active Windows:")
    for i, (hwnd, title) in enumerate(windows):
        print(f"{i+1}. {title}")

    while True:
        try:
            choice = int(input("Enter the number of the window you want to capture FPS from: "))
            if 1 <= choice <= len(windows):
                return windows[choice - 1]
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Function to capture the content of the specified window
def capture_screen(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect

    width = right - left
    height = bottom - top

    desktop_dc = win32gui.GetWindowDC(hwnd)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)

    mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)

    bmp_info = screenshot.GetInfo()
    bmp_str = screenshot.GetBitmapBits(True)

    win32gui.DeleteObject(screenshot.GetHandle())
    mem_dc.DeleteDC()
    img_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, desktop_dc)

    return bmp_str, bmp_info

# Function to calculate the frame rate based on the captured frames
def calculate_frame_rate(start_time, frame_count):
    elapsed_time = time.time() - start_time
    frame_rate = frame_count / elapsed_time if elapsed_time > 0 else 0
    return frame_rate

# Function to write data to a CSV file
def write_to_csv(filename, data):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

# Function to monitor user input to stop the script
def monitor_input():
    global stop_flag
    input("Press Enter to stop the script.\n")
    stop_flag = True

# Main function
def main():
    windows = enumerate_windows()
    if not windows:
        print("No active windows found.")
        return

    hwnd, window_title = choose_active_window(windows)
    print(f"Selected window: {window_title}")

    # Prompt user for filename
    filename = input("Enter the name of the CSV file to save data to: ")

    # Add .csv suffix if not provided
    if not filename.endswith('.csv'):
        filename += '.csv'

    start_time = time.time()
    frame_count = 0
    total_frame_count = 0
    total_elapsed_time = 0
    highest_frame_rate = float('-inf')
    global stop_flag
    stop_flag = False

    # Start a thread to monitor user input for stopping the script
    input_monitor_thread = threading.Thread(target=monitor_input)
    input_monitor_thread.start()

    while not stop_flag:
        if win32gui.IsIconic(hwnd):
            print("Window is minimized. Pausing frame rate calculation.")
            time.sleep(1)  # Pause for 1 second before checking again
            continue

        bmp_str, bmp_info = capture_screen(hwnd)
        frame_count += 1
        total_frame_count += 1

        if time.time() - start_time >= 1:
            frame_rate = calculate_frame_rate(start_time, frame_count)

            if frame_rate > highest_frame_rate:
                highest_frame_rate = frame_rate

            total_elapsed_time += time.time() - start_time
            average_frame_rate = total_frame_count / total_elapsed_time if total_elapsed_time > 0 else 0

            print("Frame Rate:", frame_rate)
            print("Highest Frame Rate:", highest_frame_rate)
            print("Average Frame Rate:", average_frame_rate)

            # Write data to CSV
            write_to_csv(filename, [time.time(), frame_rate, highest_frame_rate, average_frame_rate])

            start_time = time.time()
            frame_count = 0

    input_monitor_thread.join()

if __name__ == "__main__":
    main()
