#!/bin/bash

# Some static data
FILEPATH="$HOME/.config/leftwm" 
FULLSCREEN="config.fullscreen.ron"
HALFSCREEN="config.halfscreen.ron"
OBS="config.obs.ron"
LINK="config.ron"
MONITORTYPES=(DisplayPort HDMI DVI)

## These modes are specific to my monitor, I should get these dynamically
halfMode="1920X1080"
fullMode="3840x1080"

# Parsing params with getopt
options=$(getopt -l "help,obs,vebose" -o "hov" -a -- "$@")

showHelp () {
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
    if "$verbose"; then echo "$1"; fi
}

## This is how we get the monitors from xrandr
getMonitors () {
    local -n array="$1"
    local sedStr="s/.*\("
    for mType in "${MONITORTYPES[@]}"
    do
        sedStr+="$mType.*[01]\|"
    done
    sedStr="${sedStr:0:-2}\)/\1/p"
    array=($(xrandr --listactivemonitors | sed -n "$sedStr"))
}

## We want to prefer --auto, but maybe we haven't switched our monitor to PiP yet
#  This way we can force a mode, i.e. $halfmode or $fullmode
setScreen () {
    local output="$1"
    local mode="$2"
    if [ -z "$mode" ]; then
        local command="--mode $mode"
    else
        local command="--auto"
    fi
    $(xrandr --output "$output $command")
}

## This was the original function of this program
default_switch () {
    if [[ "$current" =~ .*"$FULLSCREEN" ]]; then
        print_str "Switching to halfscreen"
        unlink "$FILEPATH/$LINK"
        ln -s "$FILEPATH/$HALFSCREEN" "$FILEPATH/$LINK"
        print_str "Setting resolution to $halfMode"
        setScreen "$monitor" "$halfMode"
        print_str "Setting layout to MainAndVertStack"
        leftwm-command "SetLayout MainAndVertStack"
    else
        print_str "Swiching to fullscreen"
        unlink "$FILEPATH/$LINK"
        ln -s "$FILEPATH/$FULLSCREEN" "$FILEPATH/$LINK"
        print_str "Setting resolution to $fullMode"
        setScreen "$monitor" "$fullMode"
        print_str "Setting layout to CenterMainFluid"
        leftwm-command "SetLayout CenterMainFluid"
    fi
}

## This will tell left to do a soft reload, i.e. load our new config
reload () {
    print_str "Preforming a soft reload now."
    leftwm command SoftReload 
}

## Here is the main process we are trying to achieve    
main () {
    getMonitors monitors
    monitor="${monitors[0]}"

    print_str "Getting current config file"
    current=$(/usr/bin/ls -l "$FILEPATH/$LINK" | awk '{print $11}')
    print_str "Current is set to: $current"

    if "$obs"; then
        print_str "Switching to obs mode"
        if [[ "$current" =~ .*"$HALFSCREEN" ]]; then
            print_str "In halfsceen mode, switching to full"
            setScreen "$monitor" "$fullMode"
        fi
        unlink "$FILEPATH/$LINK"
        ln -s "$FILEPATH/$OBS" "$FILEPATH/$LINK"
        leftwm-command "SetLayout MainAndVertStack"
    else
        default_switch
    fi
    reload

    new=$(ls -l "$FILEPATH/$LINK" | awk '{print $11}')
    print_str "The new config file is $new"
}

main
