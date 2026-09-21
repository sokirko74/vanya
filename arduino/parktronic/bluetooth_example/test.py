import socket

# Настройки подключения (должны совпадать с настройками в приложении)
HOST = '127.0.0.1'  # Локальный адрес самого телефона
PORT = 1234         # Порт, который вы указали в Serial Bluetooth Terminal

def main():
    # Создаем стандартный TCP-сокет
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    print(f"Подключение к серверу трансляции Bluetooth на {HOST}:{PORT}...")
    try:
        s.connect((HOST, PORT))
        print("Успешно подключено! Ожидание данных от Arduino...")
        
        buffer = ""
        while True:
            # Читаем данные порциями по 1 байту
            data = s.recv(1).decode('utf-8', errors='ignore')
            if not data:
                break
                
            # Собираем строку до символа новой строки
            if data == '\n':
                print(f"Получено: {buffer.strip()}")
                buffer = ""
            else:
                buffer += data
                
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
    finally:
        s.close()
        print("Соединение закрыто.")

if __name__ == "__main__":
    main()

