from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QTableWidgetItem,QLineEdit,QComboBox,QApplication,QMainWindow,QPushButton,QTableWidget,QVBoxLayout,QWidget,)
from ui import Ui_MainWindow
from generate_production_run import calculations as calculations
import pandas as pd
import math
from math import ceil, isnan


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.setupUi(self)

        #### FUNCTIONALITY ASSOCIATED WITH PROTOTYPING TAB ####
        ### --> STACKUP TAB
        self.materialCSV_here.cursorPositionChanged.connect(self.select_material_csv)
        self.initialize_materials_dropdowns("")
        self.compositionCode.clicked.connect(self.get_materials_used)
        self.clearMaterials.clicked.connect(self.reset_materialsTable)
        self.materialsAddRow.clicked.connect(self.add_row_materialsTable)
        self.materialsRemoveRow.clicked.connect(self.remove_row_materialsTable)

        ### --> GENERATOR TAB
        item = QTableWidgetItem()
        self.stackupInfoTable.setItem(2, 0, item)
        self.setup_stackupBreakdown()
        self.clearStackup.clicked.connect(self.clear_stackupBreakdown_columns)
        self.sendToCustomerInfoSheet.clicked.connect(
            self.on_sendtoCustomerInfoSheet_clicked
        )

        #### FUNCTIONALITY ASSOCIATED WITH CUSTOMER INFORMATION TAB ####
        self.customerCSV_here.cursorPositionChanged.connect(self.select_customer_csv)
        self.initialize_customer_dropdowns("")
        self.searchClients.clicked.connect(self.find_Clients)
        self.createNewProduct.clicked.connect(self.add_New_Product)
        self.customerAddRow.clicked.connect(self.add_row_customerTable)
        self.customerRemoveRow.clicked.connect(self.remove_row_customerTable)
        self.generateRun.clicked.connect(self.populate_Production_Sheets)
        self.productionInfo.cellChanged.connect(self.calculate_dimensions)    
        self.pushButton_6.clicked.connect (self.save_table_to_csv)    


    ################################################################################
    ################################################################################

    #### FUNCTIONALITY ASSOCIATED WITH PROTOTYPING TAB ####
    ### --> STACKUP TAB

    def select_material_csv(self):
            """
            Slot function that is called when the materialCSV_here QLineEdit is clicked.
            Opens a file dialog that allows the user to select a file from their repositories.
            """
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select Material CSV", "", "CSV Files (*.csv)", options=options
            )
            if file_name:
                self.materialCSV_here.setText(file_name)
                self.initialize_materials_dropdowns(file_name)


    def initialize_materials_dropdowns(self, file_name):
        # Define expected columns
        column_names = [
            "Description", "Previously Called", "TYPE", "Fiber Category", "Resin Category", "Sequence Assist",
            "Auto-Sequence", "PN Concatenation", "PN+Description Concatenation", "UOM", "Width (in)", "Length (in)",
            "Arial Weight (gsm)", "Thickness (mm)", "$/Kg", "Heat capacity (J/C)", "Suggested Process Temp (deg F)",
            "Manufacturer", "Manufacturer PN (link to datasheet)", "Misc. Notes", "Weld Notes:", "Cut Notes:", "Inventory Locations:"
        ]

        try:
            # Try to read the CSV file
            self.df = pd.read_csv(file_name)

            # Correct any known typos in column names
            if 'Heat capcity (J/C)' in self.df.columns:
                self.df = self.df.rename(columns={'Heat capcity (J/C)': 'Heat capacity (J/C)'})

            # Check for missing columns
            missing_columns = [column for column in column_names if column not in self.df.columns]

            if missing_columns:
                raise ValueError(f"CSV file is missing required headers: {', '.join(missing_columns)}")

        except (FileNotFoundError, ValueError, KeyError, pd.errors.ParserError) as e:
            # If there's an error (file not found, missing columns, key error, or parsing error), create a default DataFrame
            print(f"Error reading CSV file: {e}. Using default column names.")
            self.df = pd.DataFrame(columns=column_names)

        # Ensure the DataFrame has the required columns, even if the CSV file had extra columns or missing some
        for column in column_names:
            if column not in self.df.columns:
                self.df[column] = None

        # Get unique fiber categories, default to an empty list if the column is missing
        fiber_categories = sorted(self.df["Fiber Category"].dropna().astype(str).unique()) if "Fiber Category" in self.df.columns else []
        self.resin_combos = []  # Initialize resin_combos as an empty list

        # Add combo boxes to the materialsTable
        for row in range(100):  # Assuming you have 6 rows
            fiber_combo = QtWidgets.QComboBox()
            fiber_combo.addItems(fiber_categories)
            self.materialsTable.setCellWidget(row, 1, fiber_combo)

            # Connect signal to slot for fiber combo box
            fiber_combo.currentIndexChanged.connect(self.pick_fiber)


    def pick_fiber(self):
        fiber_combo = self.sender()  # Get the combo box that sent the signal
        fiber_selection = fiber_combo.currentText()

        # Find the corresponding row
        for row in range(self.materialsTable.rowCount()):
            if self.materialsTable.cellWidget(row, 1) == fiber_combo:
                row_index = row
                break

        # Clear previous resin combo box and items
        resin_combo = self.materialsTable.cellWidget(row_index, 2)
        if resin_combo:
            resin_combo.clear()

        # Filter dataframe based on fiber selection
        filtered_df = self.df[self.df["Fiber Category"] == fiber_selection]

        # Get unique resin categories for the selected fiber
        resin_categories = sorted(filtered_df["Resin Category"].astype(str).unique())
        print("Filtered Resin Categories:", resin_categories)

        # Create a new resin combo box if it doesn't exist for this row
        if not resin_combo:
            resin_combo = QtWidgets.QComboBox()
            resin_combo.currentIndexChanged.connect(self.pick_resin)
            self.materialsTable.setCellWidget(row_index, 2, resin_combo)

        # Add items to the resin combo box
        resin_combo.addItems(resin_categories)

    def pick_resin(self):
        resin_combo = self.sender()  # Get the combo box that sent the signal
        resin_selection = resin_combo.currentText()
        print(f"Selected Resin: {resin_selection}")

        # Find the corresponding row
        for row in range(self.materialsTable.rowCount()):
            if self.materialsTable.cellWidget(row, 2) == resin_combo:
                row_index = row
                break

        # Clear previous description combo box and items
        description_combo = self.materialsTable.cellWidget(row_index, 3)
        if description_combo:
            description_combo.clear()

        fiber_combo = self.materialsTable.cellWidget(row_index, 1)
        fiber_selection = fiber_combo.currentText()

        # Filter dataframe based on fiber and resin selection
        filtered_df = self.df[
            (self.df["Fiber Category"] == fiber_selection)
            & (self.df["Resin Category"] == resin_selection)
        ]

        

        # Get unique descriptions for the selected fiber and resin
        descriptions = sorted(
            filtered_df["PN+Description Concatenation"].astype(str).unique()
        )

        print("Filtered Descriptions:", descriptions)

        # Create a new description combo box if it doesn't exist for this row
        if not description_combo:
            description_combo = QtWidgets.QComboBox()
            description_combo.currentIndexChanged.connect(self.pick_description)
            self.materialsTable.setCellWidget(row_index, 3, description_combo)

        print("HELLO!")
        # Add items to the description combo box
        description_combo.addItems(descriptions)

    

    def pick_description(self):
        description_combo = self.sender()  # Get the combo box that sent the signal
        description_selection = description_combo.currentText()
        print(f"Selected Description: {description_selection}")

        print("HERE1")

        # Find the corresponding row
        for row in range(self.materialsTable.rowCount()):
            if self.materialsTable.cellWidget(row, 3) == description_combo:
                row_index = row
                break

        # Clear previous location combo box and items
        location_combo = self.materialsTable.cellWidget(row_index, 4)
        if location_combo:
            location_combo.clear()

        print("HERE2")
        # Filter dataframe based on description selection
        filtered_df = self.df[
            (self.df["PN+Description Concatenation"] == description_selection)
        ]

        print("Filtered DataFrame for Locations:", filtered_df)
        
        # Combine location values into a single column
        location_col_index = self.df.columns.get_loc("Inventory Locations:")
        for i, row in filtered_df.iterrows():
            # Get the values from the "Location" column to the last column
            location_values = row.iloc[location_col_index:].astype(str)
            print(location_values)
            # Combine the values into a single comma-separated string
            combined_location = ",".join(location_values)
            # Update the "Location" column with the combined value
            filtered_df.at[i, "Inventory Locations:"] = combined_location

        # Get unique locations for the selected description
        locations = sorted(
            filtered_df["Inventory Locations:"].astype(str).unique()
        )

        print("Filtered Locations:", locations)

        # Create a new location combo box if it doesn't exist for this row
        if not location_combo:
            location_combo = QtWidgets.QComboBox()
            self.materialsTable.setCellWidget(row_index, 4, location_combo)

        # Add items to the location combo box
        location_combo.addItems(locations)



    def get_materials_used(self):
        target_range = self.stackupInfoTable.item(2, 0)  # Third row, first column
        if target_range is None:
            print("Target Range is None")  # Debugging statement
            return

        selected_material = []
        selected_pnconcatdescription = []
        for row in range(100):
            item = self.materialsTable.item(row, 0)
            if item is not None:
                material = item.text()
                selected_material.append(material)
                description_combo = self.materialsTable.cellWidget(row, 3)
                if description_combo:  # Check if description_combo is not None
                    selected_pnconcatdescription.append(description_combo.currentText())

        used_materials = []
        materials_breakdown = []

        for i, pnconcatdescription in enumerate(selected_pnconcatdescription):
            matching_row = self.df[
                self.df["PN+Description Concatenation"] == pnconcatdescription
            ]
            if not matching_row.empty:
                pn_concatenation = matching_row.iloc[0]["PN Concatenation"]
                material = selected_material[i]
                used_materials.append(material)
                materials_breakdown.append(f"{material}:{pn_concatenation}")

        target_range.setText(",".join(materials_breakdown))

    def get_alphabet_letter(self, index):
        """Determines the letter going into the material column of the stackup tab. Relevant to generating the composition code.
        This function converts an integer index to a string of alphabet letters.
            For example:
            0 -> "A", 1 -> "B" and so on.
        """
        index += 1
        result = ""

        while index > 0:
            index -= 1
            letter = chr(index % 26 + 65)
            result = letter + result
            index //= 26

        return result
    
    def reset_materialsTable(self):
        """Clears all values and resets the materialsTable to its initial state except the first column."""
        for row in range(self.materialsTable.rowCount()):
            self.remove_row_materialsTable()
        
        # Reinitialize the dropdowns
        self.initialize_materials_dropdowns(self.materialCSV_here.text())
    
    def add_dropdowns_to_row(self, row):
        fiber_combo = QtWidgets.QComboBox()
        fiber_combo.addItems(sorted(self.df["Fiber Category"].astype(str) .unique ()))
        self.materialsTable.setCellWidget(row, 1, fiber_combo)
        fiber_combo.currentIndexChanged.connect (self.pick_fiber)

    def add_row_materialsTable(self):
        row_position = self.materialsTable.rowCount()
        self.materialsTable.insertRow(row_position)
        self.add_dropdowns_to_row(row_position)

        # Populate the first column with the corresponding alphabet letter
        alphabet_letter = self.get_alphabet_letter(row_position)
        item = QTableWidgetItem(alphabet_letter)
        item.setFlags(
            item.flags() & ~QtCore.Qt.ItemIsEditable
        )  # Make the item uneditable
        item.setTextAlignment(QtCore.Qt.AlignCenter)  # Align text to the center
        self.materialsTable.setItem(row_position, 0, item)

    def remove_row_materialsTable(self):
        current_row = self.materialsTable.currentRow()
        if current_row != -1:
            self.materialsTable.removeRow(current_row)
            # Re-populate the first column to maintain consecutive letters
            for row in range(self.materialsTable.rowCount()):
                alphabet_letter = self.get_alphabet_letter(row)
                item = QTableWidgetItem(alphabet_letter)
                item.setFlags(
                    item.flags() & ~QtCore.Qt.ItemIsEditable
                )  # Make the item uneditable
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # Align text to the center
                self.materialsTable.setItem(row, 0, item)

    #### FUNCTIONALITY ASSOCIATED WITH PROTOTYPING TAB ####
    ### --> GENERATOR TAB
    def setup_stackupBreakdown(self):
        for row in range(self.stackupBreakdown.rowCount()):
            # Set QLineEdit for first column
            line_edit1 = QLineEdit()
            line_edit1.textChanged.connect(
                lambda text, r=row: self.update_third_column(r)
            )
            self.stackupBreakdown.setCellWidget(row, 0, line_edit1)

            # Set QLineEdit for second column
            line_edit2 = QLineEdit()
            line_edit2.textChanged.connect(
                lambda text, r=row: self.update_third_column(r)
            )
            self.stackupBreakdown.setCellWidget(row, 1, line_edit2)

    def update_third_column(self, row):
        line_edit1 = self.stackupBreakdown.cellWidget(row, 0)
        line_edit2 = self.stackupBreakdown.cellWidget(row, 1)
        if line_edit1 and line_edit2:
            text1 = line_edit1.text()
            text2 = line_edit2.text()
            concatenated_text = f"{text1}{text2}"
            self.stackupBreakdown.setItem(row, 2, QTableWidgetItem(concatenated_text))
            self.update_stackupInfoTable_first_row()  # Update the stackupInfoTable after updating the third column

    def update_stackupInfoTable_first_row(self):
        """Updates the first row, first column of stackupInfoTable with the concatenated values from the third column of stackupInfoTable and updates the second row, first column with the count of non-blank rows in column 3 of stackupInfoTable."""
        # Ensure the first row, first column item exists
        target_range_first_row = self.stackupInfoTable.item(0, 0)
        if target_range_first_row is None:
            target_range_first_row = QTableWidgetItem()
            self.stackupInfoTable.setItem(0, 0, target_range_first_row)

        # Ensure the second row, first column item exists
        target_range_second_row = self.stackupInfoTable.item(1, 0)
        if target_range_second_row is None:
            target_range_second_row = QTableWidgetItem()
            self.stackupInfoTable.setItem(1, 0, target_range_second_row)

        concatenated_values = []
        non_blank_count = 0

        for row in range(self.stackupBreakdown.rowCount()):
            item = self.stackupBreakdown.item(row, 2)
            if item and item.text().strip():
                concatenated_values.append(item.text())
                non_blank_count += 1

        concatenated_text = "/".join(concatenated_values)
        target_range_first_row.setText(concatenated_text)
        target_range_second_row.setText(str(non_blank_count))

    def clear_stackupBreakdown_columns(self):
        """Clears all the cells in stackupBreakdown except for the headers, and prints their values before clearing."""
        row_count = self.stackupBreakdown.rowCount()
        column_count = self.stackupBreakdown.columnCount()

        for col in range(column_count):
            header_item = self.stackupBreakdown.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else ""

        # Print the values before clearing
        for row in range(row_count):
            for col in range(column_count):
                item = self.stackupBreakdown.item(row, col)
                value = item.text() if item else ""

        # Clear the values
        for row in range(row_count):
            for col in range(column_count):
                # Clear QLineEdit widgets in the first two columns
                if col < 2:
                    cell_widget = self.stackupBreakdown.cellWidget(row, col)
                    if cell_widget and isinstance(cell_widget, QLineEdit):
                        cell_widget.clear()
                # Clear QTableWidgetItem items in the third column
                else:
                    self.stackupBreakdown.setItem(
                        row, col, QtWidgets.QTableWidgetItem("")
                    )

    def on_sendtoCustomerInfoSheet_clicked(self):

        # Get the values from stackupInfoTable
        value1 = (
            self.stackupInfoTable.item(0, 0).text()
            if self.stackupInfoTable.item(0, 0)
            else ""
        )
        value2 = (
            self.stackupInfoTable.item(1, 0).text()
            if self.stackupInfoTable.item(1, 0)
            else ""
        )
        value3 = (
            self.stackupInfoTable.item(2, 0).text()
            if self.stackupInfoTable.item(2, 0)
            else ""
        )

        # Calculate the actual row count of productionInfo
        if self.productionInfo.rowCount() == 0:
            row_count = 1
        else:
            row_count = self.productionInfo.rowCount()

        # Find the first empty row in the fifth column of productionInfo
        for row in range(row_count):
            item = self.productionInfo.item(row, 5)
            if item is None or item.text() == "":
                # Set the values from stackupInfoTable to productionInfo in the first empty row found
                item1 = QTableWidgetItem(value1)
                item1.setTextAlignment(Qt.AlignCenter)
                self.productionInfo.setItem(row, 4, item1)

                item2 = QTableWidgetItem(value2)
                item2.setTextAlignment(Qt.AlignCenter)
                self.productionInfo.setItem(row, 3, item2)

                item3 = QTableWidgetItem(value3)
                item3.setTextAlignment(Qt.AlignCenter)
                self.productionInfo.setItem(row, 13, item3)

                break  # Exit the loop after updating the first empty row

        # Check if no empty cell was found
        if row == row_count - 1 and (item is not None and item.text() != ""):
            print("No empty cell found in column 5")

    ########################################
    ### End of Prototyping Tab functions ###
    ########################################

    ################################################################################
    ################################################################################

    #### FUNCTIONALITY ASSOCIATED WITH CUSTOMER INFORMATION TAB ####
    

    def select_customer_csv(self):
        """
        Slot function that is called when the materialCSV_here QLineEdit is clicked.
        Opens a file dialog that allows the user to select a file from their repositories.
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Customer CSV", "", "CSV Files (*.csv)", options=options
        )
        if file_name:
            self.customerCSV_here.setText(file_name)
            self.initialize_customer_dropdowns(file_name)

    def initialize_customer_dropdowns(self, file_name):
        # Define expected columns
        
        column_names = [
            "CLIENT", "PART", "TARGET PARTS", "PLIES", "STACKUP", "LENGTH (0 DEGREES)", "WIDTH (90 DEGREES)",
            "PARTS/LENGTH", "PARTS/WIDTH", "LENGTH MARGIN", "WIDTH MARGIN", "PANEL LENGTH", "PANEL WIDTH",
            "MATERIALS", "LAMINATION TEMP", "LAMINATION TIME", "Press Notch", "Oven Temperature (deg C)",
            "Error Temperature (deg C)", "Pressure (MPa)", "Hold Time (sec)", "Cycle Time (sec)", "Mold Area (in^2)",
            "Mold Qty (UL)", "Lam Tray (UL)", "Mold Top Temp (deg C)", "Mold Bot Temp (deg C)", "Mold Release (UL)",
            "Top Mold Insulation Spacer (UL)", "Bot Mold Insulation Spacer (UL)", "Mold Direction - Sticker Front (UL)",
            "Tray Width (in)", "Tray alignment position 1 (in)", "Tray alignment position 2 (in)", "Bolt Configuration (UL)"
        ]

        try:
            # Try to read the CSV file
            self.customer_df = pd.read_csv(file_name)

            # Strip leading/trailing spaces from the column names
            self.customer_df.columns = self.customer_df.columns.str.strip()

            # Check for missing columns
            missing_columns = [column for column in column_names if column not in self.customer_df.columns]

            if missing_columns:
                raise ValueError(f"CSV file is missing required headers: {', '.join(missing_columns)}")

        except (FileNotFoundError, ValueError, KeyError, pd.errors.ParserError) as e:
            # If there's an error (file not found, missing columns, key error, or parsing error), create a default DataFrame
            print(f"Error reading CSV file: {e}. Using default column names.")
            self.customer_df = pd.DataFrame(columns=column_names)

        # Ensure the DataFrame has the required columns, even if the CSV file had extra columns or was missing some
        for column in column_names:
            if column not in self.customer_df.columns:
                self.customer_df[column] = None

        # Get unique CLIENT categories, default to an empty list if the column is missing
        client_categories = sorted(self.customer_df["CLIENT"].dropna().astype(str).unique()) if "CLIENT" in self.customer_df.columns else []

        # Add combo boxes to the productionInfo
        for row in range(6):  # Assuming you have 6 rows
            client_combo = QtWidgets.QComboBox()
            client_combo.addItems(client_categories)
            self.productionInfo.setCellWidget(row, 0, client_combo)

            # Connect signal to slot for client combo box
            client_combo.currentIndexChanged.connect(self.pick_client)

    def pick_client(self):
        client_combo = self.sender()  # Get the combo box that sent the signal
        client_selection = client_combo.currentText()

        # Find the corresponding row
        for row in range(self.productionInfo.rowCount()):
            if self.productionInfo.cellWidget(row, 0) == client_combo:
                row_index = row
                break

        # Clear previous part combo box and items
        part_combo = self.productionInfo.cellWidget(row_index, 1)
        if part_combo:
            part_combo.clear()

        # Filter dataframe based on client selection
        filtered_df = self.customer_df[self.customer_df["CLIENT"] == client_selection]

        # Get unique part categories for the selected client
        part_categories = sorted(filtered_df["PART"].astype(str).unique())

        # Create a new part combo box if it doesn't exist for this row
        if not part_combo:
            part_combo = QtWidgets.QComboBox()
            part_combo.currentIndexChanged.connect(self.populate_table_with_part_data)
            self.productionInfo.setCellWidget(row_index, 1, part_combo)

        # Add items to the part combo box
        part_combo.addItems(part_categories)

    def populate_table_with_part_data(self):
        part_combo = self.sender()  # Get the combo box that sent the signal
        part_selection = part_combo.currentText()

        # Find the corresponding row
        for row in range(self.productionInfo.rowCount()):
            if self.productionInfo.cellWidget(row, 1) == part_combo:
                row_index = row
                break

        # Filter dataframe based on part selection
        filtered_df = self.customer_df[self.customer_df["PART"] == part_selection]

        if not filtered_df.empty:
            row_data = filtered_df.iloc[0]  # Get the first matching row

            # Populate the productionInfo with the corresponding data
            for col in range(2, self.productionInfo.columnCount()):
                # Check for NaN and replace with an empty string if NaN
                value = (
                    ""
                    if pd.isna(row_data.iloc[col + 1])
                    else str(row_data.iloc[col + 1])
                )
                item = QTableWidgetItem(value)
                self.productionInfo.setItem(row_index, col, item)

    def find_Clients(self):
        row_position = self.productionInfo.rowCount()
        self.productionInfo.insertRow(row_position)
        client_combo = QtWidgets.QComboBox()
        client_combo.addItems(sorted(self.customer_df["CLIENT"].astype(str).unique()))
        self.productionInfo.setCellWidget(row_position, 0, client_combo)

    def add_New_Product(self):
        row_position = self.productionInfo.rowCount()
        self.productionInfo.insertRow(row_position)

    def add_row_customerTable(self):
        row_position = self.productionInfo.rowCount()
        self.productionInfo.insertRow(row_position)
        self.add_client_dropdowns_to_row(row_position)

    def remove_row_customerTable(self):
        current_row = self.productionInfo.currentRow()
        if current_row != -1:
            self.productionInfo.removeRow(current_row)

    def add_client_dropdowns_to_row(self, row):
        client_combo = QtWidgets.QComboBox()
        client_combo.addItems(sorted(self.customer_df["CLIENT"].astype(str).unique()))
        self.productionInfo.setCellWidget(row, 0, client_combo)
        client_combo.currentIndexChanged.connect(self.pick_client)

    def laminationSheet(self):
        for row in range(self.productionInfo.rowCount()):
            part_item = self.productionInfo.item(row, 4)
            if part_item and part_item.text():  # Ensure the item exists and has text
                target_parts_item = self.productionInfo.item(row, 2)
                try:
                    target_parts = float(target_parts_item.text())
                    parts_per_length = float(self.productionInfo.item(row, 7).text())
                    parts_per_width = float(self.productionInfo.item(row, 8).text())
                    if parts_per_length != 0 and parts_per_width != 0:
                        calculated_value = math.ceil(target_parts / (parts_per_length * parts_per_width))
                        self.laminationTable.setItem(row, 0, QTableWidgetItem(str(calculated_value)))
                    else:
                        self.laminationTable.setItem(row, 0, QTableWidgetItem("NaN"))
                except ValueError as ve:
                    print(f"ValueError processing row {row}: {ve}")
                    self.laminationTable.setItem(row, 0, QTableWidgetItem("NaN"))
                except Exception as e:
                    print(f"Error processing row {row}: {e}")
                    self.laminationTable.setItem(row, 0, QTableWidgetItem("NaN"))

                # Populate the remaining cells in laminationTable
                self.laminationTable.setItem(row, 1, QTableWidgetItem(self.productionInfo.item(row, 3).text()))
                self.laminationTable.setItem(row, 2, QTableWidgetItem(self.productionInfo.item(row, 4).text()))
                self.laminationTable.setItem(row, 3, QTableWidgetItem(self.productionInfo.item(row, 13).text()))
                self.laminationTable.setItem(row, 4, QTableWidgetItem(self.productionInfo.item(row, 14).text()))
                self.laminationTable.setItem(row, 5, QTableWidgetItem(self.productionInfo.item(row, 15).text()))


    def calculate_dimensions(self, row, col):
        # Only proceed if col is within the range 4:9
        if 4 <= col <= 9:
            if self.productionInfo.item(row, 4) and self.productionInfo.item(row, 4).text():
                try:
                    # Retrieve relevant cell items
                    items = {
                        "part_length": self.productionInfo.item(row, 5),
                        "part_width": self.productionInfo.item(row, 6),
                        "parts_per_length": self.productionInfo.item(row, 7),
                        "parts_per_width": self.productionInfo.item(row, 8),
                        "length_margin": self.productionInfo.item(row, 9),
                        "width_margin": self.productionInfo.item(row, 10)
                    }

                    # Define helper function to convert item to float
                    def get_float_value(item):
                        return float(item.text()) if item else None

                    # Retrieve float values
                    values = {key: get_float_value(item) for key, item in items.items()}

                    # Calculate panel length
                    if all(values[key] is not None for key in ["part_length", "parts_per_length", "length_margin"]):
                        panel_length = ceil(values["part_length"] * values["parts_per_length"] / 0.25) * 0.25 + values["length_margin"]
                        self.productionInfo.setItem(row, 11, QTableWidgetItem(str(panel_length)))
                    else:
                        self.productionInfo.setItem(row, 11, QTableWidgetItem('NaN'))

                    # Calculate panel width
                    if all(values[key] is not None for key in ["part_width", "parts_per_width", "width_margin"]):
                        panel_width = ceil(values["part_width"] * values["parts_per_width"] / 0.25) * 0.25 + values["width_margin"]
                        self.productionInfo.setItem(row, 12, QTableWidgetItem(str(panel_width)))
                    else:
                        self.productionInfo.setItem(row, 12, QTableWidgetItem('NaN'))

                except (ValueError, TypeError):
                    # Set NaN if any conversion fails
                    self.productionInfo.setItem(row, 11, QTableWidgetItem('NaN'))
                    self.productionInfo.setItem(row, 12, QTableWidgetItem('NaN'))
    
    
    def readingOrder(self):
        num_rows = self.productionInfo.rowCount()
        num_columns = self.productionInfo.columnCount()

        # Get the column headers
        headers = [
            self.productionInfo.horizontalHeaderItem(col).text()
            for col in range(num_columns)
        ]

        # Initialize a dictionary to hold the table data
        table_data = {header: [] for header in headers}

        for row in range(num_rows):
            for col in range(num_columns):
                if col in [0, 1]:  # Handle combo boxes
                    combo_box = self.productionInfo.cellWidget(row, col)
                    if combo_box and isinstance(combo_box, QComboBox):
                        selected_text = combo_box.currentText()
                        table_data[headers[col]].append(selected_text)
                    else:
                        table_data[headers[col]].append("")
                else:
                    item = self.productionInfo.item(row, col)
                    if item:
                        table_data[headers[col]].append(item.text())
                    else:
                        table_data[headers[col]].append("")

        # Ensure all columns have the same number of entries
        max_length = max(len(col) for col in table_data.values())
        for key in table_data:
            while len(table_data[key]) < max_length:
                table_data[key].append("")

        # Convert the dictionary to a DataFrame
        customer_df = pd.DataFrame(table_data)

        if not self.materialCSV_here.text() == 'Select Material CSV':
            materials_df = pd.read_csv(self.materialCSV_here.text())
            if not customer_df.empty and not materials_df.empty and \
               "STACKUP" in customer_df.columns and "PN Concatenation" in materials_df.columns:
                output_df = calculations(materials_df, customer_df)
                return output_df
            else:
                pass
        else:
            print("One of the DataFrames is empty.")
            return None

    def populate_Production_Sheets(self):
        df = self.readingOrder()

        if df is None or df.empty:
            print("DataFrame is None or empty")
            pass
        else:
            # Populate initial cuts table
            self.initialCutsTable.setRowCount(0)
            for row_index, row in df.iterrows():
                instructions_initial = f"Make {row['initial_number_of_cuts']} number of cuts at {row['cutangle']} degrees."
                row_data_initial = [
                    row["product number"],
                    instructions_initial,
                    row["cutangle"],
                    row["initial_cut_length"],
                    row["initial_number_of_cuts"],
                    row["Description"],
                ]
                self.initialCutsTable.insertRow(self.initialCutsTable.rowCount())
                for column_index, data in enumerate(row_data_initial):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.initialCutsTable.setItem(
                        self.initialCutsTable.rowCount() - 1, column_index, item
                    )
            self.initialCutsTable.resizeColumnsToContents()

            # Populate welding table
            self.weldingTable.setRowCount(0)
            for row_index, row in df.iterrows():
                instructions_welding = f"Weld {row['initial_number_of_cuts']} number of cuts at {row['cutangle']} degrees."
                row_data_welding = [
                    row["product number"],
                    instructions_welding,
                    row["cutangle"],
                    row["number_of_welds"],
                ]
                self.weldingTable.insertRow(self.weldingTable.rowCount())
                for column_index, data in enumerate(row_data_welding):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.weldingTable.setItem(
                        self.weldingTable.rowCount() - 1, column_index, item
                    )
            self.weldingTable.resizeColumnsToContents()

            # Populate secondary cuts table
            self.secondaryCutsTable.setRowCount(0)
            for row_index, row in df.iterrows():
                instructions_secondary = f"Make {row['secondary_number_of_cuts']} number of cuts at {row['cutangle']} degrees."
                row_data_secondary = [
                    row["product number"],
                    instructions_secondary,
                    row["cutangle"],
                    row["secondary_cut_length"],
                    row["secondary_number_of_cuts"],
                ]
                self.secondaryCutsTable.insertRow(self.secondaryCutsTable.rowCount())
                for column_index, data in enumerate(row_data_secondary):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.secondaryCutsTable.setItem(
                        self.secondaryCutsTable.rowCount() - 1, column_index, item
                    )
            self.secondaryCutsTable.resizeColumnsToContents()

            print("HEREEEEE GIRL")
            self.laminationSheet()


    def save_table_to_csv(self):
        # Create a new DataFrame to hold the table data
        new_data = []

        for row in range(self.productionInfo.rowCount()):
            row_data = []
            for col in range(self.productionInfo.columnCount()):
                if col < 2:  # For combo boxes
                    cell_widget = self.productionInfo.cellWidget(row, col)
                    if cell_widget:
                        row_data.append(cell_widget.currentText())
                    else:
                        row_data.append("")
                else:  # For table items
                    item = self.productionInfo.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")

            new_data.append(row_data)

        # Debug print statements
        print("New Data Extracted from Table:")
        for row in new_data:
            print(row)

        # Ensure that new_data has the same number of columns as customer_df
        if len(new_data) > 0 and len(new_data[0]) != len(self.customer_df.columns):
            print(f"Warning: Number of columns in new_data ({len(new_data[0])}) does not match customer_df ({len(self.customer_df.columns)})")
            # Adjust new_data to have the same number of columns as customer_df
            for row in new_data:
                while len(row) < len(self.customer_df.columns):
                    row.append("")
                while len(row) > len(self.customer_df.columns):
                    row.pop()

        # Convert to DataFrame
        new_df = pd.DataFrame(new_data, columns=self.customer_df.columns)

        # Debug print statements
        print("New DataFrame to Append:")
        print(new_df)
        print("Original DataFrame Columns:")
        print(self.customer_df.columns)

        # Append new_df to customer_df
        updated_df = pd.concat([self.customer_df, new_df], ignore_index=True)

        # Save to a new CSV file
        updated_df.to_csv("updated_customer_data.csv", index=False)
        print("Saved updated data to updated_customer_data.csv")

    def show_error_message(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()
    MainWindow.show()
    sys.exit(app.exec_())
