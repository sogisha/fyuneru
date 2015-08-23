var PORTS = [7100, 7101, 7102];
var SERVERPORT = 6000;

/****************************************************************************/
if(process.argv.length < 3){
    console.log("Usage: node client.js <SERVER_ADDRESS>");
    process.exit();
}

var SERVERADDR = process.argv[2];

var io = require('socket.io-client');
var SERVERURL = "ws://" + SERVERADDR + ":" + SERVERPORT;
var socket = io(SERVERURL);
var UDPAutoConnector = require('./udpAutoConnector');

console.log("Connecting to server: " + SERVERURL);

var UDPPorts = [];
for(var i=0; i<PORTS.length; i++){
    UDPPorts.push(UDPAutoConnector(PORTS[i]));
}

socket.once('connect', function(){
    console.log('connected to server');
    for(var i=0; i<PORTS.length; i++){
        UDPPorts[i].on('data', function(data){
            socket.emit('data', data);
        });
    }
    socket.on('data', function(data){
        var i = Math.floor(UDPPorts.length * Math.random());
        UDPPorts[i].send(data);
    });
});
