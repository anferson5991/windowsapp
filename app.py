# execute pip install -r requirements.txt in the first execution of the app

import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QProgressBar, QFileDialog, QMessageBox

def scrape_app_data():
    base_url = "https://play.google.com/store/search"
    page_number = 1
    app_data = []

    while True:
        url = f"{base_url}?c=apps&page={page_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        app_scores = soup.find_all("span", class_="w2kbF")
        app_names = soup.find_all("span", class_="DdYX5")
        app_owners = soup.find_all("span", class_="wMUdtb")
        app_links = soup.find_all("a", class_="Si6A0c Gy4nib")

        if len(app_names) == 0:
            break

        for score, name, owner, link in zip(app_scores, app_names, app_owners, app_links):
            app_data.append({
                "app_score": score.text.strip(),
                "app_name": name.text.strip(),
                "app_owner": owner.text.strip(),
                "app_links": "https://play.google.com" + link.get("href") if link else ""
            })

        page_number += 1

        # Limit the number of pages scraped or remove this if statement to scrape everything
        if page_number == 2:
            break

    # Create a DataFrame from the collected app data
    app_data = pd.DataFrame(app_data)

    # Access app_links and retrieve descriptions
    app_descriptions_text = []

    for app_link in app_data['app_links']:
        if app_link:
            response = requests.get(app_link)
            soup = BeautifulSoup(response.content, "html.parser")
            description_div = soup.find("div", class_="bARER")  # Adjust the class based on the actual structure

            if description_div:
                description_parts = description_div.find_all("br")
                app_description_parts = []
                for part in description_parts:
                    if "Apple TV channels and content may vary by country or region." in str(part.previous_sibling):
                        app_description_parts.append(str(part.previous_sibling))
                        break
                    app_description_parts.append(str(part.previous_sibling))

                app_description = "\n".join(app_description_parts).strip()
                app_descriptions_text.append(app_description)
            else:
                app_descriptions_text.append("Description not found")

    # Add descriptions to the DataFrame
    app_data['app_description_text'] = app_descriptions_text

    return app_data

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the UI
        self.initUI()

    def initUI(self):
        # Create a button
        btn = QPushButton('Scrape and Download', self)

        # Connect the button click event to a function
        btn.clicked.connect(self.scrape_and_download)

        # Create a layout for the UI
        layout = QVBoxLayout()
        layout.addWidget(btn)

        # Set the layout for the main window
        self.setLayout(layout)

        # Set window properties
        self.setWindowTitle('Web Scraper App')
        self.setGeometry(100, 100, 300, 100)

        # Create a progress bar
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        # Set the initial progress to 0%
        self.progress_bar.setValue(0)

    def scrape_and_download(self):
        try:
            # Initialize the progress bar
            self.progress_bar.setValue(0)

            # Run the web scraping function
            app_data = scrape_app_data()

            # Update the progress to 100% when scraping is complete
            self.progress_bar.setValue(100)

            # Save the data to a CSV file
            app_data.to_csv('app_data.csv', index=False)

            # Display a dialog to save the file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Database", "", "CSV Files (*.csv);;All Files (*)", options=options)

            if file_path:
                # Move the generated CSV file to the user-selected location
                import shutil
                shutil.move('app_data.csv', file_path)

        except Exception as e:
            # Display an error message to the user
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, 'Error', error_message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
