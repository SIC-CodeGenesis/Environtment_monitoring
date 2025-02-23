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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000,debug=True)