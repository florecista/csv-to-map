import sys
import pandas as pd
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QAction, QTabWidget, QVBoxLayout, QWidget, \
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QDialog, QFormLayout, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QUrl
from enum import Enum

from column_selection_dialog import ColumnSelectionDialog


class ApplicationDataStatus(Enum):
    Unload = 1
    Load = 2
    Action = 3


class GeoLocation:
    def __init__(self, latitude, longitude, title):
        self.latitude = latitude
        self.longitude = longitude
        self.title = title


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geolocation CSV Reader")
        self.setFixedSize(800, 600)  # Set main window size to 800x600

        # Initialize model for storing geolocations
        self.geolocations = []
        self.status = ApplicationDataStatus.Unload  # Initial state is Unload

        # Initialize combo boxes for column selection (in the main window)
        self.latitude_combo = QComboBox(self)
        self.longitude_combo = QComboBox(self)
        self.title_combo = QComboBox(self)

        # Initialize save_button (enabled by default now)
        self.save_button = QPushButton("Save", self)
        self.save_button.setEnabled(True)  # Always enabled now

        # Create the menu
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")

        self.new_action = QAction("New", self)
        self.new_action.triggered.connect(self.new_data)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open_csv)  # Calls the modified open_csv function
        self.file_menu.addAction(self.open_action)

        self.close_action = QAction("Close", self)
        self.close_action.triggered.connect(self.close_csv)
        self.file_menu.addAction(self.close_action)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Create tabs
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Data tab with table for raw CSV data
        self.data_tab = QWidget(self)
        self.data_layout = QVBoxLayout(self.data_tab)
        self.table_widget = QTableWidget(self)
        self.data_layout.addWidget(self.table_widget)

        # Map tab with OpenStreetMap (initially empty)
        self.map_tab = QWidget(self)
        self.map_layout = QVBoxLayout(self.map_tab)
        self.map_view = QWebEngineView(self)
        self.map_layout.addWidget(self.map_view)

        self.tabs.addTab(self.data_tab, "Data")
        self.tabs.addTab(self.map_tab, "Map")

    def open_csv(self):
        """Handle opening a CSV file and allow the user to select columns."""
        # First, reset the application to avoid issues with old data
        self.new_data()

        # Open file dialog to select a CSV file
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")

        # If a file was selected (file_path is not empty)
        if file_path:
            # Read CSV into pandas dataframe
            self.df = pd.read_csv(file_path)

            # Update table with CSV data
            self.table_widget.setRowCount(self.df.shape[0])
            self.table_widget.setColumnCount(self.df.shape[1])
            self.table_widget.setHorizontalHeaderLabels(self.df.columns)

            for row in range(self.df.shape[0]):
                for col in range(self.df.shape[1]):
                    self.table_widget.setItem(row, col, QTableWidgetItem(str(self.df.iloc[row, col])))

            # Change status to Load and show dialog for column selection
            self.status = ApplicationDataStatus.Load
            self.column_selection_dialog()

    def close_csv(self):
        """Clear model and reset the interface."""
        self.df = None
        self.table_widget.clearContents()
        self.geolocations = []
        self.map_view.setHtml("<h1>Map Placeholder</h1>")  # Clear map content
        self.status = ApplicationDataStatus.Unload  # Set status back to Unload

    def new_data(self):
        """Reset application state and clear data."""
        self.df = None
        self.geolocations = []
        self.table_widget.clearContents()
        self.map_view.setHtml("<h1>Map Placeholder</h1>")  # Clear the map view

        # Reset combo boxes to "Select"
        self.latitude_combo.setCurrentText("Select")
        self.longitude_combo.setCurrentText("Select")
        self.title_combo.setCurrentText("Select")

        # Always enable Save button
        self.save_button.setEnabled(True)

        self.status = ApplicationDataStatus.Unload  # Reset to Unload state

    def column_selection_dialog(self):
        """Show dialog to select latitude, longitude, and title columns."""
        dialog = ColumnSelectionDialog(self, self.df)
        dialog.exec_()

    def save_data(self, latitude_col, longitude_col, title_col):
        """Capture data from CSV and store geolocations in memory."""
        for _, row in self.df.iterrows():
            latitude = row[latitude_col]
            longitude = row[longitude_col]
            title = row[title_col]
            self.geolocations.append(GeoLocation(latitude, longitude, title))

        # Update status to Action, and load map
        self.status = ApplicationDataStatus.Action
        self.load_map()

        # Close the dialog after saving
        self.sender().parent().accept()  # Close only the dialog

    def load_map(self):
        """Load map and display geolocations."""
        if self.status == ApplicationDataStatus.Action:
            # Clear the existing map content to ensure proper reset
            self.map_view.setHtml("")  # Clear the existing map view

            # Calculate the center of all geolocations (average latitude and longitude)
            if self.geolocations:
                avg_lat = sum([loc.latitude for loc in self.geolocations]) / len(self.geolocations)
                avg_lon = sum([loc.longitude for loc in self.geolocations]) / len(self.geolocations)
            else:
                # Default to New York if no geolocations are available
                avg_lat, avg_lon = 40.712776, -74.005974  # New York coordinates

            # Start with OpenStreetMap URL and use Leaflet.js to render markers
            map_html = f"""
            <html>
                <head>
                    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                    <style>
                        #map {{ height: 100%; width: 100%; }}
                    </style>
                </head>
                <body>
                    <div id="map"></div>
                    <script>
                        // Create the map centered on the calculated average location
                        var map = L.map('map').setView([{avg_lat}, {avg_lon}], 13);  // Set center based on geolocations

                        // Add OpenStreetMap tile layer
                        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }}).addTo(map);

                        // Array of geolocations to plot
                        var geolocations = {str([{'latitude': loc.latitude, 'longitude': loc.longitude, 'title': loc.title} for loc in self.geolocations])};  // Placeholder for geolocations data

                        // Add markers for each geolocation
                        geolocations.forEach(function(location) {{
                            var marker = L.marker([location.latitude, location.longitude]).addTo(map);
                            marker.bindPopup(location.title);  // Show title in popup when marker is clicked
                        }});

                        // After adding markers, ensure the map is centered correctly
                        map.setView([{avg_lat}, {avg_lon}], 13);  // Reset the center and zoom level
                    </script>
                </body>
            </html>
            """

            # Load the generated HTML into the map view
            self.map_view.setHtml(map_html)


if __name__ == "__main__":
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        window = MainWindow()
        print("Showing window...")
        window.show()
        sys.exit(app.exec_())  # Ensure the event loop runs
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
