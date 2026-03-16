
import argparse
from datetime import datetime
from core.processor import DBFProcessor


def main():
    p = argparse.ArgumentParser(description='DBF Record Cleaner v2.0 — CLI')
    p.add_argument('--file', required=True, help='Path to .dbf file')
    p.add_argument('--cutoff', required=True, help='Cutoff date, e.g. 2024-01-31')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--preview', action='store_true', help='Analyze only')
    g.add_argument('--clean', action='store_true', help='Perform cleanup after analysis')
    args = p.parse_args()

    cutoff = datetime.strptime(args.cutoff, '%Y-%m-%d')
    proc = DBFProcessor()

    info = proc.analyze(args.file, cutoff)

    print(f'Total: {info.total}')
    print(f'Marked for deletion: {info.marked_total}')
    print(f'To recall: {len(info.to_recall_indexes)}')
    print(f'To remove: {info.to_remove_count}')
    print(f'Remaining after cleanup: {info.remaining_after_cleanup}')
    if args.preview:
        return

    result = proc.clean(info)
    print('CLEANUP COMPLETE')
    print(f'Final records: {result.total}')

if __name__ == '__main__':
    main()
