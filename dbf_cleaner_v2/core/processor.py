
import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from typing import Callable, Optional
from datetime import datetime

import dbf  # type: ignore

from .models import AnalysisResult
from .utils import parse_dt, find_dt_field, is_locked
from .config import load_config

ProgressCB = Optional[Callable[[int], None]]  # percent 0..100

class DBFProcessor:
    def __init__(self, log_dir: str = 'logs', logger: Optional[logging.Logger] = None):
        self.cfg = load_config()
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger = logger or self._build_logger()

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger('dbfcleaner')
        if logger.handlers:
            return logger
        logger.setLevel(getattr(logging, self.cfg['log_level']))
        log_path = os.path.join(self.log_dir, 'cleaner.log')
        rh = RotatingFileHandler(log_path, maxBytes=int(self.cfg['log_max_bytes']), backupCount=int(self.cfg['log_backups']))
        fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        rh.setFormatter(fmt)
        logger.addHandler(rh)
        # Also console for CLI
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        return logger

    # -------------------- Analysis --------------------
    def analyze(self, path: str, cutoff: datetime, progress_cb: ProgressCB = None) -> AnalysisResult:
        self._prechecks(path)
        self.logger.info('Analyze start | file=%s | cutoff=%s', path, cutoff.strftime('%Y-%m-%d'))

        table = dbf.Table(path)
        table.open(mode=dbf.READ_ONLY)
        try:
            dt_col = find_dt_field(table)
            if dt_col is None:
                cols = ', '.join(table.field_names)
                raise RuntimeError("Column 'DT' not found. Available: %s" % cols)

            total = len(table)
            to_recall = []
            to_remove = 0
            not_marked = 0
            parse_fail = 0
            min_dt = None
            max_dt = None

            if total == 0:
                return AnalysisResult(path, dt_col, 0, 0, [], 0, 0, 0, None, None)

            for i, record in enumerate(table):
                if progress_cb and (i % 997 == 0):  # lightweight callback
                    progress_cb(int(i * 100 / max(total, 1)))

                is_del = dbf.is_deleted(record)
                try:
                    raw = getattr(record, dt_col)
                except Exception:
                    raw = None

                dt_val = parse_dt(raw)
                if dt_val is None:
                    parse_fail += 1
                else:
                    if (min_dt is None) or (dt_val < min_dt):
                        min_dt = dt_val
                    if (max_dt is None) or (dt_val > max_dt):
                        max_dt = dt_val

                if is_del:
                    if dt_val is not None and dt_val.date() >= cutoff.date():
                        to_recall.append(i)
                    else:
                        to_remove += 1
                else:
                    not_marked += 1

            marked_total = len(to_recall) + to_remove
            self.logger.info(
                'Analyze done | total=%d marked=%d recall=%d remove=%d remaining=%d parse_fail=%d',
                total, marked_total, len(to_recall), to_remove, len(to_recall) + not_marked, parse_fail
            )
            return AnalysisResult(path, dt_col, total, marked_total, to_recall, to_remove, not_marked, parse_fail, min_dt, max_dt)
        finally:
            table.close()

    # -------------------- Clean --------------------
    def clean(self, analysis: AnalysisResult, progress_cb: ProgressCB = None) -> AnalysisResult:
        path = analysis.path
        self._prechecks(path)
        self.logger.info('Clean start | file=%s', path)

        # Nothing to do
        if analysis.to_remove_count == 0 and len(analysis.to_recall_indexes) == 0:
            self.logger.info('Nothing to do')
            return analysis

        # Backup
        if self.cfg.get('backup', True):
            bak_path = path + '.bak'
            shutil.copy2(path, bak_path)
            self.logger.info('Backup created | %s', bak_path)

        # Recall then pack
        table = dbf.Table(path)
        table.open(mode=dbf.READ_WRITE)
        try:
            recalled = 0
            total_recall = len(analysis.to_recall_indexes)
            for n, idx in enumerate(analysis.to_recall_indexes):
                rec = table[idx]
                if dbf.is_deleted(rec):
                    dbf.undelete(rec)
                    recalled += 1
                if progress_cb and total_recall:
                    progress_cb(int((n+1) * 50 / total_recall))  # first half of progress

            # pack (may take time)
            table.pack()
            self.logger.info('Packed | removed=%d', analysis.to_remove_count)
        finally:
            final_count = len(table)
            table.close()

        if progress_cb:
            progress_cb(100)
        self.logger.info('Clean done | final_records=%d', final_count)
        return AnalysisResult(
            path=path,
            dt_column=analysis.dt_column,
            total=final_count,
            marked_total=0,
            to_recall_indexes=[],
            to_remove_count=0,
            not_marked_count=final_count,
            parse_fail_count=analysis.parse_fail_count,
            min_dt=analysis.min_dt,
            max_dt=analysis.max_dt,
        )

    # -------------------- helpers --------------------
    def _prechecks(self, path: str) -> None:
        if not os.path.isfile(path):
            raise FileNotFoundError('File not found: %s' % path)
        if is_locked(path):
            raise PermissionError('File appears to be in use/locked: %s' % path)
