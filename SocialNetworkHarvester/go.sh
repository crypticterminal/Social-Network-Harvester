#!/bin/bash
gedit $(find | grep "py$" | grep -v __init__) $(find | grep "html$") &> /dev/null &
