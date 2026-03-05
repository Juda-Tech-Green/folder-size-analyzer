import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("TkAgg")

def format_size(size_in_bytes: int) -> str:
    """Dynamic unit conversion (B, KB, MB, GB, TB) using a logarithmic scale for readability."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

class DirectoryScanner:
    """Scanner Engine running on a separate thread using os.scandir for high-performance."""
    def __init__(self, root_path: str, target_depth: int):
        self.root_path = root_path
        self.target_depth = target_depth
        self.results = []
        self._cancel_flag = False

    def get_recursive_size(self, path: str) -> int:
        """Calculate the total recursive size of all contents (files and subdirectories)."""
        total_size = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._cancel_flag:
                        break
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total_size += self.get_recursive_size(entry.path)
                    except (PermissionError, FileNotFoundError, OSError):
                        pass # Ignore inaccessible files/folders
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return total_size

    def scan_target_depth(self, current_path: str, current_depth: int):
        """Finds directories exactly at the target_depth, calculating their recursive sizes."""
        if self._cancel_flag:
            return

        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if self._cancel_flag:
                        break
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if current_depth == self.target_depth:
                                size = self.get_recursive_size(entry.path)
                                self.results.append({'path': entry.path, 'size': size})
                            elif current_depth < self.target_depth:
                                self.scan_target_depth(entry.path, current_depth + 1)
                    except (PermissionError, FileNotFoundError, OSError):
                        pass
        except (PermissionError, FileNotFoundError, OSError):
            pass
    
    def run_scan(self):
        self.results = []
        # Target depth is relative to root path. Depth 1 means direct subdirectories.
        if self.target_depth == 0:
            size = self.get_recursive_size(self.root_path)
            self.results.append({'path': self.root_path, 'size': size})
        else:
            self.scan_target_depth(self.root_path, 1)

    def cancel(self):
        self._cancel_flag = True


class FolderSizeAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Folder Size Analyzer")
        self.geometry("900x750")
        
        # Grid Configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_input_section()
        self._build_dashboard_section()
        self._build_results_section()

        self.scanner = None
        self.scan_thread = None

    def _build_input_section(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        # Root Path
        ctk.CTkLabel(input_frame, text="Root Path:").grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.path_entry = ctk.CTkEntry(input_frame, placeholder_text="Select or type a directory path...")
        self.path_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse", width=80, command=self._browse_folder).grid(row=0, column=2, padx=(5, 10), pady=10)

        # Depth Selector (Slider + Label)
        ctk.CTkLabel(input_frame, text="Depth (k):").grid(row=1, column=0, padx=(10, 5), pady=10, sticky="w")
        
        depth_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        depth_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        depth_frame.grid_columnconfigure(0, weight=1)

        self.depth_slider = ctk.CTkSlider(depth_frame, from_=1, to=10, number_of_steps=9, command=self._update_depth_label)
        self.depth_slider.set(1)
        self.depth_slider.grid(row=0, column=0, sticky="ew")
        
        self.depth_label = ctk.CTkLabel(depth_frame, text="1", width=30)
        self.depth_label.grid(row=0, column=1, padx=(10, 0))

        # Analyze & Progress
        self.analyze_button = ctk.CTkButton(input_frame, text="Analyze", command=self._start_analysis)
        self.analyze_button.grid(row=2, column=0, columnspan=3, padx=10, pady=(10, 20), sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(input_frame, mode="indeterminate")
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0) # Hide visually when not active
        self.progress_bar.grid_remove()

    def _build_dashboard_section(self):
        self.dashboard_frame = ctk.CTkFrame(self)
        self.dashboard_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_rowconfigure(0, weight=1)
        
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.dashboard_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.ax.set_title("Top 5 Heaviest Folders")
        self.ax.set_ylabel("Size")
        self.figure.tight_layout()

    def _build_results_section(self):
        results_container = ctk.CTkFrame(self)
        results_container.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        results_container.grid_columnconfigure(0, weight=1)
        results_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(results_container, text="Detailed Results", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(results_container, label_text="")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.result_labels = []

    def _browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder_path)

    def _update_depth_label(self, value):
        self.depth_label.configure(text=str(int(value)))

    def _start_analysis(self):
        root_path = self.path_entry.get().strip()
        if not root_path or not os.path.exists(root_path):
            messagebox.showerror("Error", "Please provide a valid root path.")
            return

        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showinfo("Wait", "A scan is already in progress.")
            return

        target_depth = int(self.depth_slider.get())

        # Reset UI
        self._clear_results()
        self.analyze_button.configure(state="disabled", text="Analyzing...")
        self.progress_bar.grid()
        self.progress_bar.start()

        self.scanner = DirectoryScanner(root_path, target_depth)
        self.scan_thread = threading.Thread(target=self._run_scan_thread, daemon=True)
        self.scan_thread.start()
        self.after(100, self._check_scan_thread)

    def _run_scan_thread(self):
        self.scanner.run_scan()

    def _check_scan_thread(self):
        if self.scan_thread.is_alive():
            self.after(100, self._check_scan_thread)
        else:
            self._analysis_complete()

    def _clear_results(self):
        for widget in self.result_labels:
            widget.destroy()
        self.result_labels.clear()
        
        self.ax.clear()
        self.ax.set_title("Top 5 Heaviest Folders")
        self.ax.set_ylabel("Size")
        self.figure.tight_layout()
        self.canvas.draw()

    def _analysis_complete(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.analyze_button.configure(state="normal", text="Analyze")

        results = self.scanner.results
        if not results:
            messagebox.showinfo("Result", "No directories found at the specified depth.")
            return

        # Sort results by size descending
        results.sort(key=lambda x: x['size'], reverse=True)

        self._update_chart(results[:5])
        self._update_scrollable_list(results)

    def _update_chart(self, top_results):
        self.ax.clear()
        
        names = [os.path.basename(r['path']) or r['path'] for r in top_results]
        sizes = [r['size'] for r in top_results]

        # Use bytes natively for proportional bar chart, then format text
        bars = self.ax.bar(names, sizes, color='skyblue')
        
        self.ax.set_title("Top 5 Heaviest Folders")
        self.ax.set_ylabel("Size")
        
        # Add value labels on top of bars
        for bar, size in zip(bars, sizes):
            yval = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2.0, yval, format_size(size), va='bottom', ha='center', fontsize=8, rotation=15)

        # Rotate x labels if long
        self.ax.set_xticks(range(len(names)))
        self.ax.set_xticklabels(names, rotation=25, ha="right", fontsize=9)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def _update_scrollable_list(self, results):
        for i, res in enumerate(results):
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color=("gray85", "gray20"))
            frame.grid(row=i, column=0, sticky="ew", pady=2, padx=5)
            frame.grid_columnconfigure(0, weight=1)

            path_label = ctk.CTkLabel(frame, text=res['path'], anchor="w", justify="left")
            path_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            size_label = ctk.CTkLabel(frame, text=format_size(res['size']), font=ctk.CTkFont(weight="bold"))
            size_label.grid(row=0, column=1, padx=10, pady=5)

            self.result_labels.append(frame)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = FolderSizeAnalyzerApp()
    app.mainloop()
