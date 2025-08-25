'use client';

import { useEffect } from 'react';

const TEXT_INPUT_TYPES = new Set<string>([
	'text',
	'search',
	'email',
	'password',
	'tel',
	'url',
	'number',
	'date',
	'datetime-local',
	'month',
	'time',
	'week',
]);

function isTextEntryElement(el: Element): el is HTMLInputElement | HTMLTextAreaElement {
	if (el instanceof HTMLTextAreaElement) return true;
	if (el instanceof HTMLInputElement) {
		const rawType = el.getAttribute('type');
		const type = (rawType ? rawType : 'text').toLowerCase();
		return TEXT_INPUT_TYPES.has(type) || rawType === null; // default input is text
	}
	return false;
}

function applyReadOnly(el: HTMLInputElement | HTMLTextAreaElement) {
	// opt-out: allow specific inputs if needed by adding data-allow-input attribute
	if (el.hasAttribute('data-allow-input')) return;
	// Do not toggle disabled; only prevent typing
	el.readOnly = true;
}

export default function InputBlocker() {
	useEffect(() => {
		const handleKeyDown = (event: KeyboardEvent) => {
			const target = event.target as Element | null;
			if (!target) return;
			if (isTextEntryElement(target) && !(target as HTMLElement).hasAttribute('data-allow-input')) {
				const allowedKeys = new Set<string>([
					'Tab',
					'Shift',
					'Control',
					'Alt',
					'Meta',
					'ArrowLeft',
					'ArrowRight',
					'ArrowUp',
					'ArrowDown',
					'Home',
					'End',
					'PageUp',
					'PageDown',
					'Escape',
				]);
				if (!allowedKeys.has(event.key)) {
					event.preventDefault();
				}
			}
		};

		const initialize = (root: ParentNode) => {
			const nodes = root.querySelectorAll('input, textarea');
			nodes.forEach((node) => {
				if (isTextEntryElement(node)) applyReadOnly(node);
			});
		};

		initialize(document);

		const observer = new MutationObserver((mutations) => {
			for (const mutation of mutations) {
				mutation.addedNodes.forEach((n) => {
					if (n instanceof Element) {
						if (isTextEntryElement(n)) {
							applyReadOnly(n);
						} else {
							initialize(n);
						}
					}
				});
			}
		});

		observer.observe(document.documentElement, {
			childList: true,
			subtree: true,
		});

		document.addEventListener('keydown', handleKeyDown, true);
		return () => {
			observer.disconnect();
			document.removeEventListener('keydown', handleKeyDown, true);
		};
	}, []);

	return null;
}


