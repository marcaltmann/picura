export function audioPlayer() {
    return {
        repeat: false,

        toggleRepeat() {
            this.repeat = !this.repeat;
        },

        onEnded(audio) {
            if (this.repeat) {
                audio.currentTime = 0;
                audio.play();
            }
        },
    };
}
