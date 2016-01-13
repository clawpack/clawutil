#!/usr/bin/env python
r"""
Consolidate common and custom sources into one source list.

If a custom file has the same name as a common file, the common one is excluded.
Exclusions can also be manually set for replacement files with different names.

NOTE:  Unfortunately we may need to implement something that allows flexibility
as to when a module is compiled and available due to depedency issues
"""

from __future__ import print_function

from __future__ import absolute_import
from __future__ import print_function
import sys
import os

def consolidate_src_lists(common_src_files, excluded_src_files, src_files):
    r"""
    """

    excluded_src_names = [os.path.basename(os.path.splitext(src_file)[0]) 
                          for src_file in excluded_src_files]
    included_src_names = [os.path.basename(os.path.splitext(src_file)[0]) 
                          for src_file in src_files]

    src_list = []
    for src_file in common_src_files:
        if os.path.basename(os.path.splitext(src_file)[0]) not in excluded_src_names and \
           os.path.basename(os.path.splitext(src_file)[0]) not in included_src_names:
            src_list.append(src_file)

    for src_file in src_files:
        src_list.append(src_file)

    return src_list


def parse_args(arg_list):
    r"""
    """
    file_list = [[], [], []]
    list_index = 0

    for arg in arg_list:
        if arg == ";":
            list_index += 1
        else:
            file_list[list_index].append(arg)

    return file_list[0], file_list[1], file_list[2]


if __name__ == '__main__':
    if len(sys.argv) == 1:
        raise ValueError("Need to provide at least one source.")
