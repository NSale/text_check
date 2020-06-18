from flask import Flask, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    return False if users.find({"Username": username}).count() == 0 else True
class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJSON = {
                "status": 301,
                "msg": "User with that username  already exists."
            }
            return retJSON
        
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        retJSON = {
            "status": 200,
            "msg": "You are successfully registered."
        }
        return retJSON

def verifyPw(username, password):

    if not UserExist(username):
        return False

    hash_pass = users.find({
        "Username":username
    })[0]["Password"]

    return True if bcrypt.hashpw(password.encode('utf8'), hash_pass) == hash_pass else False

def countTokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]

    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJSON = {
                "status": 301,
                "msg": "User doesn't exist."
            }
            return retJSON
        
        correct_pw = verifyPw(username, password)

        if not correct_pw: 
            retJSON = {
                "status": 302,
                "msg": "You entered incorrect password."
            }
            return retJSON

        num_tokens = countTokens(username)

        if not num_tokens: 
            retJSON = {
                "status": 303,
                "msg": "You're out of tokens, please refill."
            }
            return retJSON
        
        # Calculate the edit distance
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        # Ratio is the number between 0 and 1, where 1 means more similar text is
        ratio = text1.similarity(text2)

        retJSON = {
            "status": 200,
            "Similarity": ratio,
            "msg": "Similarity score calculated successfully."
        }

        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": num_tokens-1
            }
        })

        return retJSON