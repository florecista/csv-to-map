from PyQt5.QtWidgets import QDialog, QComboBox, QFormLayout, QPushButton


class ColumnSelectionDialog(QDialog):
    def __init__(self, parent, df):
        super().__init__(parent)
        self.setWindowTitle("Select Columns")
        self.setFixedSize(400, 250)  # Set dialog size to be smaller than main window

        self.df = df
        self.parent = parent  # Store the parent reference (MainWindow)

        self.latitude_combo = QComboBox(self)
        self.longitude_combo = QComboBox(self)
        self.title_combo = QComboBox(self)

        form_layout = QFormLayout(self)
        for col in self.df.columns:
            self.latitude_combo.addItem(col)
            self.longitude_combo.addItem(col)
            self.title_combo.addItem(col)

        # Automatically select 'Latitude', 'Longitude', and 'Title' if found in the headers
        if 'Latitude' in self.df.columns:
            self.latitude_combo.setCurrentText('Latitude')
        if 'Longitude' in self.df.columns:
            self.longitude_combo.setCurrentText('Longitude')
        if 'Title' in self.df.columns:
            self.title_combo.setCurrentText('Title')

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_and_close)

        form_layout.addRow("Latitude:", self.latitude_combo)
        form_layout.addRow("Longitude:", self.longitude_combo)
        form_layout.addRow("Title:", self.title_combo)
        form_layout.addRow(self.save_button)

        self.latitude_combo.currentIndexChanged.connect(self.check_save_button)
        self.longitude_combo.currentIndexChanged.connect(self.check_save_button)
        self.title_combo.currentIndexChanged.connect(self.check_save_button)

    def check_save_button(self):
        """Enable Save button if valid columns are selected."""
        latitude = self.latitude_combo.currentText()
        longitude = self.longitude_combo.currentText()
        title = self.title_combo.currentText()

        if latitude != "Select" and longitude != "Select" and title != "Select":
            if latitude != longitude and latitude != title and longitude != title:
                self.save_button.setEnabled(True)
            else:
                self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(False)

    def save_and_close(self):
        """Capture data from CSV and store geolocations in memory."""
        latitude_col = self.latitude_combo.currentText()
        longitude_col = self.longitude_combo.currentText()
        title_col = self.title_combo.currentText()

        self.parent.save_data(latitude_col, longitude_col, title_col)
        self.accept()  # Close the dialog after saving
