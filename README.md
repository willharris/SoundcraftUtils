# Soundcraft Mixer Utilities

This repo contains tools I use to help me work with my Soundcraft Ui24r mixer.

Currently the only real utility is to move around input channels.

## Usage

`mixer.py <config.json>`

## JSON elements

The following documents my reverse-engineered understanding of the mixer's config.json file.

- a: aux chanel
- casc: cascade
- f: fx channel
- hw: hw gain channel (gain page)
- i: input channel
- l: line input
- m: master output
- mg: mute group
- mtk: multi-track
- mtx: matrix sends
- p: audio player
- s: subgroup
- v: vca
- vg: view group
