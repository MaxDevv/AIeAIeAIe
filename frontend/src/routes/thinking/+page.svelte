<script>
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';

	const imageUrl =
		'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fthumbs.dreamstime.com%2Fz%2Ffunny-robot-20707154.jpg&f=1&nofb=1&ipt=f28c236b25a3a6bc466db3683090baded1b83420651d1cc9879dd05b7eb9d097';

	let socket;
	let statusText = 'Thinking...';

	onMount(() => {
		socket = io('http://localhost:3000');

		socket.on('connect', () => {
			console.log('Connected to server on thinking page');
		});

		socket.on('ai-processing-complete', (data) => {
			console.log('AI processing complete:', data);
			statusText = 'Done!';
			const simulation = encodeURIComponent(data.simulation || 'The AI ponders your actions...');
			const newPrompt = encodeURIComponent(data.new_prompt);
			window.location.href = `/ai-response?response=${simulation}&prompt=${newPrompt}`;
		});
	});

	onDestroy(() => {
		if (socket) socket.disconnect();
	});
</script>

<div id="content">
	<div id="title">{statusText}</div>

	<div class="image-wrap">
		<img class="center-image" src={imageUrl} alt="Thinking robot" />
	</div>
</div>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=swap');

	:global(*) {
		font-family: 'Pixelify Sans', sans-serif;
	}

	:global(html),
	:global(body) {
		height: 100%;
		margin: 0;
	}

	:global(body) {
		background: radial-gradient(ellipse at bottom, #820654 0%, #1c1c1c 100%);
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}

	#content {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: 1.5rem;
	}

	#title {
		margin-bottom: 1rem;
		color: #ffb3d8;
		font-size: clamp(1.6rem, 4vw, 3rem);
		font-weight: 600;
		text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
	}

	.image-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	img.center-image {
		width: min(44vmin, 340px);
		height: min(44vmin, 340px);
		object-fit: cover;
		border-radius: 8px;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
		border: 0.25rem solid rgba(255, 255, 255, 0.04);
		background: rgba(0, 0, 0, 0.2);
	}
</style>
