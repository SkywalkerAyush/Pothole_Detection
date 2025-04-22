#!/usr/bin/python3
import smbus2
import time
from datetime import datetime
import requests  # for fetching GPS

# MPU Constants
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47

DEVICE_ADDRESS      = 0x68
ACCEL_SCALE_FACTOR  = 16384.0
GYRO_SCALE_FACTOR   = 131.0
SAMPLE_RATE_HZ      = 10
LOOP_DELAY          = 1.0 / SAMPLE_RATE_HZ

# Your Flask GPS endpoint (note the added "/gps")
GPS_URL = "https://designlab.pagekite.me/gps"

def MPU_Init(bus):
    try:
        bus.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 0x00)
        time.sleep(0.1)
    except OSError as e:
        print(f"MPU Init Error: {e}")
        exit(1)

def read_raw_data(bus, addr):
    try:
        high = bus.read_byte_data(DEVICE_ADDRESS, addr)
        low  = bus.read_byte_data(DEVICE_ADDRESS, addr + 1)
        value = (high << 8) | low
        if value >= 0x8000:
            value = -((65535 - value) + 1)
        return value
    except OSError:
        return None

def get_gps():
    """
    Fetches { lat, lon } from your Flask app.
    Returns a tuple of (lat, lon) or ('','') on failure.
    """
    try:
        res = requests.get(GPS_URL, timeout=1.0)
        if res.status_code == 200:
            data = res.json()
            return data.get("lat", ""), data.get("lon", "")
        else:
            print(f"GPS HTTP {res.status_code}")
    except Exception as e:
        print(f"GPS fetch error: {e}")
    return "", ""

if __name__ == "__main__":
    try:
        bus = smbus2.SMBus(1)
        MPU_Init(bus)

        # CSV header
        print("Timestamp,AccelX_g,AccelY_g,AccelZ_g,GyroX_dps,GyroY_dps,GyroZ_dps,Latitude,Longitude")

        last_lat, last_lon = "", ""

        while True:
            timestamp = datetime.now().isoformat()

            # read raw sensor data
            accel_x_raw = read_raw_data(bus, ACCEL_XOUT_H)
            accel_y_raw = read_raw_data(bus, ACCEL_YOUT_H)
            accel_z_raw = read_raw_data(bus, ACCEL_ZOUT_H)
            gyro_x_raw  = read_raw_data(bus, GYRO_XOUT_H)
            gyro_y_raw  = read_raw_data(bus, GYRO_YOUT_H)
            gyro_z_raw  = read_raw_data(bus, GYRO_ZOUT_H)

            # if any read fails, skip and retry
            if None in [accel_x_raw, accel_y_raw, accel_z_raw,
                        gyro_x_raw, gyro_y_raw, gyro_z_raw]:
                time.sleep(LOOP_DELAY)
                continue

            # scale to g and degrees/sec
            accel_x = accel_x_raw / ACCEL_SCALE_FACTOR
            accel_y = accel_y_raw / ACCEL_SCALE_FACTOR
            accel_z = accel_z_raw / ACCEL_SCALE_FACTOR
            gyro_x  = gyro_x_raw  / GYRO_SCALE_FACTOR
            gyro_y  = gyro_y_raw  / GYRO_SCALE_FACTOR
            gyro_z  = gyro_z_raw  / GYRO_SCALE_FACTOR

            # fetch GPS at ~1 Hz
            if int(time.time()) % 1 == 0:
                lat, lon = get_gps()
                if lat and lon:
                    last_lat, last_lon = lat, lon

            # output CSV line
            print(f"{timestamp},"
                  f"{accel_x:.4f},{accel_y:.4f},{accel_z:.4f},"
                  f"{gyro_x:.4f},{gyro_y:.4f},{gyro_z:.4f},"
                  f"{last_lat},{last_lon}")

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        pass
    finally:
        if 'bus' in locals():
            bus.close()
