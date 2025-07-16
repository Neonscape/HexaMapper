from typing import override
from qtpy.QtCore import Qt, Signal, QLocale
from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QLineEdit, QSizePolicy
from pydantic import BaseModel, Field

from widgets.controllers.controller_base import BaseController


class NumericController(BaseController):
    def __init__(
        self,
        label_text: str,
        min_value: int | float,
        max_value: int | float,
        default_value: int | float,
        step: int = 1,
        decimals: int = 0,
        parent: QWidget | None = None,
        *,
        model: BaseModel | None = None,
        model_field: str = "",
    ):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self._min = min_value
        self._max = max_value
        self._step = step
        self._decimals = decimals
        self._factor = 10 ** decimals

        # ---- new --------------------------------------------------------
        self._model = model
        self._model_field = model_field
        # -----------------------------------------------------------------

        self.label = QLabel(label_text)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.line_edit = QLineEdit()

        self.slider.setRange(
            int(min_value * self._factor), int(max_value * self._factor)
        )
        self.slider.setSingleStep(step)
        self.slider.setMaximumWidth(100)
        self.slider.setPageStep(step * 10)

        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.line_edit.setMaximumWidth(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.line_edit)

        # signals
        self.slider.valueChanged.connect(self._on_slider_change)
        self.line_edit.editingFinished.connect(self._on_edit_change)

        self.setValue(default_value)

    # ---------- public API -----------------------------------------------
    def value(self) -> int | float:
        raw = self.slider.value()
        val = raw / self._factor
        return int(val) if self._decimals == 0 else val

    def setValue(self, v: int | float) -> None:
        v = max(self._min, min(self._max, v))
        self.slider.setValue(int(v * self._factor))
        self._sync_line_edit()
        self._push_to_model()   # <--- new

    # ---------- internals ------------------------------------------------
    def _on_slider_change(self, raw: int) -> None:
        self._sync_line_edit()
        self._push_to_model()   # <--- new

    def _on_edit_change(self) -> None:
        locale = QLocale()
        v, ok = locale.toDouble(self.line_edit.text())
        if ok:
            self.setValue(v)
        else:
            self._sync_line_edit()

    def _sync_line_edit(self) -> None:
        v = self.value()
        locale = QLocale()
        if self._decimals == 0:
            txt = locale.toString(int(v))
        else:
            txt = locale.toString(float(v), "f", self._decimals)
        self.line_edit.setText(txt)

    # ---- new -----------------------------------------------------------
    def _push_to_model(self) -> None:
        """Write the current widget value into the Pydantic field."""
        if self._model is None or not self._model_field:
            return

        setattr(self._model, self._model_field, self.value())
        
    @override
    def update(self):
        return super().update()