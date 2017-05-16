import os
import sys
import argparse
import numpy as np

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    ".."
)))
from Utilities import outliers  # noqa
from Utilities import tfs_pandas  # noqa

DEF_LIMIT = 1e-5


def clean_tunes(files, limit=DEF_LIMIT):
    for file in files:
        file_df = tfs_pandas.read_tfs(file)
        mask = _get_mask(file_df, limit)
        file_df = file_df.loc[mask, :]
        _recompute_tune_stats(file_df)
        tfs_pandas.write_tfs(file_df, file_df.headers, file)


def _get_mask(file_df, limit):
    tune_col = _choose_name(file_df, "TUNEX", "TUNEY")
    mask = outliers.get_filter_mask(
        file_df.loc[:, tune_col],
        limit=limit,
    )
    return mask


def _recompute_tune_stats(file_df):
    tune_col = _choose_name(file_df, "TUNEX", "TUNEY")
    tune_avg_name = _choose_name(file_df, "Q1", "Q2")
    tune_std_name = _choose_name(file_df, "Q1RMS", "Q2RMS")
    file_df.headers[tune_avg_name] = np.mean(file_df[tune_col])
    file_df.headers[tune_std_name] = np.std(file_df[tune_col])


def _choose_name(file_df, *names):
    result = None
    for name in names:
        try:
            result = file_df[name]
            break
        except IndexError:
            continue
    if result is None:
        raise ValueError("None of " + " ".join(names) + " in the file.")
    return result


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        help="Paths to the TFS files to clean.",
        nargs="+", type=str,
    )
    parser.add_argument(
        "--limit",
        help="Limit to below which stop cleaning.",
        default=DEF_LIMIT,
        dest="limit", type=float,
    )
    options = parser.parse_args()
    return options.files, options.limit


if __name__ == "__main__":
    _files, _limit = _parse_args()
    clean_tunes(_files, _limit)
