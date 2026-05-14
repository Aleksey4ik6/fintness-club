APP_STYLESHEET = """
QWidget {
    background: #f6f7fb;
    color: #202433;
    font-family: Segoe UI;
    font-size: 14px;
}
QFrame#Sidebar {
    background: #172033;
}
QFrame#Sidebar QLabel {
    background: transparent;
}
QLabel#Brand {
    background: transparent;
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
}
QPushButton#NavButton {
    background: transparent;
    color: #d8deea;
    border: 0;
    border-radius: 8px;
    padding: 12px 14px;
    text-align: left;
}
QPushButton#NavButton:hover, QPushButton#NavButton:checked {
    background: #26334d;
    color: #ffffff;
}
QLabel#PageTitle {
    font-size: 24px;
    font-weight: 700;
}
QFrame#MetricCard {
    background: #ffffff;
    border: 1px solid #e4e7ef;
    border-radius: 8px;
}
QLabel#MetricValue {
    font-size: 28px;
    font-weight: 700;
}
QPushButton {
    background: #1f7a5c;
    color: #ffffff;
    border: 0;
    border-radius: 7px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: #16654b;
}
QPushButton#DangerButton {
    background: #c24141;
}
QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #ffffff;
    border: 1px solid #d7dce8;
    border-radius: 7px;
    padding: 8px;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #e4e7ef;
    border-radius: 8px;
    gridline-color: #edf0f6;
}
QHeaderView::section {
    background: #eef2f7;
    border: 0;
    padding: 9px;
    font-weight: 700;
}
"""
