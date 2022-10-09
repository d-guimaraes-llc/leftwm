#!/bin/bash

xprop | grep WM_CLASS | awk '{print $4}'
