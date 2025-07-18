# HexaMapper

A simple Hexagon-based map painting program.

## Features

*   **Infinite Canvas**: Pan and zoom across an endless hexagonal map.
*   **Map Painting**: Draw on the map with various colors and adjustable brush sizes to customize your cells.
*   **Save & Load**: Save your map progress to a `.hmap` file and load it later to continue your work.
*   **Export Map**: Export your entire map as a PNG image for sharing or further use.

## Installation and Running

To get HexaMapper up and running on your local machine, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Neonscape/HexaMapper.git
    ```

2.  **Navigate to the project directory**:
    ```bash
    cd HexaMapper
    ```

3.  **Create and activate a Python virtual environment**:
    ```bash
    python -m venv venv
    ```
    *   **On Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    *   **On macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the application**:
    ```bash
    python src/app.py
