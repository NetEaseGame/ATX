package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

type FlagCommand struct {
	Func  func(args ...string) error
	Usage string
}

func RunCmd(commands map[string]FlagCommand, head string, args []string) error {
	var usage = head //fmt.Sprintf("Usage:	%s ...", os.Args[0])
	for name, c := range commands {
		usage = usage + "\n\t" + name + "\t\t" + c.Usage
	}
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" {
		fmt.Println(usage)
		return nil
	}
	cmdName, cmdArgs := args[0], args[1:]
	fn, exists := commands[cmdName]
	if !exists {
		return fmt.Errorf("command(%s) not found", cmdName)
	}
	return fn.Func(cmdArgs...)
}

var (
	curpwd string = filepath.Dir(os.Args[0])
)

func atoi(a string) int {
	var i int
	_, err := fmt.Sscanf(a, "%d", &i)
	if err != nil {
		log.Fatal(err)
	}
	return i
}

func itoa(i int) string {
	return strconv.Itoa(i)
}

func sh(args ...string) (err error) {
	c := exec.Command("sh", "-c", strings.Join(args, " "))
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	c.Stdin = os.Stdin
	return c.Run()
}
