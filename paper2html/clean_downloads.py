import os
from os.path import join as pjoin
from glob import glob
import fire


def clean_downloads(filepath, storage_limit):
    dirpath, _ = os.path.split(filepath)
    pdf_files = glob(pjoin(dirpath, '*.pdf'))
    pdf_files.sort(key=lambda pdf: -os.path.getctime(pdf))
    storage_use = 0
    for pdf in pdf_files:
        storage_use += os.path.getsize(pdf)
        if storage_use > storage_limit:
            os.remove(pdf)


if __name__ == '__main__':
    fire.Fire()
