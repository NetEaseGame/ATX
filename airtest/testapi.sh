#/bin/bash
curl -X POST -F query=@testdata/mule.png -F origin=@testdata/football.png mt.nie.netease.com/api/image/locate
