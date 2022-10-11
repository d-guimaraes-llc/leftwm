#!/bin/bash

# Some static data
FULLSCREEN="config.fullscreen.ron"
HALFSCREEN="config.halfscreen.ron"
SCEENS="config.2screen.ron"
FILEPATH="$HOME/.config/leftwm" 
FILE="config.ron"

# options to be set by params
obs=false
verbose=false

# Parsing params with getopt
options=$(getopt -l "help,obs,vebose" -o "hov" -a -- "$@")

eval set -- "$options"
while true
do
    case "$1" in
        -h|--help)
            showHelp
            exit 0
            ;;
        -o|--obs)
            obs=true
            ;;
        -v|--verbose)
            verbose=true
            ;;
        --)
            shift
            break;;
    esac
    shift
done

print_str () {
    if $verbose; then echo "$1"; fi
}

print_str "Getting current config file"
current=$(/usr/bin/ls -l "$FILEPATH/$FILE" | awk '{print $11}')
print_str "Current is set to: $current"


exit 0

default_switch () {
    if [[ "$current" =~ .*"$FULLSCREEN" ]]; then
        print_str "Switching to halfscreen"
        unlink "$FILEPATH/$FILE"
        ln -s "$FILEPATH/$HALFSCREEN" "$FILEPATH/$FILE"
        if verbose; then echo "Setting resolution to 1920x1080"; fi
        xrandr --output DisplayPort-1 --mode 1920x1080 
        if verbose; then echo "Setting layout to MainAndVertStack"; fi
        leftwm-command "SetLayout MainAndVertStack"
    else
        if verbose; then echo "Swiching to fullscreen"; fi
        unlink "$FILEPATH/$FILE"
        ln -s "$FILEPATH/$FULLSCREEN" "$FILEPATH/$FILE"
        if verbose; then echo "Setting resolution to 3840x1080"; fi
        xrandr --output DisplayPort-1 --mode 3840x1080
        if verbose; then echo "Setting layout to CenterMainFluid"; fi
        leftwm-command "SetLayout CenterMainFluid"
    fi
}

relaod () {
    echo "Preforming a soft reload now."
    leftwm command SoftReload 
}


new=$(ls -l "$FILEPATH/$FILE" | awk '{print $11}')
echo "The new config file is $new"
