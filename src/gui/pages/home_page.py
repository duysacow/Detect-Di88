from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


# Trang home tổng hợp trạng thái macro và aim.
class HomePage(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("HomePage")
        self.setStyleSheet("background: #1b1b1b; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_metrics())
        layout.addLayout(self._build_summaries())
        layout.addStretch(1)

    def _build_header(self) -> QFrame:
        card = QFrame()
        card.setObjectName("PageBanner")
        card.setStyleSheet(
            """
            QFrame#PageBanner {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0d1e33,
                    stop: 1 #112944
                );
                border: 1px solid #2f3942;
                border-radius: 14px;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(3)

        eyebrow = QLabel("DI88 CONTROL")
        eyebrow.setObjectName("PageBannerEyebrow")
        title = QLabel("TRUNG TÂM ĐIỀU KHIỂN")
        title.setObjectName("PageBannerTitle")
        subtitle = QLabel("Macro & Aim By Di88")
        subtitle.setObjectName("PageBannerSubtitle")
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return card

    def _build_metrics(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._metric_card("FPS", "0", "FPS", "#8dffb1"), 1)
        layout.addWidget(self._metric_card("Độ Trễ", "0", "MS", "#ffd7a1"), 1)
        return row

    def _metric_card(self, title: str, value: str, unit: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("HomeMetricCard")
        card.setStyleSheet(
            """
            QFrame#HomeMetricCard {
                border: 1px solid #2f2f2f;
                border-radius: 11px;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 900; background: transparent;"
        )
        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(6)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {color}; font-size: 19px; font-weight: 900; background: transparent;"
        )
        unit_label = QLabel(unit)
        unit_label.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 800; background: transparent;"
        )
        value_row.addWidget(value_label)
        value_row.addWidget(unit_label)
        value_row.addStretch(1)

        helper = QLabel("Khung hình thời gian thực" if title == "FPS" else "Độ trễ suy luận hiện tại")
        helper.setStyleSheet("color: #6f767e; font-size: 9px; font-weight: 700; background: transparent;")

        layout.addWidget(title_label)
        layout.addLayout(value_row)
        layout.addWidget(helper)
        layout.addStretch(1)
        return card

    def _build_summaries(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        row.addWidget(
            self._summary_card(
                "MACRO STATUS",
                "#ff8f8f",
                [("Tư Thế", "ĐỨNG"), ("ADS", "HOLD"), ("Chế Độ Chụp", "DXCAM")],
            ),
            1,
        )
        row.addWidget(
            self._summary_card(
                "AIM STATUS",
                "#73f0ff",
                [("Model", "N/A"), ("Backend", "Chưa nạp"), ("Chế Độ Chụp", "DirectX")],
            ),
            1,
        )
        return row

    def _summary_card(self, title: str, color: str, rows: list[tuple[str, str]]) -> QFrame:
        card = QFrame()
        card.setObjectName("HomeSummaryCard")
        card.setStyleSheet(
            """
            QFrame#HomeSummaryCard {
                background: #151515;
                border: 1px solid #343434;
                border-radius: 12px;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {color}; border: none; border-radius: 4px;")
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 900; letter-spacing: 1px; background: transparent;"
        )
        title_row.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        for label_text, value_text in rows:
            row = QFrame()
            row.setObjectName("HomeSummaryRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)
            label = QLabel(label_text)
            label.setStyleSheet("color: #a7a7a7; font-size: 11px; font-weight: 700; background: transparent;")
            value = QLabel(value_text)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value.setStyleSheet("color: #f2f2f2; font-size: 12px; font-weight: 800; background: transparent;")
            row_layout.addWidget(label)
            row_layout.addStretch(1)
            row_layout.addWidget(value)
            layout.addWidget(row)
        return card
