import { describe, it, expect, vi } from 'vitest';
import { audioPlayer } from './audio-player.js';

describe('audioPlayer', () => {
    it('starts with repeat off', () => {
        const player = audioPlayer();
        expect(player.repeat).toBe(false);
    });

    it('toggleRepeat turns repeat on', () => {
        const player = audioPlayer();
        player.toggleRepeat();
        expect(player.repeat).toBe(true);
    });

    it('toggleRepeat turns repeat off again', () => {
        const player = audioPlayer();
        player.toggleRepeat();
        player.toggleRepeat();
        expect(player.repeat).toBe(false);
    });

    it('onEnded restarts audio when repeat is on', () => {
        const player = audioPlayer();
        player.repeat = true;
        const audio = { currentTime: 30, play: vi.fn() };
        player.onEnded(audio);
        expect(audio.currentTime).toBe(0);
        expect(audio.play).toHaveBeenCalledOnce();
    });

    it('onEnded does nothing when repeat is off', () => {
        const player = audioPlayer();
        const audio = { currentTime: 30, play: vi.fn() };
        player.onEnded(audio);
        expect(audio.play).not.toHaveBeenCalled();
    });
});
