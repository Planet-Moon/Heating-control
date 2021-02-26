import paho.mqtt.client as mqtt
from Modbus import modbus_device
from time import sleep
from queue import Queue
import json

class MQTTClient():
    def __init__(self, ipAddress, topicPrefix):
        self.client = mqtt.Client()
        self.topicPrefix = topicPrefix
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.subscribedTopics = {}
        # self.client.username_pw_set("admin", password="admin")
        self.client.connect(ipAddress, 1883, 60)
        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_start()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.subscribe("Heizung/#")

    def subscribe(self, topic):
        self.client.subscribe(topic)
        self.subscribedTopics[topic] = {"queue":Queue()}

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(str(msg.payload.decode('utf-8'))))
        for i in self.subscribedTopics:
            topicBeginning = i.rsplit("/#")
            found = msg.topic.find(topicBeginning[0])
            if found == 0:
                self.subscribedTopics[i]["queue"].put(msg)
            pass

    def publish(self, topic, payload=None, qos=0, retain=False):
        print("publishing: "+topic+" data: "+payload)
        self.client.publish(self.topicPrefix+topic, payload, qos, retain)

def toJson(name, value, unit):
    data = {"name":name,"value":value,"unit":unit}
    return str(data)

def main():
    HeizungMqttClient = MQTTClient("192.168.178.107","Heizung")
    # HeizungMqttClient = MQTTClient("broker.hivemq.com","Heizung")

    modbusServerRegister = [
            {"name":"TSP.oben2", "address":2,"length":1,"factor":0.1, "unit":"°C"},
            {"name":"SpeicherMitte", "address":5,"length":1,"factor":0.1, "unit":"°C"},
            {"name":"Kollektor", "address":7,"length":1,"factor":0.1, "unit":"°C"}
        ]
    HeizungModbusServer = modbus_device(ipAddress="192.168.178.107", port=502)
    for i in modbusServerRegister:
        HeizungModbusServer.newRegister(name=i["name"], address=i["address"], length=i["length"], factor=i["factor"], unit=i["unit"])
    
    while True:
        data = HeizungModbusServer.read_all()
        for i in data:
            jsonString = toJson(name=i[0], value=HeizungModbusServer.read_value(i[0]), unit="°C")
            HeizungMqttClient.publish(topic="", payload=jsonString)
        sleep(2)

if __name__ == "__main__":
    main()