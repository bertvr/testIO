import paho.mqtt.client as mqtt
import json
import codecs

# The callback for when the client receives a CONNACK response from the server.

msgReader = codecs.getreader("utf-8")



def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hello/world")

# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    print("msg detected Topic:" + msg.topic)
    # decode nodig voor van bytes naar string te gaan
    try:
        json_msg = json.loads(msg.payload.decode("utf-8"))
        print("Dag mijnheer " + json_msg['first_name'] + " " + json_msg['last_name'])
        print("Voornaam: " + json_msg['first_name'])
        print("Achternaam: " + json_msg['last_name'])
        print("Leeftijd: " + json_msg['age'])
    except KeyError as e:
        print("Parse ERROR!!! JSON key incorrect: " + e.args[0])
    except ValueError:
        print("Parse ERROR!!! No JSON object to parse!")


    print(msg.topic+" "+str(msg.payload))



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()