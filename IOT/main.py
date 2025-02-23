import dht
import machine
import time
import ssd1306  # Pastikan library sudah diinstall
import ujson
import network
import dht
import urequests as requests

# Konfigurasi variable global
DEVICE_ID = "esp32-sic6"
WIFI_SSID = "111"
WIFI_PASSWORD = "ciumdulu"
TOKEN = "BBUS-XvBqJJbY25P5kLxo9D42Ir4dhwjEF1"

def did_receive_callback(topic, message):
    """
    Fungsi callback yang dipicu ketika sebuah pesan diterima pada topik tertentu.

    Argumen:
        topic (str): Topik di mana pesan diterima.
        message (str): Isi pesan yang diterima.

    Mengembalikan:
        None
    """
    print('\n\nData Received! \ntopic = {0}, message = {1}'.format(topic, message))

def create_json_data(temperature, humidity, light, motion):
    """
    Membuat dictionary yang kompatibel dengan JSON berisi data lingkungan.

    Argumen:
        temperature (float): Nilai suhu.
        humidity (float): Nilai kelembaban.
        light (float): Nilai intensitas cahaya.
        motion (bool): Nilai deteksi gerakan.

    Mengembalikan:
        dict: Sebuah dictionary yang berisi data lingkungan.
    """
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "motion_value": motion
    }
    return data

def send_data_to_ubidots(data):
    """
    Mengirim data ke API Ubidots.

    Argumen:
        data (dict): Data yang akan dikirim ke Ubidots dalam format JSON.

    Mengembalikan:
        None

    Mencetak:
        Teks respons dari API Ubidots.
    """
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/" + DEVICE_ID
    headers = {"Content-Type": "application/json", "X-Auth-Token": TOKEN}
    response = requests.post(url, json=data, headers=headers)
    print("UBIDOTS Response:", response.text)
    
def send_data_to_api(data):
    """
        Mengirim data sensor ke API.
    Args:
        data (dict): Data sensor yang akan dikirim dalam format JSON.
    Returns:
        None
    """
    url = "http://amaw.eu.org/sensor"
    response = requests.post(url, json=data)
    print("API Response:", response.text)

# Konfigurasi DHT11/DHT22 di GPIO15
dht_pin = machine.Pin(15)
dht_sensor = dht.DHT11(dht_pin)  # Ganti dengan dht.DHT22(dht_pin) jika pakai DHT22
led_biru = machine.Pin(2, machine.Pin.OUT)  # GPIO2 untuk built-in LED
led_ijo = machine.Pin(5, machine.Pin.OUT)  # GPIO2 untuk built-in LED
led_ylw = machine.Pin(18, machine.Pin.OUT)  # GPIO2 untuk built-in LED
led_red = machine.Pin(19, machine.Pin.OUT)  # GPIO2 untuk built-in LED
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
buzzer = machine.Pin(14, machine.Pin.OUT)  # Gunakan GPIO15
pir = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Gunakan GPIO18

led_biru.value(0)
led_ijo.value(0)
led_ylw.value(0)
led_red.value(0)

# Konfigurasi LDR di GPIO34 (Analog input)
ldr_pin = machine.ADC(machine.Pin(32))
ldr_pin.atten(machine.ADC.ATTN_11DB)  # Agar bisa membaca hingga 3.3V

wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Connecting device to WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

while not wifi_client.isconnected():
    print("Connecting")
    led_biru.value(1)
    time.sleep(0.3)
    led_biru.value(0)
    time.sleep(0.3)
led_biru.value(0)

print("WiFi Connected!")
print(wifi_client.ifconfig())

while True:
    try:
        led_red.value(1)
        # Baca sensor DHT
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()

        # Baca nilai LDR (0 - 4095)
        ldr_value = ldr_pin.read()

        motion_value = pir.value()

        # Konversi ke persentase
        ldr_percent = (ldr_value / 4095) * 100
        led_red.value(0)

        print(f"Suhu: {temp}°C | Kelembaban: {hum}% | Cahaya: {ldr_value} ({ldr_percent:.2f}%)")
                    
        oled.fill(0)  # Bersihkan layar
        oled.text(f"Suhu: {temp}°C", 0, 0)  # Teks di posisi (x=0, y=0)
        oled.text(f"Kelembaban: {hum}%", 0, 15)
        oled.text(f"Cahaya: {ldr_value}", 0, 30)
        oled.text(f"Cahaya: {ldr_percent:.2f}%", 0, 45)
        oled.show()  # Tampilkan di layar
        
        led_ylw.value(1)
        buzzer.value(1)
        
        json_data = create_json_data(temp, hum, ldr_value, motion_value)
        send_data_to_ubidots(json_data)
        send_data_to_api(json_data)
        
        led_ylw.value(0)
        buzzer.value(0)

        print("Motion Value:", pir.value())  # Akan mencetak 0 atau 1 saat ada gerakan

    except Exception as e:
        print("Error membaca sensor:", e)
    led_ijo.value(1)
    time.sleep(2)  # Tunggu 2 detik sebelum membaca lagi
    led_ijo.value(0)
    print("")