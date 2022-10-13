#!/bin/bash

# Some static data
FULLSCREEN="config.fullscreen.ron"
HALFSCREEN="config.halfscreen.ron"
OBS="config.obs.ron"
FILEPATH="$HOME/.config/leftwm" 
LINK="config.ron"
# need to support HDMI too... and multiple
monitor=$(xrandr --listactivemonitors | sed -n  "s/.*\(DisplayPort-[01]\)/\1/p")
halfMode="1920x1080"
fullMode="3840x1080"

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

show_help () {
    echo "This tool switches between a few different leftwm configs"
    echo "By default, it switches between 3840x1080 and 1920x1080"
    echo "By passing a flag you can also switch it to obs mode (3840x1080 with 2 workspaces)"
    echo "Example calls"
    echo "switch-config.sh"
    echo "switch-config.sh --verbose --obs"
    echo "switch-config.sh -v"
    echo ""
    echo ""
    echo ""
    echo "Flags:"
    echo "-v --verbose   Verbose mode"
    echo "-h --help      Get this help screen"
    echo "-o --obs       Switch to obs mode"
    echo "Note: if in obs mode, calling with no flag will go back to Fullsceen mode"
}

print_str "Getting current config file"
current=$(/usr/bin/ls -l "$FILEPATH/$LINK" | awk '{print $11}')
print_str "Current is set to: $current"

default_switch () {
    if [[ "$current" =~ .*"$FULLSCREEN" ]]; then
        print_str "Switching to halfscreen"
        unlink "$FILEPATH/$LINK"
        ln -s "$FILEPATH/$HALFSCREEN" "$FILEPATH/$LINK"
        print_str "Setting resolution to $halfMode"
        xrandr --output "$monitor" --mode "$halfMode"
        print_str "Setting layout to MainAndVertStack"
        leftwm-command "SetLayout MainAndVertStack"
    else
        print_str "Swiching to fullscreen"
        unlink "$FILEPATH/$LINK"
        ln -s "$FILEPATH/$FULLSCREEN" "$FILEPATH/$LINK"
        print_str "Setting resolution to $fullMode"
        xrandr --output "$monitor" --mode "$fullMode"
        print_str "Setting layout to CenterMainFluid"
        leftwm-command "SetLayout CenterMainFluid"
    fi
}

reload () {
    echo "Preforming a soft reload now."
    leftwm command SoftReload 
}

if "$obs"; then
    print_str "Switching to obs mode"
    if [[ "$current" =~ .*"$HALFSCREEN" ]]; then
        print_str "In halfsceen mode, switching to full"
        xrandr --output "$monitor" --mode "$fullMode"
    fi
    unlink "$FILEPATH/$LINK"
    ln -s "$FILEPATH/$OBS" "$FILEPATH/$LINK"
    leftwm-command "SetLayout MainAndVertStack"
else
    default_switch
fi
reload

new=$(ls -l "$FILEPATH/$LINK" | awk '{print $11}')
echo "The new config file is $new"
