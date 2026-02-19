# !/bin/bash
set -e  
pyinstaller \
    --add-data ".svc:.svc" \
    --add-data ".env:.env" \
    --add-data "run.sh:run.sh" \
    --onedir \
    --name fulfillment_svc \
    main.py sms_worker.py