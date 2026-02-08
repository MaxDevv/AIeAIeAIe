<script>
  import Peer from 'peerjs';
  import { io } from 'socket.io-client';
  import { onMount, onDestroy } from 'svelte';
  
  let peer;
  let socket;
  let myStream;
  let mediaRecorder;
  let recordedChunks = [];
  let isPresenting = false;
  let videoElement;
  let activeCalls = [];
  let myUserId;
  let isMyTurn = false;
  
  onMount(() => {
    myUserId = localStorage.getItem('userId') ?? crypto.randomUUID();
    localStorage.setItem('userId', myUserId);

    socket = io('http://localhost:3000');
    peer = new Peer();
    
    peer.on('open', (id) => {
      socket.emit('add-peer', { userId: myUserId, peerId: id });
    });
    
    peer.on('call', (call) => {
      call.answer();
      
      let streamSet = false;
      call.on('stream', (remoteStream) => {
        if (streamSet) return;
        streamSet = true;
        
        if (videoElement) {
          videoElement.srcObject = remoteStream;
          videoElement.muted = false;
          videoElement.play().catch(() => {});
        }
      });
    });
    socket.on('next-presenter', (data) => {
      if (data.userId === myUserId) {
        isMyTurn = true;
        startStreaming();
      } else {
        isMyTurn = false;
        if (isPresenting) {
          stopPresenting();
        }
      }
    });
    
    socket.on('user-presenting', (peerId) => {
      if (peerId !== peer.id && isPresenting) {
        stopPresenting();
      }
    });
    
    socket.on('all-peers', (peers) => {
      if (!isPresenting || !myStream) return;
      
      peers.forEach(remotePeer => {
        const remotePeerId = remotePeer.peerId;
        if (remotePeerId && remotePeerId !== peer.id) {
          const call = peer.call(remotePeerId, myStream);
          activeCalls.push(call);
        }
      });
    });
    socket.on('all-users-responded', () => {
      if (isPresenting) {
        stopPresenting();
      }
    });
  });
  
  onDestroy(() => {
    if (myStream) {
      myStream.getTracks().forEach(track => track.stop());
    }
    if (socket) socket.disconnect();
    if (peer) peer.destroy();
  });

  async function startStreaming() {
    try {
      myStream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });
      
      isPresenting = true;
      
      if (videoElement) {
        videoElement.srcObject = myStream;
        videoElement.muted = true;
        videoElement.play();
      }
      
      mediaRecorder = new MediaRecorder(myStream);
      recordedChunks = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
      };
      
      mediaRecorder.onstop = uploadRecording;
      mediaRecorder.start(1000);
      
      socket.emit('start-presenting', { peerId: peer.id });
      socket.emit('get-all-peers');
      
    } catch (err) {
      console.error('Could not access camera/microphone:', err);
      alert('Could not access camera/microphone');
    }
  }
  
  function stopPresenting() {
    if (!isPresenting) return;
    
    isPresenting = false;
    
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    
    if (myStream) {
      myStream.getTracks().forEach(track => track.stop());
      myStream = null;
    }
    
    activeCalls.forEach(call => call.close());
    activeCalls = [];
    
    if (videoElement) {
      videoElement.srcObject = null;
    }
    
    socket.emit('stop-presenting');
    socket.emit('user-finished-responding', { userId: myUserId });
  }
  
  async function uploadRecording() {
    if (recordedChunks.length === 0) return;
    const username = localStorage.getItem('username') ?? 'Unknown';
    
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
    const formData = new FormData();
    formData.append('video', blob, `presentation-${Date.now()}.webm`);
    formData.append('username', username);
    
    try {
      const response = await fetch('http://localhost:3000/upload', {
        method: 'POST',
        body: formData
      });
      const result = await response.json();
      console.log('Upload result:', result);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  }
</script>

<video 
  bind:this={videoElement} 
  autoplay 
  playsinline
  style="width: 100%; background: black;"
></video>

{#if !isPresenting}
  <button on:click={startStreaming}>Start Streaming</button>
{:else}
  <button on:click={stopPresenting}>Stop Streaming</button>
{/if}

{#if isMyTurn}
  <div class="status">It's your turn to present!</div>
{/if}

<style>
  .status {
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: #ff007f;
    color: white;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: bold;
    animation: pulse 1s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
</style>
