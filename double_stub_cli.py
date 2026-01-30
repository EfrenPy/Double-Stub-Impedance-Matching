#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Double-Stub Impedance Matching Calculator

Thin wrapper for backwards compatibility. The main code is in the
double_stub package (src/double_stub/).

Author: Efren Rodriguez Rodriguez
Created: Mon Oct 14 10:22:44 2019
"""

import sys
import os
import importlib

if __name__ == '__main__':
    # Add src/ to path so the package can be found without installation
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    sys.path.insert(0, src_dir)
    cli = importlib.import_module('double_stub.cli')
    sys.exit(cli.main())
