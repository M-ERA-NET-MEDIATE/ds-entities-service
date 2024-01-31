#!/usr/bin/env bash
set -mx

# Install coverage
pip install -r .github/utils/requirements.txt

# Run server with coverage as a job
# Redo the Dockerfile entrypoints, but pointing to the run_with_coverage script
# Avoid '--reload' always.
if [ "$1" == "development" ]; then
    gunicorn --bind "0.0.0.0:${PORT}" --log-level debug --workers 1 --worker-class entities_service.uvicorn.UvicornWorker --pythonpath ".github/utils" run_with_coverage:APP &
elif [ "$1" == "production" ]; then
    gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --worker-class entities_service.uvicorn.UvicornWorker --pythonpath ".github/utils" run_with_coverage:APP &
else
    echo "unknown environment"
    exit 1
fi

echo "$(jobs -l)"

echo "waiting for signal to kill gunicorn"
SECONDS=0
while [ ! -f "stop_gunicorn" ] && [[ ${SECONDS} -lt ${RUN_TIME:-40} ]]; do
    sleep 1
done

echo "stopping gunicorn"
rm -f stop_gunicorn
GUNICORN_PID=$(ps -C gunicorn fch -o pid | head -n 1)
kill -HUP $GUNICORN_PID
sleep ${STOP_TIME:-3}

echo "exited $0"
