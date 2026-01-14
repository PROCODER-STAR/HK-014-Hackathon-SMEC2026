// Global variables
let peer;
let localStream;
let connections = [];
let dataConnections = [];
let videoEnabled = true;
let audioEnabled = true;

// Canvas variables
let canvas = document.getElementById('whiteboard');
let ctx = canvas.getContext('2d');
let isDrawing = false;
let currentColor = '#000000';
let brushSize = 3;

// Initialize everything when page loads
window.onload = function() {
    setupCanvas();
    initializePeer();
    getUserMedia();
    setupEventListeners();
};

// Setup canvas
function setupCanvas() {
    canvas.width = canvas.offsetWidth;
    canvas.height = 300;
}

// Initialize PeerJS
function initializePeer() {
    peer = new Peer();
    
    peer.on('open', function(id) {
        document.getElementById('myPeerId').textContent = 'Your ID: ' + id;
        document.getElementById('status').textContent = 'Ready! Share your ID with others.';
    });
    
    peer.on('call', function(call) {
        call.answer(localStream);
        handleIncomingCall(call);
    });
    
    peer.on('connection', function(conn) {
        handleDataConnection(conn);
    });
}

// Get user's camera and microphone
function getUserMedia() {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(function(stream) {
            localStream = stream;
            document.getElementById('localVideo').srcObject = stream;
        })
        .catch(function(error) {
            console.log('Error accessing media devices:', error);
            alert('Could not access camera/microphone');
        });
}

// Setup all event listeners
function setupEventListeners() {
    // Connect button
    document.getElementById('connectBtn').addEventListener('click', function() {
        let remotePeerId = document.getElementById('remotePeerId').value.trim();
        if (remotePeerId) {
            connectToPeer(remotePeerId);
        }
    });
    
    // Video controls
    document.getElementById('toggleVideo').addEventListener('click', toggleVideo);
    document.getElementById('toggleAudio').addEventListener('click', toggleAudio);
    document.getElementById('shareScreen').addEventListener('click', shareScreen);
    document.getElementById('leaveCall').addEventListener('click', leaveCall);
    
    // Canvas events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);
    
    // Canvas tools
    document.getElementById('colorPicker').addEventListener('change', function(e) {
        currentColor = e.target.value;
    });
    
    document.getElementById('brushSize').addEventListener('input', function(e) {
        brushSize = e.target.value;
    });
    
    document.getElementById('clearCanvas').addEventListener('click', clearCanvas);
    
    // File sharing
    document.getElementById('selectFileBtn').addEventListener('click', function() {
        document.getElementById('fileInput').click();
    });
    
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
    
    // Tab switching
    let tabs = document.querySelectorAll('.tab');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            switchTab(tab.getAttribute('data-tab'));
        });
    });
}

// Connect to a peer
function connectToPeer(remotePeerId) {
    // Make video call
    let call = peer.call(remotePeerId, localStream);
    handleIncomingCall(call);
    
    // Make data connection
    let conn = peer.connect(remotePeerId);
    handleDataConnection(conn);
}

// Handle incoming video call
function handleIncomingCall(call) {
    call.on('stream', function(remoteStream) {
        addVideoStream(remoteStream, call.peer);
    });
    
    call.on('close', function() {
        removeVideoStream(call.peer);
    });
    
    connections.push(call);
}

// Handle data connection
function handleDataConnection(conn) {
    conn.on('open', function() {
        document.getElementById('status').textContent = 'Connected to ' + conn.peer;
        dataConnections.push(conn);
    });
    
    conn.on('data', function(data) {
        if (data.type === 'draw') {
            drawRemote(data);
        } else if (data.type === 'clear') {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        } else if (data.type === 'file') {
            receiveFile(data);
        }
    });
    
    conn.on('close', function() {
        dataConnections = dataConnections.filter(function(c) {
            return c !== conn;
        });
    });
}

// Add video stream to page
function addVideoStream(stream, peerId) {
    let videoBox = document.createElement('div');
    videoBox.className = 'video-box';
    videoBox.id = 'video-' + peerId;
    
    let video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    video.playsinline = true;
    
    let name = document.createElement('span');
    name.className = 'video-name';
    name.textContent = 'Peer: ' + peerId.substring(0, 8);
    
    videoBox.appendChild(video);
    videoBox.appendChild(name);
    document.getElementById('videosGrid').appendChild(videoBox);
}

// Remove video stream
function removeVideoStream(peerId) {
    let videoBox = document.getElementById('video-' + peerId);
    if (videoBox) {
        videoBox.remove();
    }
}

// Toggle video on/off
function toggleVideo() {
    videoEnabled = !videoEnabled;
    localStream.getVideoTracks()[0].enabled = videoEnabled;
    
    let btn = document.getElementById('toggleVideo');
    btn.textContent = videoEnabled ? 'Video Off' : 'Video On';
}

// Toggle audio on/off
function toggleAudio() {
    audioEnabled = !audioEnabled;
    localStream.getAudioTracks()[0].enabled = audioEnabled;
    
    let btn = document.getElementById('toggleAudio');
    btn.textContent = audioEnabled ? 'Mute' : 'Unmute';
}

// Share screen
function shareScreen() {
    navigator.mediaDevices.getDisplayMedia({ video: true })
        .then(function(screenStream) {
            let screenTrack = screenStream.getVideoTracks()[0];
            
            connections.forEach(function(conn) {
                let sender = conn.peerConnection.getSenders().find(function(s) {
                    return s.track.kind === 'video';
                });
                if (sender) {
                    sender.replaceTrack(screenTrack);
                }
            });
            
            document.getElementById('localVideo').srcObject = screenStream;
            
            screenTrack.onended = function() {
                connections.forEach(function(conn) {
                    let sender = conn.peerConnection.getSenders().find(function(s) {
                        return s.track.kind === 'video';
                    });
                    if (sender) {
                        sender.replaceTrack(localStream.getVideoTracks()[0]);
                    }
                });
                document.getElementById('localVideo').srcObject = localStream;
            };
        })
        .catch(function(error) {
            console.log('Screen sharing failed:', error);
        });
}

// Leave call
function leaveCall() {
    connections.forEach(function(conn) {
        conn.close();
    });
    
    dataConnections.forEach(function(conn) {
        conn.close();
    });
    
    connections = [];
    dataConnections = [];
    
    let videoBoxes = document.querySelectorAll('.video-box:not(:first-child)');
    videoBoxes.forEach(function(box) {
        box.remove();
    });
    
    document.getElementById('status').textContent = 'Call ended';
}

// Canvas drawing functions
function startDrawing(e) {
    isDrawing = true;
    let rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    
    ctx.beginPath();
    ctx.moveTo(x, y);
}

function draw(e) {
    if (!isDrawing) return;
    
    let rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineTo(x, y);
    ctx.stroke();
    
    // Send drawing data to peers
    dataConnections.forEach(function(conn) {
        conn.send({
            type: 'draw',
            x: x,
            y: y,
            color: currentColor,
            size: brushSize
        });
    });
}

function stopDrawing() {
    isDrawing = false;
}

function drawRemote(data) {
    ctx.strokeStyle = data.color;
    ctx.lineWidth = data.size;
    ctx.lineCap = 'round';
    ctx.lineTo(data.x, data.y);
    ctx.stroke();
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    dataConnections.forEach(function(conn) {
        conn.send({ type: 'clear' });
    });
}

// File sharing functions
function handleFileSelect(e) {
    let file = e.target.files[0];
    if (!file) return;
    
    let reader = new FileReader();
    reader.onload = function(event) {
        let fileData = {
            type: 'file',
            name: file.name,
            size: file.size,
            data: event.target.result
        };
        
        dataConnections.forEach(function(conn) {
            conn.send(fileData);
        });
        
        addFileToList(file.name, file.size, true);
    };
    reader.readAsDataURL(file);
}

function receiveFile(fileData) {
    addFileToList(fileData.name, fileData.size, false, fileData.data);
}

function addFileToList(name, size, isSent, data) {
    let fileList = document.getElementById('fileList');
    let li = document.createElement('li');
    li.className = 'file-item';
    
    let info = document.createElement('span');
    info.textContent = name + ' (' + (size / 1024).toFixed(2) + ' KB)';
    
    let btn = document.createElement('button');
    
    if (isSent) {
        btn.textContent = 'Sent';
        btn.disabled = true;
    } else {
        btn.textContent = 'Download';
        btn.onclick = function() {
            let a = document.createElement('a');
            a.href = data;
            a.download = name;
            a.click();
        };
    }
    
    li.appendChild(info);
    li.appendChild(btn);
    fileList.appendChild(li);
}

// Tab switching
function switchTab(tabName) {
    let tabs = document.querySelectorAll('.tab');
    let tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(function(tab) {
        tab.classList.remove('active');
    });
    
    tabContents.forEach(function(content) {
        content.classList.remove('active');
    });
    
    document.querySelector('[data-tab="' + tabName + '"]').classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}