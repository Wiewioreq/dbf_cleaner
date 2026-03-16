import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import logging

from core.processor import DBFProcessor
from core.models import AnalysisResult
from gui.themes import Theme


class GuiLoggerHandler(logging.Handler):
    def __init__(self, widget: tk.Text):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.configure(state='normal')
        self.widget.insert('end', msg + '\n')
        self.widget.see('end')
        self.widget.configure(state='disabled')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DBF Record Cleaner v2.0 Enterprise')
        self.resizable(False, False)
        self.theme = Theme()
        self.processor = DBFProcessor()

        self.file_var = tk.StringVar()
        today = datetime.today()
        self.day_var = tk.StringVar(value=str(today.day))
        self.month_var = tk.StringVar(value=str(today.month))
        self.year_var = tk.StringVar(value=str(today.year))

        self._build_ui()
        self.analysis: AnalysisResult = None  # type: ignore

    def _build_ui(self):
        # File frame
        f_file = ttk.LabelFrame(self, text='DBF File')
        f_file.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Entry(f_file, textvariable=self.file_var, width=56).pack(side='left', padx=(8, 6), pady=8)
        ttk.Button(f_file, text='Browse…', command=self._browse).pack(side='left', padx=(0, 8))

        # Date frame
        f_date = ttk.LabelFrame(self, text='Delete records older than:')
        f_date.pack(fill='x', padx=10, pady=5)
        ttk.Label(f_date, text='Day').grid(row=0, column=0, padx=(8, 4), pady=8, sticky='e')
        ttk.Entry(f_date, textvariable=self.day_var, width=5, justify='center').grid(row=0, column=1)
        ttk.Label(f_date, text='Month').grid(row=0, column=2, padx=(12, 4), sticky='e')
        ttk.Entry(f_date, textvariable=self.month_var, width=5, justify='center').grid(row=0, column=3)
        ttk.Label(f_date, text='Year').grid(row=0, column=4, padx=(12, 4), sticky='e')
        ttk.Entry(f_date, textvariable=self.year_var, width=8, justify='center').grid(row=0, column=5, padx=(0, 8))

        # Buttons
        f_btn = ttk.Frame(self)
        f_btn.pack(fill='x', padx=10, pady=5)
        ttk.Button(f_btn, text='Preview', command=self._preview, width=18).pack(side='left', padx=(0, 6))
        btn_clean = ttk.Button(f_btn, text='Clean Old Records', command=self._clean, width=22)
        btn_clean.pack(side='left')

        # Status grid
        f_status = ttk.LabelFrame(self, text='Status')
        f_status.pack(fill='x', padx=10, pady=5)
        self.lbl_total = ttk.Label(f_status, text='Total records (incl. deleted): -')
        self.lbl_marked = ttk.Label(f_status, text='Currently marked for deletion: -')
        self.lbl_recall = ttk.Label(f_status, text='Will be recalled (newer/equal): -')
        self.lbl_remove = ttk.Label(f_status, text='Will be packed/removed (older): -')
        self.lbl_remaining = ttk.Label(f_status, text='Records after cleanup: -')
        for i, w in enumerate([self.lbl_total, self.lbl_marked, self.lbl_recall, self.lbl_remove, self.lbl_remaining]):
            w.grid(row=i, column=0, sticky='w', padx=8, pady=2)

        # Progress
        f_prog = ttk.Frame(self)
        f_prog.pack(fill='x', padx=10, pady=(0, 5))
        ttk.Label(f_prog, text='Progress').pack(side='left', padx=8)
        self.pb = ttk.Progressbar(f_prog, length=360, mode='determinate')
        self.pb.pack(side='left', padx=8)

        # Log
        f_log = ttk.LabelFrame(self, text='Log')
        f_log.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        self.txt = tk.Text(f_log, height=12, wrap='word', state='disabled')
        self.txt.pack(fill='both', expand=True, padx=8, pady=8)

        # Footer
        ttk.Label(self, text='Made by Pawel', foreground=self.theme.text_muted).pack(fill='x', padx=10, pady=(0, 8))

        # Attach logger to GUI
        handler = GuiLoggerHandler(self.txt)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        self.processor.logger.addHandler(handler)

    def _browse(self):
        path = filedialog.askopenfilename(title='Select DBF file', filetypes=[('DBF files', '*.dbf *.DBF'), ('All files', '*.*')])
        if path:
            self.file_var.set(path)

    def _get_cutoff(self):
        try:
            d = int(self.day_var.get()); m = int(self.month_var.get()); y = int(self.year_var.get())
            return datetime(y, m, d)
        except Exception:
            messagebox.showerror('Error', 'Please enter a valid date (day, month, year).')
            return None

    def _set_progress(self, val: int):
        val = max(0, min(100, int(val)))
        self.pb['value'] = val
        self.update_idletasks()

    def _preview(self):
        path = self.file_var.get().strip()
        cutoff = self._get_cutoff()
        if not path or not cutoff:
            return
        try:
            self._set_progress(0)
            self.analysis = self.processor.analyze(path, cutoff, progress_cb=self._set_progress)
        except Exception as e:
            messagebox.showerror('Read Error', str(e))
            return
        self._refresh_status(self.analysis)
        self._set_progress(100)

    def _clean(self):
        if not self.analysis:
            messagebox.showwarning('Warning', 'Run Preview first.')
            return
        if self.analysis.to_remove_count == 0 and len(self.analysis.to_recall_indexes) == 0:
            messagebox.showinfo('Info', 'Nothing to do — no records to recall or remove.')
            return
        cutoff_info = f"Date range: {self.analysis.min_dt} -> {self.analysis.max_dt}" if self.analysis.min_dt and self.analysis.max_dt else ''
        ok = messagebox.askyesno('Confirm Cleanup',
            f"{cutoff_info}\n\nRecall {len(self.analysis.to_recall_indexes)} newer records and pack/remove {self.analysis.to_remove_count} older records?\nA .bak backup will be created before changes.")
        if not ok:
            return
        try:
            self._set_progress(0)
            result = self.processor.clean(self.analysis, progress_cb=self._set_progress)
        except Exception as e:
            messagebox.showerror('Write Error', str(e))
            return
        self.analysis = result
        self._refresh_status(result)
        messagebox.showinfo('Success', f"Cleanup complete. {result.total} records remain.")
        self._set_progress(100)

    def _refresh_status(self, info: AnalysisResult):
        self.lbl_total.config(text=f'Total records (incl. deleted): {info.total}')
        self.lbl_marked.config(text=f'Currently marked for deletion: {info.marked_total}')
        self.lbl_recall.config(text=f'Will be recalled (newer/equal): {len(info.to_recall_indexes)}')
        self.lbl_remove.config(text=f'Will be packed/removed (older): {info.to_remove_count}')
        self.lbl_remaining.config(text=f'Records after cleanup: {info.remaining_after_cleanup}')


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()