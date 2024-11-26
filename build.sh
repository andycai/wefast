#!/bin/bash

# 构建 Windows 版本
echo "Building Windows version..."
docker build -f Dockerfile.windows -t unitytool-win .
docker create --name unitytool-win unitytool-win
docker cp unitytool-win:/src/dist ./dist-windows
docker rm -f unitytool-win

# 构建 Linux 版本
echo "Building Linux version..."
docker build -f Dockerfile.linux -t unitytool-linux .
docker create --name unitytool-linux unitytool-linux
docker cp unitytool-linux:/src/dist ./dist-linux
docker rm -f unitytool-linux

echo "Build complete!" 