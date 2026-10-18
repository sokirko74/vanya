import imaplib
import time
import os

EMAIL = "sokirko@yandex.ru"
PASSWORD = os.getenv("YA_MAIL_PASSWORD")
assert PASSWORD is not None

MBOX_PATH = os.path.expanduser("yandex_backup.mbox")
INDEX_FILE = os.path.expanduser("yandex_last_index.txt")
CHUNK_SIZE = 100  # Качаем порциями по 100 писем, чтобы не перегружать сервер


def get_start_index():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r') as f:
                return int(f.read().strip())
        except ValueError:
            pass
    return 1


def save_index(index):
    with open(INDEX_FILE, 'w') as f:
        f.write(str(index))


def format_time(seconds):
    """Красиво форматирует секунды в часы, минуты и секунды."""
    if seconds < 60:
        return f"{int(seconds)} сек."
    elif seconds < 3600:
        return f"{int(seconds // 60)} мин. {int(seconds % 60)} сек."
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ч. {minutes} мин."


def download_mail():
    print(f"[{time.strftime('%H:%M:%S')}] Подключение к imap.yandex.ru...")
    mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
    mail.login(EMAIL, PASSWORD)

    status, data = mail.select('INBOX', readonly=True)
    if status != 'OK':
        print(f"[{time.strftime('%H:%M:%S')}] Не удалось открыть папку Входящие")
        return

    total_messages = int(data[0])
    start_idx = get_start_index()

    print(f"[{time.strftime('%H:%M:%S')}] Всего во Входящих найдено писем: {total_messages}")
    if start_idx > 1:
        print(
            f"[{time.strftime('%H:%M:%S')}] Возобновляем скачивание с письма №{start_idx} (осталось {total_messages - start_idx + 1} писем)...")

    # Фиксируем время начала активного скачивания для расчета ETA
    start_time = time.time()
    initial_idx = start_idx

    while start_idx <= total_messages:
        end_idx = min(start_idx + CHUNK_SIZE - 1, total_messages)
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] Запрашиваю диапазон {start_idx} - {end_idx} из {total_messages}...")

        try:
            status, msg_data = mail.fetch(f"{start_idx}:{end_idx}", '(RFC822)')

            if status == 'OK':
                with open(MBOX_PATH, 'ab') as mbox_file:
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            mbox_file.write(b"From fake@domain.com Sun Oct 11 16:40:00 2026\n")
                            mbox_file.write(response_part[1])
                            mbox_file.write(b"\n\n")

                downloaded_in_session = end_idx - initial_idx + 1
                elapsed_time = time.time() - start_time

                # Считаем скорость и расчетное время до конца (ETA)
                if downloaded_in_session > 0 and elapsed_time > 0:
                    speed = downloaded_in_session / elapsed_time  # писем в секунду
                    remaining_messages = total_messages - end_idx
                    eta_seconds = remaining_messages / speed
                    eta_str = format_time(eta_seconds)
                    speed_str = f"{speed:.1f} пис/сек"
                else:
                    eta_str = "расчет..."
                    speed_str = "--"

                print(
                    f"[{time.strftime('%H:%M:%S')}] Успешно скачано. Скорость: {speed_str} | Осталось времени: {eta_str}")

                start_idx = end_idx + 1
                save_index(start_idx)
            else:
                print(
                    f"[{time.strftime('%H:%M:%S')}] Ошибка сервера на диапазоне {start_idx}:{end_idx}. Пробую еще раз...")
                time.sleep(5)

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Сбой: {e}. Переподключение через 5 секунд...")
            time.sleep(5)
            try:
                mail = imaplib.IMAP4_SSL('imap.yandex.ru', 993)
                mail.login(EMAIL, PASSWORD)
                mail.select('INBOX', readonly=True)
            except Exception as conn_err:
                print(f"[{time.strftime('%H:%M:%S')}] Ошибка переподключения: {conn_err}.")

    print(f"[{time.strftime('%H:%M:%S')}] Готово! Все письма сохранены в файл: {MBOX_PATH}")

    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)

    mail.logout()


if __name__ == "__main__":
    download_mail()
