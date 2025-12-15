from __future__ import annotations

import tkinter as tk


class MainWindow:
    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root or tk.Tk()


def create_app() -> MainWindow:
    return MainWindow()
