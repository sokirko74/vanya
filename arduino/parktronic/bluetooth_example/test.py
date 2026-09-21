import time
from jnius import autoclass

# Подключаем Java-классы Андроида через Pyjnius
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
UUID = autoclass('java.util.UUID')

# Имя вашего Bluetooth-модуля (измените, если у вас называется иначе)
DEVICE_NAME = "HC-05" 

# Стандартный UUID для работы с последовательным портом (SPP профиль)
SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"

def get_bluetooth_socket():
    adapter = BluetoothAdapter.getDefaultAdapter()
    if not adapter:
        print("Bluetooth не поддерживается на этом устройстве")
        return None
        
    if not adapter.isEnabled():
        print("Пожалуйста, включите Bluetooth на телефоне!")
        return None

    # Ищем наш модуль среди сопряженных устройств
    paired_devices = adapter.getBondedDevices().toArray()
    target_device = None
    
    for device in paired_devices:
        if device.getName() == DEVICE_NAME:
            target_device = device
            break
            
    if not target_device:
        print(f"Устройство {DEVICE_NAME} не найдено в сопряженных!")
        return None

    print(f"Подключаемся к {DEVICE_NAME} ({target_device.getAddress()})...")
    
    # Создаем RFCOMM сокет для обмена данными
    uuid_obj = UUID.fromString(SPP_UUID)
    socket = target_device.createRfcommSocketToServiceRecord(uuid_obj)
    socket.connect()
    print("Успешно подключено!")
    return socket

def main():
    socket = None
    try:
        socket = get_bluetooth_socket()
        if not socket:
            return

        input_stream = socket.getInputStream()
        
        print("Ожидание данных от Arduino (для выхода закройте программу)...")
        buffer = ""
        
        while True:
            # Если в буфере есть байты для чтения
            if input_stream.available() > 0:
                # Читаем один байт и переводим в символ
                char = chr(input_stream.read())
                
                # Собираем строку до символа новой строки
                if char == '\n':
                    print(f"Получено: {buffer.strip()}")
                    buffer = ""
                else:
                    buffer += char
            else:
                time.sleep(0.1) # Защита от перегрузки процессора
                
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if socket:
            socket.close()
            print("Соединение закрыто.")

if __name__ == "__main__":
    main()
