#!/usr/bin/env node

if(process.argv.length < 4){
    console.log("Usage: node server.js <SERVER_PORT> UDP_PORT1 UDP_PORT2 ...");
    process.exit();
}

var PORTS = process.argv.slice(3);
var SERVERPORT = parseInt(process.argv[2], 10);
for(var i=0; i<PORTS.length; i++) PORTS[i] = parseInt(PORTS[i], 10);

/****************************************************************************/

var http = require('http').Server();
var io = require('socket.io')(http);
var UDPAutoConnector = require('./udpAutoConnector');

var UDPPorts = [];
for(var i=0; i<PORTS.length; i++){
    UDPPorts.push(UDPAutoConnector(PORTS[i]));
}

function newSocketConnection(socket){
    console.log("New connection on SocketIO");
    for(var i=0; i<UDPPorts.length; i++){
        UDPPorts[i].on('data', function(data){
            // send UDP emitted data back to client
            socket.emit('data', data);            
        });
    }
    socket.on('data', function(data){
        var i = Math.floor(UDPPorts.length * Math.random());
        UDPPorts[i].send(data);
    });
    socket.emit('greeting', {});
}

io.on('connection', newSocketConnection);
http.listen(SERVERPORT, function(){
    console.log('listening on *:' + SERVERPORT);
});
