#!/bin/sh
version="$1"
if [ -z "$version" ]
then
  echo "usage: $0 version-tag"
  exit 1
fi
tar -c -v -z --transform 's/^v\(.*\)/xenbee-\1/g' --exclude "*.svn*" -f xenbee-$version.tar.gz v$version
