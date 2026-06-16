from flask import Flask, Response, send_file
from mss import mss
from PIL import Image
import io
import threading
import time

app = Flask(__name__)

# =======================
# DEFAULT SETTINGS
# =======================
FPS = 12
RES = (800, 450)
DELAY_MS = 150

FRAME_TIME = 1 / FPS

latest_frame = None
lock = threading.Lock()

# =======================
# OPTIONS MENU
# =======================
FPS_OPTIONS = {
    "a": 8,
    "b": 12,
    "c": 15,
    "d": 20,
    "x": 30  # psycho
}

RES_OPTIONS = {
    "a": (640, 360),
    "b": (800, 450),
    "c": (960, 540),
    "d": (1280, 720),
    "e": (1600, 900),
    "x": (1920, 1080)  # psycho
}

DELAY_OPTIONS = {
    "a": 200,
    "b": 150,
    "c": 100,
    "d": 75,
    "x": 50  # psycho
}

# =======================
# SETUP MENU (PC CONSOLE)
# =======================
def setup():
    global FPS, RES, FRAME_TIME, DELAY_MS

    print("\n=== STREAM SETUP ===")

    print("\nFPS:")
    print("a = 8")
    print("b = 12 (recommended)")
    print("c = 15")
    print("d = 20")
    print("x = 30 🔥 PSYCHO")

    f = input("FPS choice: ").strip().lower()
    if f in FPS_OPTIONS:
        FPS = FPS_OPTIONS[f]

    print("\nRESOLUTION:")
    print("a = 640x360")
    print("b = 800x450 (recommended)")
    print("c = 960x540")
    print("d = 1280x720")
    print("e = 1600x900")
    print("x = 1920x1080 🔥 PSYCHO")

    r = input("RES choice: ").strip().lower()
    if r in RES_OPTIONS:
        RES = RES_OPTIONS[r]

    print("\nDELAY:")
    print("a = 200ms (very stable)")
    print("b = 150ms")
    print("c = 100ms")
    print("d = 75ms")
    print("x = 50ms 🔥 PSYCHO")

    d = input("DELAY choice: ").strip().lower()
    if d in DELAY_OPTIONS:
        DELAY_MS = DELAY_OPTIONS[d]

    FRAME_TIME = 1 / FPS

    print("\n====================")
    print(f"FPS: {FPS}")
    print(f"RES: {RES}")
    print(f"DELAY: {DELAY_MS}ms")
    print("====================\n")

    if FPS == 30 or RES == (1920, 1080) or DELAY_MS <= 75:
        print("⚠ PSYCHO MODE ENABLED — expect lag or Xbox slowdown\n")

setup()

# =======================
# BACKGROUND CAPTURE LOOP
# =======================
def capture_loop():
    global latest_frame

    with mss() as sct:
        monitor = sct.monitors[1]

        while True:
            start = time.time()

            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.rgb)
            img = img.resize(RES)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=55)
            frame = buf.getvalue()

            with lock:
                latest_frame = frame

            elapsed = time.time() - start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

threading.Thread(target=capture_loop, daemon=True).start()

# =======================
# BOOT SCREEN
# =======================
@app.route("/")
def boot():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Boot</title>
<meta http-equiv="refresh" content="2;url=/live">

<style>
html,body{
    margin:0;
    background:black;
    height:100%;
}
img{
    width:100%;
    height:100%;
    object-fit:contain;
}
</style>
</head>

<body>
<img src="/boot.png">
</body>
</html>
"""

@app.route("/boot.png")
def boot_img():
    return send_file("boot.png", mimetype="image/png")

# =======================
# LIVE PAGE
# =======================
@app.route("/live")
def live():
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Live</title>
</head>

<body style="margin:0;background:black;">

<img id="s" style="width:100%">

<script>
var delay = {DELAY_MS};

function update(){{
    document.getElementById("s").src =
        "/frame.jpg?t=" + Date.now();
}}

setInterval(update, delay);
update();
</script>

</body>
</html>
"""

# =======================
# FRAME ENDPOINT
# =======================
@app.route("/frame.jpg")
def frame():
    with lock:
        if latest_frame is None:
            return "", 204

        return Response(
            latest_frame,
            mimetype="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Content-Disposition": "inline"
            }
        )

# =======================
# RUN SERVER
# =======================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=80,
        threaded=True,
        debug=False
    )