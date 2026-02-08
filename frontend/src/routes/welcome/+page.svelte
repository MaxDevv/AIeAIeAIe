<script>
    function startGame() {
        let username = `Guest-${Math.floor(Math.random() * 1_000_000)}`;
        const candidate = prompt("Enter a username!", username);
        username = candidate ? candidate : username;
		location.href = `/party?username=${encodeURIComponent(username)}`;
    }
</script>

<div id="content">
	<div id="title">Welcome to AIeAIeAIe!</div>
	<button id="start" on:click={() => startGame()}>Join Game</button>
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
		margin: 0;
		padding: 0;
		height: 100%;
	}

	:global(body) {
		background: radial-gradient(ellipse at bottom, #820654 0%, #1c1c1c 100%);
		background-attachment: fixed;
		min-height: 100vh;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
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

	:global(#title) {
		color: #ff007f;
		font-size: 5vw;
	}
	:global(#start) {
		border: 0.125vw solid #911c56;
		border-radius: 1vw;
		background-color: #ff007f;
		color: #ffffff;
		width: 20vw;
		height: 5vw;
		transition: background-color 0.125s ease-out;
		font-size: 1.5vw;
	}
	:global(#start):hover {
		background-color: #ff84c2;
        cursor: pointer;
	}
</style>