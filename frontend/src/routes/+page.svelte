<script>
	import Presenting from './presenting.svelte';
	import { onMount, onDestroy } from 'svelte';

	onMount(() => {
		location.href = '/welcome';
	});
</script>

<Presenting />
