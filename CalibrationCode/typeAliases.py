#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Type Aliases for the module."""
from typing import Tuple, Dict, Union, List

TempCoefsType = Tuple[int, int, int]
PresCoefsType = Tuple[int, int, int, int, int, int, int, int, int]
HumidityCoefsType = Tuple[int, int, int, int, int, int]
UCompDataType = List[Dict[str, Union[int]]]
