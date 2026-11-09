#!/bin/sh
set -e
cd "$(dirname "$0")/.."

CLUSTER="${CLUSTER:-transactions}"
IMAGE="transactions-pipeline:local"

docker build -t "$IMAGE" .
kind load docker-image "$IMAGE" --name "$CLUSTER"
kubectl --context "kind-$CLUSTER" apply -f k8s/
