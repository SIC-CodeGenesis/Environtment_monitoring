from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

#************************** Initiate Flask App **************************
app = Flask(__name__)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['environment_monitoring']
collection = db['sensor']

#************************** API Endpoints **************************
@app.route('/', methods=['GET'])
def index():
    """
    Endpoint utama untuk memeriksa status server.
    
    Mengembalikan:
        Response: Respons JSON dengan status server.
    """
    return jsonify({'status': 'Server is running'}), 200

@app.route('/sensor', methods=['POST'])
def sensor():
    """
    Menyimpan data sensor ke dalam database MongoDB.
    
    Menerima JSON dengan parameter:
        - temperature (float)
        - humidity (float)
        - light (float)
    
    Mengembalikan:
        Response: JSON dengan status sukses dan data yang diterima
        atau JSON dengan status gagal jika terjadi kesalahan.
    """
    try:
        data = request.get_json()
        temperature = data.get('temperature', '')
        humidity = data.get('humidity', '')
        light = data.get('light', '')
        
        if not temperature or not humidity or not light:
            raise Exception('Data tidak valid')
        
        # Memasukkan data ke MongoDB
        collection.insert_one(data)
        
        response = {
            'status': 'success',
            'data_received': {
                'temperature': temperature,
                'humidity': humidity,
                'light': light,
                'id': str(data['_id'])
            }
        }
        return jsonify(response), 200
    except Exception as e:
        response = {
            'status': 'fail',
            'message': str(e)
        }
        return jsonify(response), 500

@app.route("/sensor", methods=["GET"])
def get_sensor():
    """
    Mengambil semua data sensor dari database.
    
    Parameter opsional:
        - sort: "lowest" untuk urutan naik, "highest" untuk urutan turun.
    
    Mengembalikan:
        Response: JSON dengan daftar data sensor yang telah diurutkan.
    """
    try:
        sorted_param = request.args.get("sort", 1)
        if sorted_param == "lowest":
            sorted_param = 1
        elif sorted_param == "highest":
            sorted_param = -1
        
        data = collection.find().sort("datetime", sorted_param)
        result = []
        for item in data:
            item["_id"] = str(item["_id"])
            result.append(item)
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sensor/avg", methods=["GET"])
def get_avg():
    """
    Menghitung rata-rata nilai temperature, humidity, dan light.
    
    Mengembalikan:
        Response: JSON dengan nilai rata-rata dari setiap parameter sensor.
    """
    try:
        data = collection.aggregate([
            {"$group": {
                "_id": None,
                "avg_temp": {"$avg": "$temperature"},
                "avg_humidity": {"$avg": "$humidity"},
                "avg_light": {"$avg": "$light"}
            }},
            {"$project": {
                "_id": 0,
                "avg_temp": 1,
                "avg_humidity": 1,
                "avg_light": 1
            }}
        ])
        return jsonify({"data": list(data)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sensor/<string:field>/avg", methods=["GET"])
def get_avg_field(field):
    """
    Menghitung rata-rata dari satu parameter sensor tertentu.
    
    Parameter URL:
        - field: "temperature", "humidity", atau "light".
    
    Mengembalikan:
        Response: JSON dengan nilai rata-rata dari field yang dipilih.
    """
    try:
        if field not in ["temperature", "humidity", "light"]:
            return jsonify({"error": "Bad request"}), 400
        
        data = collection.aggregate([
            {"$group": {"_id": None, "avg": {"$avg": f"${field}"}}}, 
            {"$project": {"_id": 0, "avg": 1}}
        ])
        return jsonify({"data": list(data)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sensor/<string:field>/all", methods=["GET"])
def get_all_field(field):
    """
    Mengambil semua data dari satu parameter sensor tertentu.
    
    Parameter URL:
        - field: "temperature", "humidity", atau "light".
    
    Parameter opsional:
        - sort: "lowest" untuk urutan naik, "highest" untuk urutan turun.
    
    Mengembalikan:
        Response: JSON dengan daftar nilai field yang telah diurutkan.
    """
    try:
        sorted_param = request.args.get("sort", 1)
        if sorted_param == "lowest":
            sorted_param = 1
        elif sorted_param == "highest":
            sorted_param = -1
        
        if field not in ["temperature", "humidity", "light"]:
            return jsonify({"error": "Bad request"}), 400
        
        data = collection.find({}, {"_id": 0, field: 1}).sort(field, sorted_param)
        return jsonify({"data": list(data)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)