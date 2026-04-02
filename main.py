import sys
from PyQt6.QtWidgets import QApplication
from data_manager import DataManager
from ui_main import MainWindow

def main():
    DataManager.init_files()
    app = QApplication(sys.argv) 
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()