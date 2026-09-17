"""Dark Qt stylesheet for the application."""

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e24;
    color: #e0e0e8;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QMainWindow {
    background-color: #18181c;
}
QGroupBox {
    border: 1px solid #3a3a48;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #9ab4ff;
}
QLabel {
    color: #c8c8d4;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #2a2a34;
    border: 1px solid #454558;
    border-radius: 4px;
    padding: 4px 6px;
    min-height: 22px;
    selection-background-color: #4a6fa5;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #6a8fd8;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #2a2a34;
    selection-background-color: #4a6fa5;
}
QPushButton {
    background-color: #3d5a9e;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4d6aae;
}
QPushButton:pressed {
    background-color: #2d4a8e;
}
QPushButton#btnReset {
    background-color: #4a4a58;
}
QPushButton#btnReset:hover {
    background-color: #5a5a68;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555568;
    background: #2a2a34;
}
QCheckBox::indicator:checked {
    background: #3d5a9e;
    border-color: #6a8fd8;
}
QScrollArea {
    border: none;
    background: transparent;
}
QSplitter::handle {
    background: #3a3a48;
    width: 3px;
}
QStatusBar {
    background: #141418;
    color: #9090a0;
}
QMessageBox {
    background-color: #1e1e24;
}
"""
