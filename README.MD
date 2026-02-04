# Install PyArmor
pip install pyarmor

# Get the Hardware ID of the Client PC (run on the client first)
pyarmor hdinfo

# Generate code locked to that specific Hardware ID
pyarmor gen --bind-device <Hardware-ID> main.py
