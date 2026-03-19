
# app_manager.py


import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui     import QIcon

import database as db

_app: QApplication | None = None
_win = None

# icon.png lives in the same directory as this file (project root)
_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")


def _app_icon() -> QIcon:
    """Return a QIcon from icon.png if it exists, else an empty QIcon."""
    if os.path.isfile(_ICON_PATH):
        return QIcon(_ICON_PATH)
    return QIcon()


def launch_login() -> None:
    from gui.login_window import LoginWindow
    from gui.main_window  import MainWindow

    db.init()

    icon = _app_icon()

    login = LoginWindow()
    login.setWindowIcon(icon)

    if login.exec() == QDialog.DialogCode.Accepted:
        global _win
        _win = MainWindow(login.current_user())
        _win.setWindowIcon(icon)
        _win.showMaximized()
    else:
        if _app:
            _app.quit()


def main() -> None:
    global _app
    _app = QApplication(sys.argv)
    _app.setStyle("Fusion")
    _app.setWindowIcon(_app_icon())   # taskbar + all child windows inherit
    launch_login()
    sys.exit(_app.exec())


if __name__ == "__main__":
    main()
