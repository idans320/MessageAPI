from flask.json import JSONEncoder
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

Messages = {} #a dictionary containing all messages sent to an user. I would have probably have used SQLite for persistent data, but it's good for the demo. 


class GeneratorID:
    def __init__(self):
        self.id = 0

    def get_id(self):
        self.id += 1
        return self.id


generatorid = GeneratorID()

flatten = lambda l: [item for sublist in l for item in sublist]

class Message:
    def __init__(self, sender, receiver, message, subject, unread=True):
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.subject = subject
        self.creation_date = datetime.now()
        self.unread = unread
        self.deleted = False
        self.id = generatorid.get_id()


class CustomJSONEncoder(JSONEncoder):
    #An encoder for Message object
    def default(self, obj):
        if isinstance(obj,Message):
            return obj.__dict__
        elif isinstance(obj,datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

def _send_message(sender, receiver, message, subject):
    #create a new message instance
    message = Message(sender, receiver, message, subject)
    Messages[receiver].append(message) if receiver in Messages.keys(
    ) else Messages.update({receiver: [message]})
    return {"id": message.id}


def _read_message(receiver,msgid):
    if receiver in Messages.keys():
        if msgid == None: #if id not specified read the earliest unread message
            try:
                #finding the earliest unread message
                msg = next(
                    filter(lambda msg: msg.unread == True and msg.deleted == False, Messages[receiver]))
                msg.unread = False
                return msg
            except StopIteration:
                return {}
        else:
            try:
                msg = next(filter(lambda msg: msg.id == msgid and msg.deleted == False, Messages[receiver]))
                msg.unread = False
                return msg
            except StopIteration:
                return {"Error":"MessageID does not exist, or does not available to user"}
    else:
        return {}


def _read_all_messages(receiver, msgs=[]):
    #recursive reading and marked as read for all unread messages
    if receiver in Messages.keys():
        msg = _read_message(receiver,None)
        if msg == {}:
            return msgs
        else:
            new = list(msgs)
            new.append(msg)
            return _read_all_messages(receiver, new)
    else:
        return []


def _get_all_messages(receiver):
    if receiver in Messages.keys():
        #getting all message  by specific user
        return [msg for msg in filter(lambda msg : msg.deleted == False, Messages[receiver])]
    else:
        return []
def _delete_message(user,msgid):
    try:
        # iterating over all existing messages and find the specific id if it's either sent by username or received by username
        allmsgs = flatten([msg for msg in Messages.values()])
        msg = next(filter(lambda msg: (msg.receiver == user or msg.sender == user ) and msg.id == msgid and msg.deleted == False, allmsgs))
        msg.deleted = True
        return True
    except StopIteration:
        return False

@app.route('/sendmessage', methods=['POST'])
def send_message():
    try:
        content = request.json
        return jsonify(
            _send_message(content["sender"], content["receiver"],
                          content["message"], content["subject"]))
    except Exception as e:
        print(e)
        return {"Error": "Invalid Request"}


@app.route('/readmessage', methods=['POST'])
def read_message():
    try:
        content = request.json        
        msgid = content["id"] if "id" in content.keys() else None
        return jsonify(_read_message(content["username"],msgid))
    except Exception as e:
        print(e)
        return {"Error": "Invalid Request"}


@app.route('/readallmessages', methods=['POST'])
def read_all_messages():
    try:
        content = request.json
        return jsonify(_read_all_messages(content["username"]))
    except Exception as e:
        print(e)
        return {"Error": "Invalid Request"}


@app.route('/getallmessages', methods=['POST'])
def get_all_messages():
    try:
        content = request.json
        return jsonify(_get_all_messages(content["username"]))
    except Exception as e:
        print(e)
        return {"Error": "Invalid Request"}


@app.route('/deletemessage', methods=['POST'])
def delete_messages():
    try:
        content = request.json
        return jsonify({"deleted" : _delete_message(content["username"],content["id"])})
    except Exception as e:
        print(e)
        return {"Error": "Invalid Request"}