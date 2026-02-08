<script>
	import { onMount, onDestroy } from 'svelte';
	import { io } from 'socket.io-client';

	const imageUrl =
		'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fthumbs.dreamstime.com%2Fz%2Ffunny-robot-20707154.jpg&f=1&nofb=1&ipt=f28c236b25a3a6bc466db3683090baded1b83420651d1cc9879dd05b7eb9d097';

	export let robotText;
	export let newPrompt;

	let display = '';
	let aborted = false;
	let reducedMotion = false;
	let socket;
	let canProceed = false;

	function rand(min, max) {
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	async function typeOnce(text) {
		if (reducedMotion) {
			display = text;
			canProceed = true;
			return;
		}

		display = "";
		for (let i = 0; i < text.length && !aborted; i++) {
			const ch = text[i];
			display += ch;

			let delay;
			if (ch === " ") delay = rand(20, 60);
			else if (/[.,;:!?…]/.test(ch)) delay = rand(200, 420);
			else delay = rand(35, 80);

			if (Math.random() < 0.03) {
				await new Promise((r) => setTimeout(r, rand(80, 160)));
			}

			await new Promise((r) => setTimeout(r, delay));
		}
		canProceed = true;
	}

	function handleNext() {
		if (socket) {
			socket.emit('ai-response-read');
		}
		if (newPrompt) {
			const encodedPrompt = encodeURIComponent(newPrompt);
			window.location.href = `/prompt?prompt=${encodedPrompt}`;
		} else {
			window.location.href = '/prompt';
		}
	}

	onMount(() => {
		socket = io('http://localhost:3000');

		const query = new URLSearchParams(location.search);
		robotText = query.get('response') ?? "Unknown response";
		newPrompt = query.get('prompt') ?? "";
		reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		
		aborted = false;
		typeOnce(robotText).catch(() => {});
	});

	onDestroy(() => {
		aborted = true;
		if (socket) socket.disconnect();
	});
</script>

<main id="wrap" aria-live="polite">
	<img class="robot-image" src={imageUrl} alt="Friendly robot" />

	<div class="typed-wrap" role="status" aria-atomic="true">
		<span class="typed">{display}</span>
	</div>
	
	<button 
		on:click={handleNext} 
		disabled={!canProceed}
		class:visible={canProceed}
		class="next-button"
	>
		Next
	</button>
</main>

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

	#wrap {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 2rem;
		box-sizing: border-box;
		text-align: center;
		gap: 1rem;
	}

	.robot-image {
		width: min(44vmin, 340px);
		height: min(44vmin, 340px);
		max-width: 92%;
		max-height: calc(100vh - 200px);
		object-fit: cover;
		border-radius: 8px;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
		border: 0.25rem solid rgba(255, 255, 255, 0.04);
		background: rgba(0, 0, 0, 0.18);
	}

	.typed-wrap {
		margin-top: 1rem;
		max-width: 90%;
		min-height: 2rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.45rem 0.85rem;
		background: rgba(255, 255, 255, 0.03);
		border-radius: 8px;
		font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, 'Courier New', monospace;
		color: #dfe7ff;
		font-size: clamp(0.95rem, 2.2vw, 1.05rem);
		line-height: 1.35;
	}

	.typed {
		white-space: pre-wrap;
		word-break: break-word;
	}

	.next-button {
		padding: 0.75rem 2rem;
		font-size: clamp(1rem, 2.5vw, 1.4rem);
		background: #ff007f;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		opacity: 0;
		pointer-events: none;
	}

	.next-button.visible {
		opacity: 1;
		pointer-events: auto;
	}

	.next-button:hover {
		background: #ff84c2;
		transform: scale(1.05);
	}

	.next-button:disabled {
		background: #666;
		cursor: not-allowed;
		transform: none;
	}
</style>
