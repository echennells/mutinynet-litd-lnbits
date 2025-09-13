group "default" {
  targets = ["bitcoind"]
}

target "bitcoind" {
  dockerfile = "Dockerfile"
  platforms = [
    "linux/amd64",
    "linux/arm64",
    "linux/arm/v7"
  ]
  tags = ["mutinynet-bitcoind:latest"]
}