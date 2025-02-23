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
    return jsonify({'status': 'Server is running'}), 200

@app.route('/sensor', methods=['POST'])
def sensor():
    try:
        data = request.get_json()
        temperature = data.get('temperature','')
        humidity = data.get('humidity','')
        light = data.get('light','')
        if (not temperature or not humidity or not light):
            raise Exception('Invalid data')
        # Insert data into MongoDB
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
    app.run(host='0.0.0.0', port=3000,debug=True)