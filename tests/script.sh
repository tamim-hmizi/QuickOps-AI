#!/bin/bash

echo "This should say VM : "

curl -X POST http://localhost:8001/analyze-deployment \
  -H "Content-Type: application/json" \
  -d @tests/vm_test.json

echo "*******************"

echo "This should say K8S : "

curl -X POST http://localhost:8001/analyze-deployment \
  -H "Content-Type: application/json" \
  -d @tests/k8s_test.json

echo "*******************"
