#!/bin/sh

if [ -z "$1" ]; then
	echo "Use create-symlinks.sh <directory>"
	echo 
	echo "directory should point to the addons directory of the server"
	exit 1
fi


for i in $(ls -1 | grep -v '*.sh'); do 
	if [ -d "$i" ]; then
		ln -s "$(pwd)/$i" "$1"
	else
		echo "'$i' doesn't exist"
	fi
done

