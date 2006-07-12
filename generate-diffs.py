#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generate changes and diff files for new packages

import os
import logging

from momlib import *
from util import tree


def options(parser):
    parser.add_option("-p", "--package", type="string", metavar="PACKAGE",
                      action="append",
                      help="Process only theses packages")
    parser.add_option("-c", "--component", type="string", metavar="COMPONENT",
                      action="append",
                      help="Process only these destination components")

def main(options, args):
    if len(args):
        distros = args
    else:
        distros = get_pool_distros()

    # For each package in the given distributions, iterate the pool in order
    # and generate a diff from the previous version and a changes file
    for distro in distros:
        for dist in DISTROS[distro]["dists"]:
            for component in DISTROS[distro]["components"]:
                if options.component is not None \
                       and component not in options.component:
                    continue

                for source in get_sources(distro, dist, component):
                    if options.package is not None \
                           and source["Package"] not in options.package:
                        continue

                    sources = get_pool_sources(distro, source["Package"])
                    version_sort(sources)

                    last = None
                    for this in sources:
                        try:
                            generate_diff(distro, last, this)
                        finally:
                            if last is not None:
                                cleanup_source(last)

                        last = this

def generate_diff(distro, last, this):
    """Generate the differences."""
    logging.debug("%s: %s %s", distro, this["Package"], this["Version"])

    changes_filename = changes_file(distro, this)
    if not os.path.isfile(changes_filename):
        unpack_source(this)
        try:
            save_changes_file(changes_filename, this, last)
            logging.info("Saved changes file: %s",
                          tree.subdir(ROOT, changes_filename))
        except (ValueError, OSError):
            logging.error("dpkg-genchanges for %s failed",
                          tree.subdir(ROOT, changes_filename))

    if last is None:
        return

    diff_filename = diff_file(distro, this)
    if not os.path.isfile(diff_filename):
        unpack_source(this)
        unpack_source(last)
        save_patch_file(diff_filename, last, this)
        save_basis(diff_filename, last["Version"])
        logging.info("Saved diff file: %s", tree.subdir(ROOT, diff_filename))


if __name__ == "__main__":
    run(main, options, usage="%prog [DISTRO...]",
        description="generate changes and diff files for new packages")