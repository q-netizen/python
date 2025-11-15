import paho.mqtt.client as mqtt
import requests
import json

# Настройки MQTT (wqtt.ru)
MQTT_BROKER = "10.200.200.1"  # Адрес брокера
MQTT_PORT = 1883      # Порт
TOPIC_TEMPERATURE = "/devices/climate_control/controls/setTemp"  # Температура
TOPIC_FAN_SPEED = "/devices/climate_control/controls/cooler_speed"          # Скорость: 1=low, 2=medium, 3=high, 4=auto
TOPIC_ONOFF = "/devices/climate_control/controls/cooler1_status"              # Вкл/выкл: 1=вкл, 0=выкл
TOPIC_MODE = "/devices/climate_control/controls/cooler_mode"                # Режим: 1=cool, 2=heat, 3=fan_only, 4=dry, 5=auto

# Настройки Yandex API (из ваших данных)
YANDEX_TOKEN = "y0__xDhxYi6BRjzvzsg6a_wjRUqTAQRYsUNMq_gTpSwGlGapcXaGA"  # Ваш токен
DEVICE_ID = "eac57bfa-fbf3-4b48-ac62-f9bc7b037f6b"  # ID кондиционера
SKILL_ID = "T"  # Skill ID из JSON

# Функция для отправки команды на Yandex API
def send_command_to_yandex(actions):
    url = "https://api.iot.yandex.net/v1.0/devices/actions"
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Content-Type": "application/json"
    }
    # Структура: devices — массив, actions — массив команд для одного устройства
    data = {
        "devices": [
            {
                "id": DEVICE_ID,
                "actions": actions  # Массив команд (можно несколько)
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Отправлено на Yandex: {actions}")
        print(f"Ответ: {response.status_code} - {response.text}")
        if response.status_code != 200:
            print("Ошибка: Проверьте токен, ID и команду. Подробности в ответе.")
    except Exception as e:
        print(f"Ошибка запроса: {e}")

# Обработчик сообщений MQTT
def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8')  # Значение из топика
    topic = message.topic
    print(f"Получено из MQTT: Топик={topic}, Значение={payload}")
    
    actions = []  # Массив для команд (можно отправить несколько сразу)
    
    if topic == TOPIC_TEMPERATURE:
        # Температура: range, instance "temperature", value — число 16-30
        try:
            temp_value = int(payload)
            if 16 <= temp_value <= 30:
                actions.append({
                    "type": "devices.capabilities.range",
                    "state": {
                        "instance": "temperature",
                        "value": temp_value
                    }
                })
            else:
                print("Ошибка: Температура вне диапазона 16-30°C.")
        except ValueError:
            print("Ошибка: Значение температуры не число.")
    
    elif topic == TOPIC_FAN_SPEED:
        # Скорость: mode, instance "fan_speed", value — маппинг чисел на строки
        speed_mapping = {"1": "low", "2": "medium", "3": "high", "4": "auto"}
        if payload in speed_mapping:
            actions.append({
                "type": "devices.capabilities.mode",
                "state": {
                    "instance": "fan_speed",
                    "value": speed_mapping[payload]
                }
            })
        else:
            print(f"Ошибка: Скорость '{payload}' не в списке 1-4.")
    
    elif topic == TOPIC_ONOFF:
        # Вкл/выкл: on_off, instance "on", value — true/false
        if payload == "2":
            actions.append({
                "type": "devices.capabilities.on_off",
                "state": {
                    "instance": "on",
                    "value": True
                }
            })
        elif payload == "1":
            actions.append({
                "type": "devices.capabilities.on_off",
                "state": {
                    "instance": "on",
                    "value": False
                }
            })
        else:
            print(f"Ошибка: Значение onoff '{payload}' не 0 или 1.")
    
    elif topic == TOPIC_MODE:
        # Режим: mode, instance "thermostat", value — маппинг чисел на строки
        mode_mapping = {"1": "cool", "2": "heat", "3": "fan_only", "4": "dry", "5": "auto"}
        if payload in mode_mapping:
            actions.append({
                "type": "devices.capabilities.mode",
                "state": {
                    "instance": "thermostat",
                    "value": mode_mapping[payload]
                }
            })
        else:
            print(f"Ошибка: Режим '{payload}' не в списке 1-5.")
    
    # Отправка команд, если есть
    if actions:
        send_command_to_yandex(actions)

# Подключение к MQTT
def main():
    client = mqtt.Client()
    client.on_message = on_message
    
    # Аутентификация
    #client.username_pw_set("u_YQTY7E", "G62N7HLz")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("Подключено к MQTT.")
        
        # Подписка на все топики
        client.subscribe([
            (TOPIC_TEMPERATURE, 0),
            (TOPIC_FAN_SPEED, 0),
            (TOPIC_ONOFF, 0),
            (TOPIC_MODE, 0)
        ])
        print("Подписка на топики выполнена.")
        
        # Запуск цикла прослушивания
        client.loop_forever()
    except Exception as e:
        print(f"Ошибка подключения к MQTT: {e}")

if __name__ == "__main__":
    main()
