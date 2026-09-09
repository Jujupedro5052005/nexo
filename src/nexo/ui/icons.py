"""Small, dependency-free vector icon set used throughout the UI."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap


def icon(name: str, color: str = "#9AA7B8", size: int = 20) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.5, size / 11))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _draw(painter, name, float(size))
    painter.end()
    return QIcon(pixmap)


def _draw(painter: QPainter, name: str, size: float) -> None:
    s = size / 20
    if name in {"overview", "analytics", "reports"}:
        for x, top in ((3, 10), (8, 5), (13, 8), (18, 3)):
            painter.drawLine(QPointF(x*s, 16*s), QPointF(x*s, top*s))
    elif name in {"wallet", "portfolio"}:
        painter.drawRoundedRect(QRectF(2*s, 5*s, 16*s, 11*s), 2*s, 2*s)
        painter.drawLine(QPointF(3*s, 7*s), QPointF(15*s, 7*s))
        painter.drawEllipse(QPointF(14*s, 11*s), s, s)
    elif name in {"assets", "search"}:
        painter.drawEllipse(QRectF(3*s, 3*s, 10*s, 10*s))
        painter.drawLine(QPointF(12*s, 12*s), QPointF(18*s, 18*s))
    elif name in {"transactions", "swap"}:
        for points in ((3,7,16,7),(13,4,16,7),(16,7,13,10),(17,14,4,14),(7,11,4,14),(4,14,7,17)):
            painter.drawLine(QPointF(points[0]*s,points[1]*s), QPointF(points[2]*s,points[3]*s))
    elif name in {"planning", "calendar"}:
        painter.drawRoundedRect(QRectF(3*s, 4*s, 14*s, 13*s), 2*s, 2*s)
        painter.drawLine(QPointF(3*s, 8*s), QPointF(17*s, 8*s))
        painter.drawLine(QPointF(7*s, 2*s), QPointF(7*s, 6*s))
        painter.drawLine(QPointF(13*s, 2*s), QPointF(13*s, 6*s))
    elif name in {"goals", "target"}:
        painter.drawEllipse(QRectF(3*s, 3*s, 14*s, 14*s))
        painter.drawEllipse(QRectF(7*s, 7*s, 6*s, 6*s))
    elif name in {"alerts", "bell"}:
        painter.drawArc(QRectF(5*s, 4*s, 10*s, 12*s), 0, 180*16)
        painter.drawLine(QPointF(5*s, 10*s), QPointF(3*s, 15*s))
        painter.drawLine(QPointF(3*s, 15*s), QPointF(17*s, 15*s))
        painter.drawLine(QPointF(17*s, 15*s), QPointF(15*s, 10*s))
        painter.drawArc(QRectF(8*s, 14*s, 4*s, 4*s), 180*16, 180*16)
    elif name in {"settings", "gear"}:
        painter.drawEllipse(QRectF(6*s, 6*s, 8*s, 8*s))
        painter.drawEllipse(QRectF(9*s, 9*s, 2*s, 2*s))
        for points in ((10,2,10,6),(10,14,10,18),(2,10,6,10),(14,10,18,10)):
            painter.drawLine(QPointF(points[0]*s,points[1]*s), QPointF(points[2]*s,points[3]*s))
    elif name in {"plus", "add"}:
        painter.drawLine(QPointF(4*s, 10*s), QPointF(16*s, 10*s))
        painter.drawLine(QPointF(10*s, 4*s), QPointF(10*s, 16*s))
    elif name == "user":
        painter.drawEllipse(QRectF(7*s, 3*s, 6*s, 6*s))
        painter.drawArc(QRectF(3*s, 10*s, 14*s, 9*s), 0, 180*16)
    elif name == "logout":
        painter.drawArc(QRectF(2*s, 3*s, 11*s, 14*s), 70*16, 220*16)
        painter.drawLine(QPointF(9*s, 10*s), QPointF(18*s, 10*s))
        painter.drawLine(QPointF(15*s, 7*s), QPointF(18*s, 10*s))
        painter.drawLine(QPointF(18*s, 10*s), QPointF(15*s, 13*s))
    else:
        painter.setBrush(QBrush(QColor("#10C7C7")))
        painter.drawEllipse(QPointF(10*s, 10*s), 3*s, 3*s)
