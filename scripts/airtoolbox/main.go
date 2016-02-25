package main

import (
	"fmt"
	"log"
	"os"
)

const VERSION = "ver1.1"

var (
	commands = map[string]FlagCommand{
		"version": {cmdVersion, "show version"},
	}
)

func cmdVersion(args ...string) (err error) {
	fmt.Println(VERSION)
	return nil
}

func main() {
	usage := fmt.Sprintf("Usage:	%s ...", os.Args[0])
	err := RunCmd(commands, usage, os.Args[1:])
	if err != nil {
		log.Fatal(err)
	}
}
