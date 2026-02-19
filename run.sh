#!/bin/bash

# cd $HOME/challan/fulfillment-svc
# source ../.venv/bin/activate

# xattr -dr com.apple.quarantine .
# find . -name "*.so" -exec codesign --force --sign - {} \;

# find workflow -name "*.so" -print0 \
#   | xargs -0 codesign --force --deep --sign -

export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export GRPC_ENABLE_FORK_SUPPORT=true
export PYTHONFAULTHANDLER=1
export MAX_MESSAGES_PER_WORKER=300
export SMS_PORT=9090


## 1. AUTO-KILL: Clean up port 9090 if already in use
EXISTING_PID=$(lsof -t -i :$SMS_PORT || true)
if [ ! -z "$EXISTING_PID" ]; then
    echo "Port $SMS_PORT is busy (PID: $EXISTING_PID). Cleaning up..."
    kill -9 $EXISTING_PID 2>/dev/null
    sleep 1 # Give the OS a second to release the socket
fi  

uvicorn sms_worker:app --reload --host 127.0.0.1 --port $SMS_PORT & OTP_PID=$!
echo "OTP worker started (pid=$OTP_PID)"


while true; do
   if ! kill -0 $OTP_PID 2>/dev/null; then
       echo "OTP worker died. Exiting..."
       exit 1
   fi

   python main.py
   echo "Worker exited, restarting in 5s..."
   sleep 5
done