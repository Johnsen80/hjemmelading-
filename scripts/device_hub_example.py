# Device Hub: Sensor- og avstandsstøtte

import requests
import serial


class ChronographSensor:
    """Eksempelklasse for kronograf via USB/seriell."""

    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(port, baudrate=9600, timeout=2)

    def read_velocity(self):
        self.ser.write(b"READ\n")
        line = self.ser.readline().decode().strip()
        try:
            return float(line)
        except Exception:
            return None


class RangefinderSensor:
    """Eksempelklasse for avstandsmåler via Bluetooth/HTTP."""

    def __init__(self, device_url):
        self.device_url = device_url

    def read_distance(self):
        try:
            resp = requests.get(self.device_url, timeout=2)
            resp.raise_for_status()
            data = resp.json()
            return data.get("distance_m")
        except Exception:
            return None


# Eksempelbruk:
if __name__ == "__main__":
    # Kronograf via USB
    try:
        chrono = ChronographSensor("COM3")
        v = chrono.read_velocity()
        print(f"Hastighet fra kronograf: {v} fps")
    except Exception as e:
        print("Kronograf ikke tilgjengelig:", e)

    # Avstandsmåler via HTTP
    rf = RangefinderSensor("http://localhost:5000/range")
    d = rf.read_distance()
    print(f"Avstand fra kikkert: {d} meter")
