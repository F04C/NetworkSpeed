import psutil
import threading
import time
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import mplcursors
import os
import json

class DataUsageMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Usage Monitor")
        self.labels = []

        # Create labels
        for i in range(4):
            label = tk.Label(root, text="")
            label.pack()
            self.labels.append(label)

        # Create a figure for the graphs
        self.figure = Figure(figsize=(8, 3))
        self.ax_upload = self.figure.add_subplot(121)
        self.ax_download = self.figure.add_subplot(122)

        # Create initial data points for the graphs
        self.upload_data = [0]
        self.download_data = [0]

        # Plot the initial data
        self.line_upload, = self.ax_upload.plot(self.upload_data, label='Upload Speed (Mbps)')
        self.line_download, = self.ax_download.plot(self.download_data, label='Download Speed (Mbps)')

        # Set y-axis limits
        self.ax_upload.set_ylim(0, 10)
        self.ax_download.set_ylim(0, 10)

        # Set titles and legends
        self.ax_upload.set_title('Upload Speed (Mbps)')
        self.ax_download.set_title('Download Speed (Mbps)')

        self.ax_upload.legend()
        self.ax_download.legend()

        # Create canvas for the graphs
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill='both')

        # Enable zooming with mplcursors
        mplcursors.cursor(hover=True)

        # Create total data variables
        self.total_upload_data = 0
        self.total_download_data = 0

        self.last_upload_bytes = psutil.net_io_counters().bytes_sent
        self.last_download_bytes = psutil.net_io_counters().bytes_recv

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self.monitor_data_usage)
        self.monitor_thread.daemon = True  # Set the thread as a daemon to automatically exit when the main program exits
        self.monitor_thread.start()

        # Load previous data if available
        self.load_saved_data()

    def load_saved_data(self):
        try:
            with open("data_usage_monitor_data.json", "r") as file:
                data = json.load(file)
                self.total_upload_data = data.get("total_upload_data", 0)
                self.total_download_data = data.get("total_download_data", 0)
        except FileNotFoundError:
            # File not found, ignore and continue with default values
            pass
        except Exception as e:
            print(f"Error loading saved data: {e}")

    def save_data(self):
        try:
            data = {
                "total_upload_data": self.total_upload_data,
                "total_download_data": self.total_download_data,
            }
            with open("data_usage_monitor_data.json", "w") as file:
                json.dump(data, file)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_upload_speed(self):
        try:
            network_stats = psutil.net_io_counters()
            upload_bytes = network_stats.bytes_sent
            upload_speed = (upload_bytes - self.last_upload_bytes) * 8 / (1024 * 1024)  # Convert bytes to megabits
            self.last_upload_bytes = upload_bytes
            return upload_speed
        except Exception as e:
            # Handle exceptions if any
            print(f"Error getting upload speed: {e}")
        return 0.0

    def get_download_speed(self):
        try:
            network_stats = psutil.net_io_counters()
            download_bytes = network_stats.bytes_recv
            download_speed = (download_bytes - self.last_download_bytes) * 8 / (1024 * 1024)  # Convert bytes to megabits
            self.last_download_bytes = download_bytes
            return download_speed
        except Exception as e:
            # Handle exceptions if any
            print(f"Error getting download speed: {e}")
        return 0.0

    def monitor_data_usage(self):
        while True:
            try:
                # Calculate total upload and download speeds in megabits per second
                total_upload_speed = self.get_upload_speed()
                total_download_speed = self.get_download_speed()

                # Accumulate total uploaded and downloaded data
                self.total_upload_data += total_upload_speed * 0.1  # Multiply by the interval (.1 seconds)
                self.total_download_data += total_download_speed * 0.1  # Multiply by the interval (.1 seconds)

                # Update the labels and graphs with the data usage information
                self.update_labels(total_upload_speed, total_download_speed)
                self.update_graphs(total_upload_speed, total_download_speed)

                # Save data
                self.save_data()
            except Exception as e:
                print(f"Error in monitoring data usage: {e}")

            # Wait for a shorter interval (1 second) before the next update
            time.sleep(1)

    def update_labels(self, total_upload_speed, total_download_speed):
        # Update the labels with the data usage information
        for i, label in enumerate(self.labels):
            if i == 0:
                label.config(text=f"Total Upload Data: {self.total_upload_data:.2f} MB")
            elif i == 1:
                label.config(text=f"Total Download Data: {self.total_download_data:.2f} MB")
            elif i == 2:
                label.config(text=f"Upload Speed: {total_upload_speed:.2f} Mbps")
            elif i == 3:
                label.config(text=f"Download Speed: {total_download_speed:.2f} Mbps")

    def update_graphs(self, total_upload_speed, total_download_speed):
        # Update the upload and download speed graphs
        self.upload_data.append(total_upload_speed)
        self.download_data.append(total_download_speed)

        # Limit the number of data points to show (adjust if needed)
        max_data_points = 100

        if len(self.upload_data) > max_data_points:
            self.upload_data = self.upload_data[-max_data_points:]
        if len(self.download_data) > max_data_points:
            self.download_data = self.download_data[-max_data_points:]

        # Update the data in the plots
        self.line_upload.set_xdata(list(range(len(self.upload_data))))
        self.line_upload.set_ydata(self.upload_data)

        self.line_download.set_xdata(list(range(len(self.download_data))))
        self.line_download.set_ydata(self.download_data)

        # Adjust the x-axis limits based on the number of data points
        self.ax_upload.set_xlim(0, len(self.upload_data))
        self.ax_download.set_xlim(0, len(self.download_data))

        # Redraw the canvas
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = DataUsageMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.save_data)  # Save data when the window is closed
    root.mainloop()
