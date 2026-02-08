<script>
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';

	const DURATION = 10; // !! 30 !!

	let duration = DURATION;
	let timeLeft = duration;
	let progress = 100;
	let startTime = 0;
	let raf = null;
	let socket;
	let timerFinished = false;

	let promptText;

	const imageUrl =
		'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fthumbs.dreamstime.com%2Fz%2Ffunny-robot-20707154.jpg&f=1&nofb=1&ipt=f28c236b25a3a6bc466db3683090baded1b83420651d1cc9879dd05b7eb9d097';


	function tick() {
		const elapsed = (Date.now() - startTime) / 1000;
		timeLeft = Math.max(0, duration - elapsed);
		progress = Math.max(0, (timeLeft / duration) * 100);

		if (timeLeft > 0) {
			raf = requestAnimationFrame(tick);
		} else {
			progress = 0;
			timeLeft = 0;
			handleTimerFinished();
		}
	}

	function handleTimerFinished() {
		if (timerFinished) return;
		timerFinished = true;
		if (socket) {
			socket.emit('prompt-timer-finished');
		}
		const username = localStorage.getItem('username') ?? 'Someone';
		location.href = `/user-responding?user=${encodeURIComponent(username)}`;
	}

	onMount(() => {
		socket = io('http://localhost:3000');
		
		const query = new URLSearchParams(location.search);
		promptText = query.get('prompt') ?? "Unknown prompt";
		startTime = Date.now();
		raf = requestAnimationFrame(tick);
	});

	onDestroy(() => {
		if (raf) cancelAnimationFrame(raf);
		if (socket) socket.disconnect();
	});

	$: displaySeconds = Math.ceil(timeLeft);
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

<div id="content" on:keydown>
	<div id="title">Go find and use an item in your home to win!</div>

	<div class="image-wrap" aria-hidden="false">
		<img class="center-image" src={imageUrl} alt="AI" />
	</div>

	<div class="timer" aria-live="polite">{displaySeconds}s left</div>

	<div class="prompt">{promptText}</div>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=swap');
	:global(*) {
		font-family: 'Pixelify Sans', sans-serif;
		font-optical-sizing: auto;
		font-weight: 400;
		font-style: normal;
	}

	:global(html),
	:global(body) {
		height: 100%;
		margin: 0;
	}
	:global(body) {
		font-family:
			system-ui,
			-apple-system,
			'Segoe UI',
			Roboto,
			'Helvetica Neue',
			Arial;
		background: radial-gradient(ellipse at bottom, #820654 0%, #1c1c1c 100%);
		color: #fff;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
		min-height: 100vh;
		box-sizing: border-box;
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
		width: 100%;
		background: linear-gradient(90deg, #ff007f, #ff84c2);
		transform-origin: left center;
		transition: width 0.05s linear;
	}

	#content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		min-height: 100vh;
		padding: 1.5rem;
		box-sizing: border-box;
	}

	#title {
		margin-top: 1.6rem;
		color: #ffb3d8;
		font-size: clamp(1.4rem, 4vw, 2.8rem);
		font-weight: 600;
		text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
	}

	.image-wrap {
		margin: 0.8rem 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
	}

	img.center-image {
		display: block;
		width: min(44vmin, 340px);
		height: min(44vmin, 340px);
		max-width: 92%;
		max-height: calc(100vh - 280px);
		object-fit: cover;
		border-radius: 8px;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
		border: 0.25rem solid rgba(255, 255, 255, 0.04);
		background: rgba(0, 0, 0, 0.2);
	}

	.timer {
		margin-top: 0.8rem;
		font-size: clamp(1rem, 2.5vw, 1.4rem);
		color: #fff;
		padding: 0.25rem 0.6rem;
		background: rgba(0, 0, 0, 0.25);
		border-radius: 999px;
		min-width: 6.5rem;
	}

	.prompt {
		margin-top: 0.6rem;
		max-width: 90%;
		color: #ffd4ea;
		font-size: clamp(0.9rem, 2vw, 1.05rem);
		line-height: 1.35;
		padding: 0.6rem 1rem;
		background: rgba(255, 255, 255, 0.03);
		border-radius: 6px;
	}
</style>
