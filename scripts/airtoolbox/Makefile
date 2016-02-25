everything: build

build: build-linux
	GOARCH=arm go build
	cp airtoolbox ../../airtest/binfiles/
	./a.test version > ../../airtest/binfiles/airtoolbox.version

build-linux:
	go build -o a.test

install: build
	adb push airtoolbox /data/local/tmp/

test: build-linux
	./a.test
