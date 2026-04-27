import serial


def import_from_device(port, baudrate=9600):
    """
    Import data from an external device via a serial port.

    :param port: Serial port to connect to (e.g., 'COM3').
    :param baudrate: Baud rate for the serial connection.
    """
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"Connected to device on {port}.")
            while True:
                line = ser.readline().decode("utf-8").strip()
                if line:
                    print(f"Received: {line}")
                    # Process the data here (e.g., save to database)
    except serial.SerialException as e:
        print(f"Serial error: {e}")


if __name__ == "__main__":
    # Example usage
    import_from_device("COM3")
