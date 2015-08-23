var util = require('util'),
    events = require('events'),
    dgram = require('dgram'),
    buffer = require('buffer');
var MAGIC = "Across the Great Wall, we can reach every corner in the world.";

function UDPAutoConnector(port){
    var self = this;
    events.EventEmitter.call(this);

    var UDPConnected = false;

    var socket = dgram.createSocket('udp4');
    socket.bind();

    socket.on('message', function(data){
        if(data.toString() == MAGIC){
            self.emit("registered");
            UDPConnected = true;
            return;
        }
        self.emit('data', data);
        console.log("Recv fr UDPPort:", data);
    });

    this.send = function(data){
        console.log("Send to UDPPort:", data);
        socket.send(data, 0, data.length, port, '127.0.0.1');
    }

    var MAGICBuffer = new buffer.Buffer(MAGIC);
    function register(){
        if(UDPConnected) return;
        self.send(MAGICBuffer);
        console.log("UDP Auto Connector: Trying to connect [" + port + "].");
        setTimeout(register, 2000);
    }
    register();

    return this;
}
util.inherits(UDPAutoConnector, events.EventEmitter);

module.exports = function(port){
    return new UDPAutoConnector(port);
}
