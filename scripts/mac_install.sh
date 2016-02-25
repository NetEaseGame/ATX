#!/bin/bash

confirm () {
    # call with a prompt string or use a default
    read -r -p "${1:-Are you sure? [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

brew_install() {
    if brew list "$1" &>/dev/null
	then
		echo "PROGRAM $1 already installed"
	else
		echo "INSTALL $1 ..."
		brew install "$1"
	fi
}

echo "!!!!!!!!!!WARNING!!!!!!!!!!!!!!"
echo "DONOT run this script with root privilege"
echo "Starting setup ios environment for airtest..."
echo

confirm || exit 1

echo "This may take a long time..."

echo "-------Step 1: installing brew"
which brew || ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
hash -r

echo "-------Step 2: installing a brewed python"
brew tap homebrew/science
brew tap homebrew/python
#brew update && brew upgrade
brew_install python
brew_install node

echo "-------Step 3: installing appium"
which appium || npm install -g appium

echo "-------Step 4: installing opencv"
brew_install opencv

echo "-------Step 5: installing pillow"
brew_install pillow

echo "-------Step 6: check"
echo "python: " `which python`
echo "appium: " `appium -h &>/dev/null && echo ok || echo fail`
echo "opencv:" `python -c "import cv2" && echo ok || echo fail`
echo "appium:" `python -c "from PIL import Image" && echo ok || echo fail`

echo "-------Step 6: installing airtest"
which pip || easy_install pip
set -eu
pip install virtualenv
pip install Appium-Python-Client
pip install --upgrade -i http://mt.nie.netease.com:3141/simple/ airtest
