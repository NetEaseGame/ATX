package main

import "encoding/xml"

type Intent struct {
	Action struct {
		Name string `xml:"name,attr"`
	} `xml:"action"`
	Category struct {
		Name string `xml:"name,attr"`
	} `xml:"category"`
}

type Activity struct {
	Label        string `xml:"label,attr"`
	Name         string `xml:"name,attr"`
	IntentFilter Intent `xml:"intent-filter"`
}

type Manifest struct {
	XMLName     xml.Name `xml:"manifest"`
	Package     string   `xml:"package,attr"`
	Application struct {
		Activities []Activity `xml:"activity"`
	} `xml:"application"`
}
