import tkinter as tk
from tkinter import filedialog
import src.wrapper_tools.analyse_tools
from src.interface.visualisation import InternalWindow
from src.interface.analyse import AnalysisWindows


class AppManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulateur Hydraulique - Studio CAO & Analyse")
        self.geometry("1400x900")

        self.windows = []
        self.active_window = None

        self.setup_menu()
        self.workspace = tk.Frame(self, bg="#2c3e50")
        self.workspace.pack(fill=tk.BOTH, expand=True)

    def setup_menu(self):
        menubar = tk.Menu(self)

        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(
            label="Ouvrir un réseau (.inp)...", command=self.open_file)
        menu_file.add_separator()
        menu_file.add_command(label="Quitter", command=self.quit)
        menubar.add_cascade(label="Fichier", menu=menu_file)

        menu_view = tk.Menu(menubar, tearoff=0)
        menu_view.add_command(label="Recentrer la vue active", command=lambda: self.active_window.reset_view(
        ) if hasattr(self.active_window, 'reset_view') else None)
        menubar.add_cascade(label="Vue", menu=menu_view)

        menu_analysis = tk.Menu(menubar, tearoff=0)
        menu_analysis.add_command(
            label="Nouvelle fenêtre d'Analyse (Grid Search)...", command=self.open_analysis)
        menubar.add_cascade(label="Analyse", menu=menu_analysis)

        self.config(menu=menubar)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("EPANET", "*.inp")])
        if path:
            win = InternalWindow(self.workspace, self)
            self.windows.append(win)
            win.load_file(path)

    def open_analysis(self):
        win = AnalysisWindow(self.workspace, self)
        self.windows.append(win)

    def set_active_window(self, window):
        self.active_window = window
        for w in self.windows:
            w.set_active_style(w == window)

    def remove_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
        if self.active_window == window:
            self.active_window = self.windows[-1] if self.windows else None
            if self.active_window:
                self.active_window.set_active_style(True)


app = AppManager()
app.mainloop()
