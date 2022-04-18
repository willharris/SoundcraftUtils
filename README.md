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

## View Group Numbering

In addition to the main channels, view groups can include other channels. The numbering is as follows:

- 0-23: main channels 1-24
- 24-25: line in L-R
- 26-27: player L-R
- 28-31: FX 1-4
- 32-37: subgroups 1-6
- 38-47: aux 1-10
- 48-53: vca 1-6
