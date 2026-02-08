
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/ai-response" | "/party" | "/prompt" | "/thinking" | "/user-responding" | "/welcome";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/ai-response": Record<string, never>;
			"/party": Record<string, never>;
			"/prompt": Record<string, never>;
			"/thinking": Record<string, never>;
			"/user-responding": Record<string, never>;
			"/welcome": Record<string, never>
		};
		Pathname(): "/" | "/ai-response" | "/ai-response/" | "/party" | "/party/" | "/prompt" | "/prompt/" | "/thinking" | "/thinking/" | "/user-responding" | "/user-responding/" | "/welcome" | "/welcome/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/robots.txt" | string & {};
	}
}