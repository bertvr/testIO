import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import codecs
import threading
import time
from IOPi.ABE_helpers import ABEHelpers
from IOPi.ABE_IoPi import IoPi
import time
import datetime


mqttServer = "localhost"
mqttServerPort = 1883
mqttWritTopic = "raspi/writeI2cIO"
mqttReadTopic = "raspi/readI2cIO"


# init i2c bus
i2c_helper = ABEHelpers()
i2c_bus = i2c_helper.get_smbus()

bus = IoPi(i2c_bus, 0x20)

#port 0 als outputs
bus.set_port_direction(0, 0x00)
bus.write_port(0, 0x00)
#port 1 als inputs
bus.set_port_direction(1, 0xFF)
bus.set_port_pullups(1, 0xFF)

# hook for json dumps
def jdefault(o):
    return o.__dict__


class MsgReadI2cIO:
    def __init__(self, timeStamp, port, pin, val):
        self.timeStamp = timeStamp
        self.port = port
        self.pin = pin
        self.val = val





# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hello/world")
    client.subscribe(mqttWritTopic)

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



def on_write_i2c_message(client, userdata, msg):
    print("on_write_i2c_message detected Topic:" + msg.topic)
    # decode nodig voor van bytes naar string te gaan n
    try:
        json_msg = json.loads(msg.payload.decode("utf-8"))
        print("pin: " + str(json_msg['pin']) + " Value:" + str(json_msg['value']))
        bus.write_pin(json_msg['pin'], json_msg['value'])
    except KeyError as e:
        print("on_write_i2c_message: Parse ERROR!!! JSON key not pin: " + e.args[0])

    try:
        json_msg = json.loads(msg.payload.decode("utf-8"))
        print("mux: " + str(json_msg['mux']) + " Value:" + str(json_msg['value']))
        bus.write_port(0, json_msg['value'])
    except KeyError as e:
        print("on_write_i2c_message: Parse ERROR!!! JSON key not mux: " + e.args[0])
    except ValueError:
        print("on_write_i2c_message: Parse ERROR!!! No JSON object to parse!")

    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.message_callback_add(mqttWritTopic, on_write_i2c_message)
# mqttc.message_callback_add("$SYS/broker/bytes/#", on_message_bytes)

client.connect(mqttServer, mqttServerPort, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
#client.loop_forever()
client.loop_start()


lastVal = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0,
               9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0}


while True:
    # read pin 1 on bus 1.  If pin 1 is high set the output on bus 2 pin 1 to high, otherwise set it to low.
    # connect pin 1 on bus 1 to ground to see the output on bus 2 pin 1 change state.
    # print("input loop started")



    for i in [9,10,11,12,13,14,15,16]:
        value = bus.read_pin(i)
        if (lastVal[i] != value):
            print("input " + str(i) + " triggered! value=" + str(value))
            print("lastValue " + str(lastVal[i]) )
            msg = MsgReadI2cIO(str(datetime.datetime.now()), 1, i, value)
            publish.single(mqttReadTopic, json.dumps(msg, default=jdefault), hostname=mqttServer, port=mqttServerPort)
            lastVal[i] = value
            lastVal[i] = value



    # wait 0.1 seconds before reading the pins again

    time.sleep(0.1)

