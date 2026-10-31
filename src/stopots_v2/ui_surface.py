# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
"""Superfície orgânica vetorial, com antialiasing no renderer software."""
from PySide6.QtCore import Property, Signal, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtQuick import QQuickPaintedItem


class OrganicSurface(QQuickPaintedItem):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill = QColor('#fffdf8'); self._border = QColor('transparent'); self._softness = 1.0
        self.setAntialiasing(True)

    @Property(QColor, notify=changed)
    def surfaceColor(self): return self._fill

    @surfaceColor.setter
    def surfaceColor(self, value):
        self._fill = QColor(value); self.changed.emit(); self.update()

    @Property(QColor, notify=changed)
    def borderColor(self): return self._border

    @borderColor.setter
    def borderColor(self, value):
        self._border = QColor(value); self.changed.emit(); self.update()

    @Property(float, notify=changed)
    def softness(self): return self._softness

    @softness.setter
    def softness(self, value):
        self._softness = value; self.changed.emit(); self.update()

    def paint(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=max(1,self.width()-2),max(1,self.height()-2)
        r=min(28,h*.42,w*.18);s=self._softness
        p=QPainterPath();p.moveTo(1+r,1)
        p.cubicTo(w*.48,1+3*s,w*.6,1+5*s,w-r,1);p.quadTo(w+1,1,w+1,r+1)
        p.cubicTo(w+1,h*.42,w-3*s,h*.7,w+1,h-r);p.quadTo(w+1,h+1,w-r*.7,h+1)
        p.cubicTo(w*.65,h+1,w*.35,h-4*s,r*.8,h+1);p.quadTo(1,h+1,1,h-r)
        p.cubicTo(1,h*.7,4*s,h*.36,1,r*1.3);p.quadTo(1,1,r+1,1);p.closeSubpath()
        painter.fillPath(p,self._fill)
        if self._border.alpha():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(self._border,1.25));painter.drawPath(p)
        painter.restore()
