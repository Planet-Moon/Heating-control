#%%
#
# Example to perform a speedwire discovery using python
#
import codecs
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.application.internet import MulticastServer

# Change this address to the address of you local network interface
localInterface = '192.168.179.107' # 110

# Nothin to change below this line
spwMCastAdr = '239.12.255.254'
spwPort = 9522

discoveryRequest  = '534d4100000402a0ffffffff0000002000000000'
discoveryRequest_text =  codecs.decode(discoveryRequest,'hex')
discoveryResponse = '534d4100000402a000000001000200000001'
discoveryResponse_text =  codecs.decode(discoveryResponse,'hex')
discoveryResponse = '534d4100000402a000000001'

found_devices = []

#%%
class MulticastClientUDP(DatagramProtocol):

    def startProtocol(self):
        print("Joining speedwire multicast group.")
        self.transport.joinGroup(spwMCastAdr)
        self.transport.setOutgoingInterface(localInterface)
        
        print("Sending discovery request.")
        data = codecs.decode(discoveryRequest, 'hex')
        self.transport.write(data, (spwMCastAdr, spwPort))

    def datagramReceived(self, datagram, srcAddress_port_obj):
        global found_devices
        srcAddress, port = srcAddress_port_obj
        data = codecs.encode(datagram, 'hex')
        
        device_obj = [srcAddress, data]

        ipAddressFound = False
        for i in found_devices:
            if i[0] == srcAddress:
                ipAddressFound = True
                break

        if not ipAddressFound:
            found_devices.append(device_obj) 
            print("IP address found: "+srcAddress)   
        
        compare_with = codecs.decode(discoveryResponse, 'hex')
        comparison = data.startswith(compare_with)
        if (comparison):
            print("Found Device: "+srcAddress)

def stopReactor():
    global found_devices
    print("Discovery finished.")
    for i in found_devices:
        print(str(i[0])+":\n\t"+str(i[1]))
    reactor.stop()

reactor.listenMulticast(spwPort, MulticastClientUDP(), listenMultiple=True)
reactor.callLater(10, stopReactor)
reactor.run()