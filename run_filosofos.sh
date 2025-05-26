#!/bin/bash
for i in {1..5}
do
  gnome-terminal -- python filosofo.py $i
done