#!/bin/bash

echo "test detecting by contract file path:"
PonziSleuth -p test/examples -m gpt-3.5-turbo-1106 -t 0

# echo "test detecting by contract address:"
# PonziSleuth -a 0x1bea112a4bA183fcDb3D9B8bc7A144Cb8a01a532 -m llama3 -t 0