#!/bin/bash

FULLSCREEN="config.fullscreen.ron"
HALFSCREEN="config.halfscreen.ron"
FILEPATH="$HOME/.config/leftwm" 
FILE="config.ron"

# use /usr/bin/ls incase ls is aliased
current=$(/usr/bin/ls -l "$FILEPATH/$FILE" | awk '{print $11}')
echo "The current is: $current"

if [[ "$current" =~ .*"$FULLSCREEN" ]]; then
    echo "Switching to halfscreen"
    unlink "$FILEPATH/$FILE"
    ln -s "$FILEPATH/$HALFSCREEN" "$FILEPATH/$FILE"
    echo "Setting resolution to 1920x1080"
    xrandr --output DisplayPort-1 --mode 1920x1080 
    echo "Setting layout to MainAndVertStack"
    leftwm-command "SetLayout MainAndVertStack"
else
    echo "Swiching to fullscreen"
    unlink "$FILEPATH/$FILE"
    ln -s "$FILEPATH/$FULLSCREEN" "$FILEPATH/$FILE"
    echo "Setting resolution to 3840x1080"
    xrandr --output DisplayPort-1 --mode 3840x1080
    echo "Setting layout to CenterMainFluid"
    leftwm-command "SetLayout CenterMainFluid"
fi

echo "Preforming a soft reload now."
leftwm command SoftReload 

new=$(ls -l "$FILEPATH/$FILE" | awk '{print $11}')
echo "The new config file is $new"
