var PORTS = [17100, 17101, 17102];
var SERVERPORT = 6000;

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
            socket.send('data', data);            
        });
    }
    socket.on('data', function(data){
        var i = Math.floor(UDPPorts.length * Math.random());
        UDPPorts[i].send(data);
    });
}

io.on('connection', newSocketConnection);
http.listen(SERVERPORT, function(){
    console.log('listening on *:' + SERVERPORT);
});
