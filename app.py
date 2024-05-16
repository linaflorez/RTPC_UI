from PyQt5 import QtCore, QtGui, QtWidgets
from ui import Ui_MainWindow
import pandas as pd

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initialize_dropdowns()  # Initialize dropdowns when window is created
        self.pushButton_4.clicked.connect(self.get_materials_used)  # Connect pushButton_4 to make composition code

    
    ##### SAVE

    def initialize_dropdowns(self):
        """
        Initializes the dropdown menus in the UI.
        
        Reads a CSV file containing material data, populates the fiber category dropdown menu,
        and connects signals to slots for the fiber category, resin category, and description dropdown menus.
        """
        # Read CSV file
        self.df = pd.read_csv('./materialsdata.csv')

        # Get unique fiber categories
        fiber_categories = sorted(self.df['Fiber Category'].astype(str).unique())
        self.resin_combos = []  # Initialize resin_combos as an empty list


        # Add combo boxes to the tableWidget_8
        for row in range(6):  # Assuming you have 6 rows
            fiber_combo = QtWidgets.QComboBox()
            fiber_combo.addItems(fiber_categories)
            self.tableWidget_8.setCellWidget(row, 0, fiber_combo)

            # Connect signal to slot for fiber combo box
            fiber_combo.currentIndexChanged.connect(self.pick_fiber)

        # No need to connect signals for resin and description since they are dependent

    def pick_fiber(self):
        fiber_combo = self.sender()  # Get the combo box that sent the signal
        fiber_selection = fiber_combo.currentText()

        # Find the corresponding row
        for row in range(self.tableWidget_8.rowCount()):
            if self.tableWidget_8.cellWidget(row, 0) == fiber_combo:
                row_index = row
                break

        # Clear previous resin combo box and items
        resin_combo = self.tableWidget_8.cellWidget(row_index, 1)
        if resin_combo:
            resin_combo.clear()

        # Filter dataframe based on fiber selection
        filtered_df = self.df[self.df['Fiber Category'] == fiber_selection]

        # Get unique resin categories for the selected fiber
        resin_categories = sorted(filtered_df['Resin Category'].astype(str).unique())

        # Create a new resin combo box if it doesn't exist for this row
        if not resin_combo:
            resin_combo = QtWidgets.QComboBox()
            resin_combo.currentIndexChanged.connect(self.pick_resin)
            self.tableWidget_8.setCellWidget(row_index, 1, resin_combo)

        # Add items to the resin combo box
        resin_combo.addItems(resin_categories)

    def pick_resin(self):
        resin_combo = self.sender()  # Get the combo box that sent the signal
        resin_selection = resin_combo.currentText()

        # Find the corresponding row
        for row in range(self.tableWidget_8.rowCount()):
            if self.tableWidget_8.cellWidget(row, 1) == resin_combo:
                row_index = row
                break

        # Clear previous description combo box and items
        description_combo = self.tableWidget_8.cellWidget(row_index, 2)
        if description_combo:
            description_combo.clear()

        fiber_combo = self.tableWidget_8.cellWidget(row_index, 0)
        fiber_selection = fiber_combo.currentText()

        # Filter dataframe based on fiber and resin selection
        filtered_df = self.df[(self.df['Fiber Category'] == fiber_selection) & 
                              (self.df['Resin Category'] == resin_selection)]

        # Get unique descriptions for the selected fiber and resin
        descriptions = sorted(filtered_df['PN+Description Concatenation'].astype(str).unique())

        # Create a new description combo box if it doesn't exist for this row
        if not description_combo:
            description_combo = QtWidgets.QComboBox()
            self.tableWidget_8.setCellWidget(row_index, 2, description_combo)

        # Add items to the description combo box
        description_combo.addItems(descriptions)

    ##### SAVE

    def get_materials_used(self):
        target_range = self.scrollArea_2.tableWidget.item(2, 0)  # Third row, first column
        selected_material = []
        selected_pnconcatdescription = []
        for row in range(6):
            fiber_combo = self.tableWidget_8.cellWidget(row, 0)
            resin_combo = self.tableWidget_8.cellWidget(row, 1)
            description_combo = self.tableWidget_8.cellWidget(row, 2)
            if fiber_combo and resin_combo and description_combo:
                selected_material.append(fiber_combo.currentText())
                selected_pnconcatdescription.append(description_combo.currentText())

        used_materials = []
        materials_breakdown = []
        for i, pnconcatdescription in enumerate(selected_pnconcatdescription):
            for index, row in self.df.iterrows():
                if row['PN+Description Concatenation'] == pnconcatdescription:
                    material = selected_material[i]
                    used_materials.append(material)
                    materials_breakdown.append(f"{material}:{row['PN+Description Concatenation']}")

        target_range.setText(','.join(materials_breakdown))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()
    MainWindow.show()
    sys.exit(app.exec_())
