package main

import (
	"fmt"
	"log"
	"strconv"

	"github.com/shirou/gopsutil"
)

func init() {
	commands["stat"] = FlagCommand{cmdStat, "netio"}
}

func cmdStat(args ...string) (err error) {
	var usage = "Usage:	airtoolbox stat ..."
	return RunCmd(statCommands, usage, args)
}

var (
	statCommands = map[string]FlagCommand{
		"netio": {cmdStatNetio, "<pid|proc_name>  stat net sent,recv"},
	}
)

// convert name to pid
func name2pid(name string) (int32, error) {
	pid, err := strconv.Atoi(name)
	if err == nil {
		return int32(pid), nil
	}
	pids, err := gopsutil.Pids()
	if err != nil {
		return 0, err
	}
	for _, pid := range pids {
		p, er := gopsutil.NewProcess(pid)
		if er != nil {
			continue
		}
		pname, er := p.Name()
		if er != nil {
			continue
		}
		if pname == name {
			fmt.Println(pid)
			return pid, nil
		}
	}
	return 0, fmt.Errorf("proc(%s) not found", name)
}

func cmdStatNetio(args ...string) (err error) {
	if len(args) != 1 {
		return ErrArguments
	}
	pid, err := name2pid(args[0])
	if err != nil {
		return
	}
	proc, err := gopsutil.NewProcess(pid)
	if err != nil {
		log.Fatal(err)
	}
	ncs, err := proc.NetIOCounters()
	if err != nil {
		log.Fatal(err)
	}

	var sent, recv uint64
	for _, c := range ncs {
		if c.Name == "lo" {
			continue
		}
		sent += c.BytesSent
		recv += c.BytesRecv
		fmt.Printf("%s: sent:%d, recv:%d\n", c.Name, c.BytesSent, c.BytesRecv)
	}
	fmt.Printf("send: %dKB\nrecv: %dKB\n", sent>>10, recv>>10)
	return nil
}
