#!/usr/bin/env bash

set -e

usage() {
    echo "Usage: $0 {install|reinstall}"
    exit 1
}

install() {
  virtualenv ve
  ve/bin/pip3 install -r requirements.txt

  PYTHON_VERSION=$(
    ve/bin/python3 --version | awk '{print $NF}' | awk -F. '{print $1"."$2}'
  )

  ORIG_DIR=$PWD
  cd ve/lib/python"$PYTHON_VERSION"/site-packages/ && {
    for patch in "$ORIG_DIR"/share/patches/*.patch; do
      patch -p0 < "$patch"
    done
  } && cd "$ORIG_DIR"
}

reinstall() {
  rm -rf ve/
  install
}

# Check if at least one argument is provided
if [ "$#" -eq 0 ]; then
  usage
fi

# Process the command using a case statement
case $1 in
  install)
    install
    ;;
  reinstall)
    reinstall
    ;;
  *)
    echo "Error: Unknown command '$1'"
    usage
    ;;
esac
