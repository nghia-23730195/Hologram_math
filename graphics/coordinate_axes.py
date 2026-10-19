"""Hệ trục tọa độ Oxyz và lưới tham chiếu cho bài học hình học."""

from OpenGL.GL import *


def draw_coordinate_axes(size=8.0, step=1.0):
    """Vẽ lưới mặt phẳng XZ và ba trục tọa độ quanh tâm."""
    glDisable(GL_LIGHTING)
    glLineWidth(1.0)

    glBegin(GL_LINES)
    glColor4f(0.12, 0.18, 0.24, 0.45)
    value = -size
    while value <= size + 0.001:
        glVertex3f(value, 0.0, -size)
        glVertex3f(value, 0.0, size)
        glVertex3f(-size, 0.0, value)
        glVertex3f(size, 0.0, value)
        value += step

    glLineWidth(2.0)
    glColor4f(0.95, 0.2, 0.2, 0.9)  # X
    glVertex3f(-size, 0.0, 0.0)
    glVertex3f(size, 0.0, 0.0)
    glColor4f(0.2, 0.95, 0.35, 0.9)  # Y
    glVertex3f(0.0, -size, 0.0)
    glVertex3f(0.0, size, 0.0)
    glColor4f(0.25, 0.55, 1.0, 0.9)  # Z
    glVertex3f(0.0, 0.0, -size)
    glVertex3f(0.0, 0.0, size)
    glEnd()
    glEnable(GL_LIGHTING)
