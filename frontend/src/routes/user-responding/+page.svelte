<script>
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';
	import Peer from 'peerjs';

	const DURATION = 30;

	let duration = DURATION;
	let timeLeft = duration;
	let progress = 100;
	let startTime = 0;
	let raf = null;

	let socket;
	let peer;
	let myUserId;
	let myPeerId;
	
	let currentPresenter = null;
	let isMyTurn = false;
	let myStream = null;
	let mediaRecorder;
	let recordedChunks = [];
	let videoElement;
	let activeCalls = [];
	let isPresenting = false;
	function log(msg, data) {
		const line = data ? `[USER-RESPONDING] ${msg}: ${JSON.stringify(data)}` : `[USER-RESPONDING] ${msg}`;
		console.log(line);
	}

	function tick() {
		const elapsed = (Date.now() - startTime) / 1000;
		timeLeft = Math.max(0, duration - elapsed);
		progress = Math.max(0, (timeLeft / duration) * 100);

		if (timeLeft > 0) {
			raf = requestAnimationFrame(tick);
		} else {
			progress = 0;
			timeLeft = 0;
		}
	}

	function resetTimer() {
		if (typeof window === 'undefined') return;
		if (raf) cancelAnimationFrame(raf);
		startTime = Date.now();
		timeLeft = duration;
		progress = 100;
		raf = requestAnimationFrame(tick);
	}

	onMount(() => {
		log('onMount called');
		myUserId = localStorage.getItem('userId') ?? crypto.randomUUID();
		localStorage.setItem('userId', myUserId);
		const urlParams = new URLSearchParams(window.location.search);
		const username = urlParams.get('user') ?? 'Someone';
		log('User info', { myUserId, username });
		socket = io('http://localhost:3000');
		log('Socket created');
		peer = new Peer();
		log('Peer created');

		peer.on('open', (id) => {
			myPeerId = id;
			log('Peer opened', { myPeerId });
			socket.emit('add-peer', { userId: myUserId, peerId: id, username: username });
			log('Sent add-peer');
		});
		
		peer.on('error', (err) => {
			log('Peer error', err);
		});
		peer.on('call', (call) => {
			log('Incoming call received');
			
			// If it's my turn to present, I should NOT answer incoming calls
			// The viewers should receive MY stream, not the other way around
			if (isMyTurn) {
				log('Ignoring incoming call - I am the presenter');
				// Close the incoming call politely
				try { call.close(); } catch(e) {}
				return;
			}
			
			try {
				log('Answering call as viewer');
				call.answer();
				
				let streamSet = false;
				call.on('stream', (remoteStream) => {
					if (streamSet) return;
					streamSet = true;
					log('Remote stream received', { hasVideo: remoteStream.getVideoTracks().length > 0 });
					if (videoElement) {
						log('Setting remote stream to video element');
						videoElement.srcObject = remoteStream;
						videoElement.muted = false;
						videoElement.play().then(() => {
							log('Remote video playing');
						}).catch((e) => {
							log('Error playing remote video', e.message);
						});
					}
				});
				
				call.on('error', (err) => {
					log('Call error', err.message);
				});
				
				call.on('close', () => {
					log('Call closed');
				});
				
				activeCalls.push(call);
			} catch (e) {
				log('Error answering call', e.message);
			}
		});
		socket.on('next-presenter', async (data) => {
			log('Received next-presenter', data);
			log('My userId', myUserId);
			
			const wasMyTurn = isMyTurn;
			const newIsMyTurn = data.userId === myUserId;
			if (wasMyTurn && !newIsMyTurn && isPresenting && mediaRecorder) {
				log('Switching away from me - stopping recording');
				if (mediaRecorder.state !== 'inactive') {
					mediaRecorder.stop();
					log('Waiting for upload...');
					await new Promise(r => setTimeout(r, 2000));
					log('Upload wait complete');
				}
			}
			
			currentPresenter = data;
			isMyTurn = newIsMyTurn;
			log('Is my turn', isMyTurn);
			
			resetTimer();
			if (myStream) {
				myStream.getTracks().forEach(track => track.stop());
				myStream = null;
			}
			activeCalls.forEach(call => call.close());
			activeCalls = [];
			isPresenting = false;

			if (isMyTurn) {
				log('Starting to present');
				await startStreaming();
			} else {
				log('Waiting for others to present');
				if (videoElement) {
					videoElement.srcObject = null;
				}
			}
		});
		socket.on('all-users-responded', async () => {
			log('All users responded');
			if (raf) cancelAnimationFrame(raf);
			timeLeft = 0;
			progress = 0;
			if (isMyTurn && isPresenting && mediaRecorder) {
				log('Stopping final recording for upload');
				if (mediaRecorder.state !== 'inactive') {
					mediaRecorder.stop();
					log('Waiting for upload to complete...');
					await new Promise(r => setTimeout(r, 3000));
				}
			}
			
			log('Navigating to thinking page');
			window.location.href = '/thinking';
		});
		socket.on('all-peers', (peers) => {
			log('Received all-peers', { isPresenting, hasStream: !!myStream, peerCount: peers?.length });
			if (!isPresenting || !myStream) {
				log('Not calling peers - not presenting or no stream');
				return;
			}
			
			log('Peer list:', peers.map(p => ({ id: p.userId, peerId: p.peerId, name: p.username })));
			
			let callCount = 0;
			peers.forEach(remotePeer => {
				const remotePeerId = remotePeer.peerId;
				if (remotePeerId && remotePeerId !== myPeerId) {
					log('Calling peer', { remotePeerId, username: remotePeer.username });
					try {
						const call = peer.call(remotePeerId, myStream);
						if (call) {
							activeCalls.push(call);
							callCount++;
							log('Call initiated successfully');
						}
					} catch (e) {
						log('Error calling peer', e.message);
					}
				} else {
					log('Skipping peer (no peerId or is me)', { remotePeerId, myPeerId, username: remotePeer.username });
				}
			});
			log(`Called ${callCount} peers`);
		});
		socket.on('connect', () => {
			log('Socket connected');
			socket.emit('join-room', { userId: myUserId, username: username });
			log('Sent join-room');
			socket.emit('get-current-presenter');
			log('Sent get-current-presenter');
		});
		startTime = Date.now();
		raf = requestAnimationFrame(tick);
	});

	onDestroy(() => {
		log('onDestroy');
		if (raf) cancelAnimationFrame(raf);
		stopPresenting();
		if (socket) socket.disconnect();
		if (peer) peer.destroy();
	});

	async function startStreaming() {
		log('startStreaming called');
		if (typeof window === 'undefined') {
			log('Window undefined, cannot start');
			return;
		}
		
		try {
			log('Requesting media devices...');
			myStream = await navigator.mediaDevices.getUserMedia({ 
				video: true, 
				audio: true 
			});
			log('Got media stream', { tracks: myStream.getTracks().length });
			
			isPresenting = true;
			
			if (videoElement) {
				videoElement.srcObject = myStream;
				videoElement.muted = true;
				videoElement.play();
				log('Video element playing');
			}
			recordedChunks = [];
			log('Cleared recorded chunks');
			const mimeType = MediaRecorder.isTypeSupported('video/webm') 
				? 'video/webm' 
				: MediaRecorder.isTypeSupported('video/mp4') 
					? 'video/mp4' 
					: '';
			
			log('Using mimeType', { mimeType });
			
			const options = mimeType ? { mimeType } : {};
			mediaRecorder = new MediaRecorder(myStream, options);
			log('MediaRecorder created', { mimeType: mediaRecorder.mimeType, state: mediaRecorder.state });
			
			mediaRecorder.ondataavailable = (e) => {
				log(`Data available: ${e.data.size} bytes`);
				if (e.data.size > 0) {
					recordedChunks.push(e.data);
				}
			};
			
			mediaRecorder.onstop = () => {
				log('MediaRecorder stopped, calling uploadRecording');
				uploadRecording();
			};
			
			mediaRecorder.onerror = (e) => {
				log('MediaRecorder error', e.message);
			};
			await new Promise(r => setTimeout(r, 100));
			
			if (mediaRecorder.state === 'inactive') {
				mediaRecorder.start(1000);
				log('MediaRecorder started successfully');
			} else {
				log('MediaRecorder already in state:', mediaRecorder.state);
			}
			socket.emit('start-presenting', { peerId: myPeerId, userId: myUserId });
			socket.emit('get-all-peers');
			
		} catch (err) {
			log('Could not access camera/microphone', err.message);
			console.error(err);
			alert('Could not access camera/microphone: ' + err.message);
		}
	}

	function stopPresenting() {
		log('stopPresenting');
		isPresenting = false;
		
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			log('Stopping mediaRecorder');
			mediaRecorder.stop();
		}
		
		if (myStream) {
			log('Stopping stream tracks');
			myStream.getTracks().forEach(track => track.stop());
			myStream = null;
		}
		
		activeCalls.forEach(call => call.close());
		activeCalls = [];
		
		if (videoElement) {
			videoElement.srcObject = null;
		}
		
		if (socket) {
			socket.emit('stop-presenting');
		}
	}

	async function uploadRecording() {
		log('uploadRecording called');
		if (typeof window === 'undefined') {
			log('Window undefined, cannot upload');
			return;
		}
		if (recordedChunks.length === 0) {
			log('No recorded chunks to upload!');
			return;
		}
		
		log(`Uploading ${recordedChunks.length} chunks`);
		const urlParams = new URLSearchParams(window.location.search);
		const username = urlParams.get('user') ?? 'Someone';
		
		const blob = new Blob(recordedChunks, { type: 'video/webm' });
		log(`Blob created: ${blob.size} bytes`);
		
		const formData = new FormData();
		formData.append('video', blob, `presentation-${Date.now()}.webm`);
		formData.append('username', username);
		log('FormData created with fields: video, username', { username });
		
		try {
			log('Sending fetch request to /upload...');
			const response = await fetch('http://localhost:3000/upload', {
				method: 'POST',
				body: formData
			});
			log(`Upload response status: ${response.status}`);
			const result = await response.json();
			log('Upload result', result);
		} catch (err) {
			log('Upload failed', err.message);
			console.error(err);
		}
	}
	$: displaySeconds = typeof window !== 'undefined' ? Math.ceil(timeLeft) : 30;
	$: displayUsername = currentPresenter?.username ?? 'Someone';
	$: statusText = isMyTurn ? 'You are responding!' : `${displayUsername} is responding!`;
</script>

<div
	class="top-bar"
	role="progressbar"
	aria-label="Time remaining"
	aria-valuemin="0"
	aria-valuemax={duration}
	aria-valuenow={Math.round(timeLeft)}
>
	<div class="fill" style="width: {progress}%;"></div>
</div>

<div class="wrap">
	<div class="content">
		<div class="title">{statusText}</div>

		{#if isMyTurn}
			<div class="status-badge presenting">Presenting</div>
		{/if}

		<div class="card">
			<video
				bind:this={videoElement}
				autoplay
				playsinline
				class="video-stream"
			></video>
		</div>

		<div class="timer">{displaySeconds}s left</div>
	</div>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=swap');

	:global(html),
	:global(body) {
		margin: 0;
		padding: 0;
		height: 100%;
		font-family: 'Pixelify Sans', sans-serif;
		background: radial-gradient(ellipse at bottom, #820654 0%, #1c1c1c 100%);
		color: #fff;
	}
	.top-bar {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 0.9rem;
		background: rgba(255, 255, 255, 0.08);
		overflow: hidden;
		z-index: 20;
	}

	.top-bar .fill {
		height: 100%;
		background: linear-gradient(90deg, #ff007f, #ff84c2);
		transition: width 0.05s linear;
	}

	.wrap {
		height: 100vh;
		padding: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
	}

	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.8rem;
	}

	.title {
		margin-top: 1.6rem;
		color: #ffb3d8;
		font-size: clamp(1.3rem, 4vw, 2.4rem);
		font-weight: 600;
		text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
	}

	.status-badge {
		padding: 0.4rem 1rem;
		border-radius: 999px;
		font-size: clamp(0.9rem, 2vw, 1.2rem);
		font-weight: 600;
	}

	.status-badge.presenting {
		background: #ff007f;
		color: white;
		animation: pulse 1.5s infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	.card {
		width: clamp(220px, 60vw, 480px);
		aspect-ratio: 1 / 1;
		overflow: hidden;
		border-radius: 8px;
		box-shadow: 0 8px 28px rgba(0, 0, 0, 0.5);
		background: linear-gradient(
			180deg,
			rgba(255, 255, 255, 0.02),
			rgba(0, 0, 0, 0.04)
		);
	}

	.video-stream {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
		background: black;
	}

	.timer {
		font-size: clamp(1rem, 2.5vw, 1.4rem);
		padding: 0.25rem 0.6rem;
		background: rgba(0, 0, 0, 0.25);
		border-radius: 999px;
		min-width: 6.5rem;
		text-align: center;
	}
</style>
