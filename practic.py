import serial
import time
from PIL import Image

# Порт COM, до якого підключено ESP32-C3
SERIAL_PORT = 'COM3'  # Заміни на свій порт, напр. '/dev/ttyUSB0'
BAUD_RATE = 9600

# Поріг, що використовується для визначення яка грань зверху
AXIS_THRESHOLD = 7.0  # Значення прискорення у м/с²

# Відповідність між назвами граней і шляхами до зображень
IMAGES = {
    'TOP +X': 'диплом\\1.jpg',
    'TOP -X': 'диплом\\2.jpg',
    'TOP +Y': 'диплом\\3.jpg',
    'TOP -Y': 'диплом\\4.jpg',
    'TOP +Z': 'диплом\\5.jpg',
    'TOP -Z': 'диплом\\6.jpg'
}

# Глобальні змінні для відстеження відкритого зображення та поточної грані
current_image = None
current_face = None


def determine_face(acc_x, acc_y, acc_z):
    """
    Визначає, яка грань куба зараз зверху на основі прискорення по осях.
    Повертає назву грані, якщо перевищено поріг, інакше — 'UNKNOWN'.
    """
    # Створюємо словник з можливими орієнтаціями
    axes = {
        'TOP +X': acc_x,
        'TOP -X': -acc_x,
        'TOP +Y': acc_y,
        'TOP -Y': -acc_y,
        'TOP +Z': acc_z,
        'TOP -Z': -acc_z
    }
    # Вибираємо вісь з найбільшим значенням
    face = max(axes, key=axes.get)

    # Повертаємо грань, якщо її значення більше порогу
    if abs(axes[face]) > AXIS_THRESHOLD:
        return face
    return 'UNKNOWN'


def handle_face(face):
    """
    Відкриває зображення для нової грані. Закриває попереднє, якщо треба.
    Ігнорує повторення тієї ж грані або невизначені випадки.
    """
    global current_image, current_face

    # Якщо грань не змінилась або невідома — нічого не робимо
    if face == current_face or face == 'UNKNOWN':
        return

    print(f"[→] Грань: {face}")

    # Закриваємо попереднє зображення, якщо воно відкрите
    if current_image:
        current_image.close()

    # Отримуємо шлях до зображення для поточної грані
    image_path = IMAGES.get(face)
    if image_path:
        try:
            # Відкриваємо та показуємо зображення
            current_image = Image.open(image_path)
            current_image.show()
            current_face = face  # Оновлюємо поточну грань
        except Exception as e:
            print(f"[!] Помилка при відкритті зображення: {e}")
    else:
        print(f"[!] Немає зображення для грані: {face}")


def main():
    """
    Основна функція програми: зчитує дані з серійного порту,
    обробляє їх, визначає грань і викликає відповідне зображення.
    """
    try:
        # Встановлюємо з'єднання з ESP через COM-порт
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[✓] Підключено до {SERIAL_PORT}")
        time.sleep(2)  # Чекаємо на ініціалізацію

        while True:
            # Читаємо рядок з порту
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            try:
                # Парсимо 6 значень з рядка
                parts = line.strip(';').split(';')
                if len(parts) != 6:
                    continue

                # Отримуємо акселерометричні координати
                acc_x, acc_y, acc_z = map(float, parts[:3])

                # Визначаємо активну грань
                face = determine_face(acc_x, acc_y, acc_z)

                # Обробляємо зміну грані
                handle_face(face)

            except ValueError:
                print(f"[!] Некоректні дані: {line}")

    except serial.SerialException as e:
        print(f"[!] Помилка з'єднання: {e}")


# Запускаємо програму
if __name__ == "__main__":
    main()
