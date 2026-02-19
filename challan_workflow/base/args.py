
firefox_browser_args = [
    "--start-maximized",
    "--no-remote" # Ensures it uses the profile you specified
]

firefox_browser_ctx_args = {
    "viewport": None,
    "locale": "en-IN",
    "timezone_id": "Asia/Kolkata",
    "java_script_enabled": True,
    "record_video_dir": None,
    # These prefs help hide the 'Robot' nature in Firefox
    "extra_http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    }
}

browser_args = [
    "--disable-blink-features=AutomationControlled",
    #"--disable-features=IsolateOrigins,site-per-process",
    #"--excludeSwitches=enable-automation",
    #"--use-fake-ui-for-media-stream",
    #"--use-fake-device-for-media-stream",
    "--disable-infobars",
    "--disable-dev-shm-usage",
    #"--no-sandbox",
    "--start-maximized"
]

browser_ctx_args = {
    "viewport": None,
    "locale": "en-IN",
    "timezone_id": "Asia/Kolkata",
    #"screen": {"width": 1920, "height": 1080}, # Important: Match screen resolution to viewport
    "device_scale_factor": 1,
    "is_mobile": False,
    "has_touch": False,
    "permissions": [],
    "java_script_enabled": True
}
