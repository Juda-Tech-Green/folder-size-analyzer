# Folder Size Analyzer

A high-performance Python desktop application that analyzes your disk space usage. It provides a modern GUI built with `customtkinter` to scan directories up to a specific depth, calculate folder sizes, and display the detailed results along with a bar chart visualization.

## Preview

![Preview](Preview.png)

### Quick Start

[Download FolderSizeAnalyzer.rar](FolderSizeAnalyzer.rar)

**Download &rarr; Extract &rarr; Execute &rarr; Analyze!**

<br>
⚠️ **WARNING: Don't delete the `_internal` folder!** The executable needs it to run correctly.

## Parameterized Depth Analysis

The application must accept a Root Path ($P_0$) and a Depth Key ($k$).

- **Targeting**: The analyzer should identify all directories $D$ located exactly at depth $k$ relative to $P_0$.
- **Aggregation**: For each directory $D_i$ at depth $k$, calculate the total recursive size of all its contents (files and subdirectories):

$$Size(D_i) = \sum \text{size}(f) \text{ for all } f \in \text{descendants}(D_i)$$

## Features

- **Modern UI**: Smooth and beautiful graphical interface using `customtkinter`.
- **Targeted Depth Analysis**: Specify a root path and a target depth ($k$) to find exactly which subfolders are taking up space.
- **High Performance**: Uses `os.scandir()` for fast and efficient directory traversal.
- **Multithreading**: Scanning runs in the background, keeping the UI completely responsive.
- **Visual Dashboard**: Automatically generates a dynamic bar chart for the top 5 heaviest folders using `matplotlib`.
- **Intelligent Formatting**: Dynamically converts bytes into the most readable unit (KB, MB, GB, TB).

## Requirements

- Python 3.8+
- `customtkinter`
- `matplotlib`

## Installation

1. Clone the repository or download the source code.
2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
   Activate it:
   - **Windows**: `.\.venv\Scripts\activate`
   - **Mac/Linux**: `source .venv/bin/activate`

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Click **Browse** to choose a root directory, or paste a path directly.
3. Select the **Depth (k)** using the slider. A depth of 1 means direct subdirectories of the root path.
4. Click **Analyze**. Wait for the progress bar to finish.
5. Review the detailed scrollable list of folders and the Top 5 chart.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
