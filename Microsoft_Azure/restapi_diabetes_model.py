from bson import ObjectId
from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient

connection_string = 'mongodb+srv://sikandarnust1140:ZBXI5No3tsTeKb0u@cluster0.mo69b0z.mongodb.net/newDB?retryWrites=true&w=majority'
client = MongoClient(connection_string)
database = client['Diabetes_Prediction']
collection = database['user']

app = Flask(__name__)

ML_MODEL_ENDPOINT = "http://ea491c1f-f3ef-4e9f-bfae-7f3bc22e5e09.uksouth.azurecontainer.io/score"


@app.route('/predict', methods=['POST'])
def predict():
    input_data = request.json
    print(input_data)
    api_key = request.headers.get('Authorization')
    headers = {
        'Authorization': f'Bearer {api_key}', 
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(ML_MODEL_ENDPOINT, json=input_data, headers=headers)
        response.raise_for_status()


        response_json = response.json()

        response_json_str = {str(k): v for k, v in response_json.items()}

        post = collection.insert_one(response_json_str)

        id = post.inserted_id
        response_json_str['_id'] = str(id)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": "Invalid JSON response from model"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to insert data into MongoDB: {str(e)}"}), 500

    return jsonify(response_json_str)


@app.route('/get_patient_data/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    try:
        data = collection.find_one({'_id': ObjectId(patient_id)})
        if data:
            data['_id'] = str(data['_id'])
            return jsonify(data)
        else:
            return jsonify({"error": "Patient not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_patient_data/<patient_id>', methods=['DELETE'])
def delete_patient_data(patient_id):
    try:
        data = collection.find_one({'_id': ObjectId(patient_id)})

        if not data:
            return jsonify({"error" : "patient not found"}), 200

        collection.delete_one({'_id': ObjectId(patient_id)})
        return  {"message" :  "patient data deleted successfully"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
