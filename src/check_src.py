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
import warnings
import argparse


def check_duplicate_fortran_src(src_list):
    r"""Check to see if there may be hidden fixed-format Fortran files.

    """

    output = ""

    # Extract all base paths to check for duplicate src conflicts
    base_paths = []
    for src_file in src_list:
        if os.path.dirname(src_file) not in base_paths:
            base_paths.append(os.path.dirname(src_file))

    for src_file in src_list:
        base_name = os.path.splitext(os.path.basename(src_file))[0]
        extension = os.path.splitext(src_file)[-1]

        if extension.lower() in (".f90", ".f"):
            if extension.lower() == ".f90":
                file_name = "%s.f" % base_name
            elif extension.lower() == ".f":
                file_name = "%s.f90" % base_name

            for base_path in base_paths:
                check_file = os.path.join(base_path, file_name)
                if os.path.exists(check_file):
                    output = "".join((output, "%s -- %s, " % (src_file,
                                                              check_file)))

    return output


def consolidate_src_lists(src_files, common_src_files, excluded_src_files):
    r"""
    Takes source lists provided and consolidates them based on the following:
     - source in the *src_files* list is always added,
     - source in the *common_src_files* list is included except if it is in the
       *exclued_src_files* list or specified in *src_files*.
    """

    excluded_src_names = [os.path.basename(os.path.splitext(src_file)[0])
                          for src_file in excluded_src_files] +  \
                         [os.path.basename(os.path.splitext(src_file)[0])
                          for src_file in src_files]

    src_list = []
    for src_file in common_src_files:
        name = os.path.basename(os.path.splitext(src_file)[0])
        if name not in excluded_src_names:
            src_list.append(src_file)

    for src_file in src_files:
        src_list.append(src_file)

    return src_list


def parse_args(arg_list, delimiter=";"):
    r"""Parses the command line input into lists separated by *delimiter*
    """
    file_lists = [[]]

    for arg in arg_list:
        if arg == delimiter:
            file_lists.append([])
        else:
            file_lists[-1].append(arg)

    return file_lists


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Consolidate and check Fortran source list.")
        print("  Usage:  ./check_src.py [consolidate|conflict] ...")
        print("  Two functions exist in this script: ")
        print("    (1) consolidate - a unified list of source based on three")
        print("        lists, the overall source list, a list of source that")
        print("        be included if not already in the first source list or")
        print("        if it is in the third exclude list.")
        print("    (2) conflict - Given a list of source files check to see")
        print("        if there might be Fortran 90 source with '.f90' that")
        print("        would hide a fixed-format Fortran source with '.f'.")

    if sys.argv[1].lower() == "consolidate":
        source_files, common_files, excluded_files = parse_args(sys.argv[2:])
        src_list = consolidate_src_lists(source_files, common_files,
                                                       excluded_files)
        print(" ".join(src_list))

    elif sys.argv[1].lower() == "conflicts":
        print(check_duplicate_fortran_src(sys.argv[2:]))

    else:
        raise ValueError("ERROR:  Unknown sub-command %s." % sys.argv[1])
