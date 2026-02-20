from __future__ import annotations
from PySide6.QtWidgets import QApplication

from tcas_sim.sim.simulator import Simulator
from tcas_sim.gui.main_window import MainWindow


def main():
    app = QApplication([])
    sim = Simulator()  # you customize time_scale, intruders, probability here if you want
    w = MainWindow(sim)
    w.resize(1320, 760)
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
