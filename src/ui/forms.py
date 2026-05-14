from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QCompleter,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class EntityDialog(QDialog):
    def __init__(
        self,
        title: str,
        fields: list[dict[str, Any]],
        data: dict[str, Any] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.fields = fields
        self.inputs: dict[str, Any] = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        for field in fields:
            name = field["name"]
            label = field["label"]
            widget = self._create_widget(field, data.get(name) if data else None)
            self.inputs[name] = widget
            form.addRow(label, widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict[str, Any]:
        result = {}
        for field in self.fields:
            name = field["name"]
            widget = self.inputs[name]
            result[name] = self._read_widget(widget, field["type"])
        return result

    def _create_widget(self, field: dict[str, Any], value: Any):
        field_type = field["type"]
        if field_type in ("choice", "foreign_choice"):
            widget = QComboBox()
            options = field["options_provider"]() if "options_provider" in field else field["options"]
            for key, label in options:
                widget.addItem(label, key)
            if field_type == "foreign_choice":
                widget.setEditable(True)
                widget.setInsertPolicy(QComboBox.NoInsert)
                widget.completer().setCompletionMode(QCompleter.PopupCompletion)
                widget.completer().setFilterMode(Qt.MatchContains)
                widget.completer().setCaseSensitivity(Qt.CaseInsensitive)
            if value is not None:
                index = widget.findData(value)
                widget.setCurrentIndex(max(index, 0))
            return widget
        if field_type == "date":
            widget = QDateEdit(calendarPopup=True)
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setDate(QDate.fromString(str(value), "yyyy-MM-dd") if value else QDate.currentDate())
            return widget
        if field_type == "datetime":
            widget = QDateTimeEdit(calendarPopup=True)
            widget.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            widget.setDateTime(
                QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm:ss")
                if value
                else QDateTime.currentDateTime()
            )
            return widget
        if field_type == "int":
            widget = QSpinBox()
            widget.setRange(0, 100000)
            widget.setValue(int(value or 0))
            return widget
        if field_type == "money":
            widget = QDoubleSpinBox()
            widget.setRange(0, 10000000)
            widget.setDecimals(2)
            widget.setValue(float(value or 0))
            return widget
        if field_type == "text":
            widget = QTextEdit()
            widget.setFixedHeight(90)
            widget.setPlainText(str(value or ""))
            return widget

        widget = QLineEdit()
        widget.setText(str(value or ""))
        return widget

    def _read_widget(self, widget, field_type: str):
        if field_type in ("choice", "foreign_choice"):
            return widget.currentData()
        if field_type == "date":
            return widget.date().toString("yyyy-MM-dd")
        if field_type == "datetime":
            return widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        if field_type == "int":
            return widget.value()
        if field_type == "money":
            return widget.value()
        if field_type == "text":
            return widget.toPlainText().strip()
        return widget.text().strip()


def open_entity_dialog(
    title: str,
    fields: list[dict[str, Any]],
    on_save: Callable[[dict[str, Any]], None],
    data: dict[str, Any] | None = None,
    parent=None,
) -> None:
    dialog = EntityDialog(title, fields, data, parent)
    if dialog.exec() == QDialog.Accepted:
        on_save(dialog.values())
