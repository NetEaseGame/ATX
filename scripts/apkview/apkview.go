package main

import (
	"bytes"
	"encoding/xml"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"text/template"
)

var TMPAPKPATH string

func init() {
	TMPAPKPATH, _ = ioutil.TempDir(".", "apktmp-") //"tmpapk-directory"
}

var (
	format  = flag.String("f", "{{.package}}/{{.activity}}", "output format")
	apkpath = flag.String("apk", "", "android pkg path")
	quite   = flag.Bool("q", false, "suppress debug info")
)

func ParseApk() error {
	toolpath := filepath.Join(SelfDir(), "apktool.jar")
	fmt.Println(toolpath)
	c := exec.Command("java", "-jar", toolpath, "decode", "--force", *apkpath, TMPAPKPATH)
	if !*quite {
		c.Stdout = os.Stdout
		c.Stderr = os.Stderr
	}
	return c.Run()
}

func SelfDir() string {
	selfDir := filepath.Dir(os.Args[0])
	if !filepath.IsAbs(selfDir) {
		selfDir, _ = filepath.Abs(selfDir)
	}
	return selfDir
}

func ParseManifest() (pkgname string, activity string, err error) {
	manifest := filepath.Join(TMPAPKPATH, "AndroidManifest.xml")
	data, err := ioutil.ReadFile(manifest)
	if err != nil {
		return
	}
	mf := new(Manifest)
	if err = xml.Unmarshal(data, mf); err != nil {
		return
	}
	for _, act := range mf.Application.Activities {
		if act.IntentFilter.Action.Name == "android.intent.action.MAIN" {
			activity = act.Name
			break
		}
	}
	return mf.Package, activity, nil
}

func main() {
	defer os.RemoveAll(TMPAPKPATH)
	flag.Parse()
	if *apkpath == "" {
		log.Fatal("need apkpath")
	}
	if err := ParseApk(); err != nil {
		log.Fatal(err)
	}

	pkgname, activity, err := ParseManifest()
	if err != nil {
		log.Fatal(err)
	}
	wr := bytes.NewBuffer(nil)
	tmpl, err := template.New("t").Parse(*format)
	if err != nil {
		log.Fatal(err)
	}
	tmpl.Execute(wr, map[string]string{
		"package":  pkgname,
		"activity": activity})
	fmt.Println(string(wr.Bytes()))
}
