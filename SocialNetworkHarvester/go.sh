#!/bin/bash
gedit $(find | grep "py$\|\.html" | grep -v __init__) &> /dev/null &
