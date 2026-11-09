#!/bin/sh
set -e
cd "$(dirname "$0")/.."

CLUSTER="${CLUSTER:-transactions}"
K="kubectl --context kind-$CLUSTER --namespace transactions"

debug() {
    echo "--- Échec : état du cluster"
    $K get pods
    $K logs --selector job-name --tail=50 --prefix || true
}
trap 'status=$?; [ $status -ne 0 ] && debug; $K patch cronjob process-transactions -p "{\"spec\":{\"suspend\":false}}" || true; exit $status' EXIT

run_job() {
    name="$1"
    $K delete job "$name" --ignore-not-found >/dev/null
    $K create job "$name" --from=cronjob/process-transactions >/dev/null
    $K wait --for=condition=complete "job/$name" --timeout=180s >/dev/null
    $K logs "job/$name"
}

$K rollout status deployment/s3 --timeout=180s
$K patch cronjob process-transactions -p '{"spec":{"suspend":true}}'

echo "--- Envoi des CSV dans le S3"
$K delete job generate-csv --ignore-not-found
$K apply -f k8s/demo/generate-csv-job.yaml
$K wait --for=condition=complete job/generate-csv --timeout=180s
$K logs job/generate-csv

echo "--- Premier traitement"
first=$(run_job process-first)
echo "$first"
echo "$first" | grep -q "3 nouveau(x) fichier(s) à traiter"
echo "$first" | grep -q "Transactions flaggées : 5/21"

echo "--- Second traitement (rien de nouveau)"
second=$(run_job process-second)
echo "$second"
echo "$second" | grep -q "Aucun nouveau fichier à traiter"

echo "Test d'architecture OK"
