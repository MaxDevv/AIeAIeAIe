<script>
	import { onMount } from 'svelte';
	import { io } from 'socket.io-client';

	export let initialUsers = [];

	let users = [...initialUsers];
	let userId, username;
	let socket = io('http://localhost:3000');
	export function addUser(username) {
		if (!username || typeof username !== 'string') return;
		const name = username.trim();
		if (!name) return;

		if (users.includes(name)) return;
		users = [...users, name];
	}

	export function removeUser(username) {
		users = users.filter((u) => u !== username);
	}

	export function getUsers() {
		return users.slice();
	}

	export function startGame() {
		socket.emit("start-game");
	}

	onMount(() => {
		const query = new URLSearchParams(location.search);
		username = query.get('username') ?? `Guest-${Math.floor(Math.random() * 1_000_000)}`;
		userId = localStorage.getItem('userId') ?? crypto.randomUUID();
		localStorage.setItem('userId', userId);
		localStorage.setItem('username', username);  // Store username for later use
		console.log(userId);
		socket.emit('join-room', { username: username, userId: userId });
		socket.on("all-peers", (data) => {
			for (const user of data) {
				if (user?.username) addUser(user.username);
			}
		});
		socket.on("starting-game", (prompt) => {
			location.href = `/prompt?prompt=${encodeURIComponent(prompt)}`;
		});
		addUser(username);
	});
</script>

<div class="party" role="region" aria-label="Party users">
	<div id="title">Party</div>
	<div class="tags" aria-live="polite">
		{#each users as user (user)}
			<div class="tag" title={user}>{user}</div>
		{/each}
	</div>
	<button id="start" on:click={() => startGame()}>Start Game</button>
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

	:global(#title) {
		color: #ff007f;
		font-size: 5vw;
		display: block;
		width: 100%;
		text-align: center;
		margin-bottom: 1.5rem;
	}

	:global(#content) {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		min-height: 100vh;
		box-sizing: border-box;
	}

	:global(#start) {
		border: 0.125vw solid #911c56;
		border-radius: 0.5vw;
		background-color: #ff007f;
		color: #ffffff;
		width: 10vw;
		height: 2.5vw;
		transition: background-color 0.125s ease-out;
		font-size: 1vw;
	}
	:global(#start):hover {
		background-color: #ff84c2;
        cursor: pointer;
	}

	.party {
		min-height: 100vh;
		box-sizing: border-box;
		padding: 20px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
		background: radial-gradient(ellipse at bottom, #820654 0%, #1c1c1c 100%);
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
		max-width: 100%;
		justify-content: center;
		align-items: center;
	}

	.tag {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 1vw 2vw;
		border-radius: 1vw;
		background: rgba(255, 255, 255, 0.06);
		color: #fff;
		font-size: 2vw;
		letter-spacing: 0.2px;
		box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
		white-space: nowrap;
		user-select: none;
	}
</style>
