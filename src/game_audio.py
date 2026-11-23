"""화면별 배경음악과 전투 효과음."""

from pathlib import Path

import pico2d as p
from pico2d import pico2d as canvas


class GameAudio:
    def __init__(self):
        self.tracks = {}
        self.effects = {}
        self.current_track = None
        if not canvas.audio_on:
            return

        folder = Path(__file__).resolve().parents[1] / 'assets/audio'
        for name in ('menu', 'chapter1', 'chapter2', 'chapter3', 'upgrades', 'instructions', 'training'):
            self.tracks[name] = p.load_music(str(folder / f'{name}.ogg'))
        volumes = {
            'hit': 64, 'hurt': 80, 'burst': 70, 'burst_miss': 44,
            'jump': 48, 'roll': 52, 'pickup': 58,
            'card_move': 43, 'card_confirm': 60,
            'reroll_common': 54, 'reroll_rare': 63, 'reroll_legendary': 72,
            'crossbow_draw': 53, 'heavy_inhale': 69, 'tower_collapse': 78,
        }
        for name, volume in volumes.items():
            effect = p.load_wav(str(folder / f'{name}.wav'))
            effect.set_volume(volume)
            self.effects[name] = effect

    def play_screen(self, screen):
        track = self.tracks.get(screen)
        if track is self.current_track:
            return
        if self.current_track is not None:
            self.current_track.stop()
        self.current_track = track
        if track is not None:
            track.set_volume(28 if screen == 'instructions' else 36)
            track.repeat_play()

    def play_effect(self, name):
        effect = self.effects.get(name)
        if effect is not None:
            effect.play()
