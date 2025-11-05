import random, os, subprocess
from midiutil import MIDIFile

# ===== コード進行パターン =====
chord_progressions = {
    "王道進行": [[60,64,67], [67,71,74], [69,72,76], [65,69,72]],
    "カノン進行": [[60,64,67], [67,71,74], [69,72,76], [64,67,71],
                   [65,69,72], [60,64,67], [65,69,72], [67,71,74]],
    "循環進行": [[60,64,67], [69,72,76], [62,65,69], [67,71,74]],
    "小室進行": [[69,72,76], [65,69,72], [67,71,74], [60,64,67]],
    "ロック進行": [[60,64,67], [65,69,72], [67,71,74], [60,64,67]],
    "哀愁進行": [[69,72,76], [65,69,72], [60,64,67], [67,71,74]],
    "Ⅱ-Ⅴ-Ⅰ": [[62,65,69,72], [67,71,74,77], [60,64,67,71]],
    "モーダル進行": [[60,64,67,71], [62,65,69,72], [64,67,71,74], [65,69,72,76]]
}

# ===== 楽器候補 =====
chord_instruments = [
    "Acoustic Grand Piano", "Electric Piano 1", "Electric Guitar (clean)",
    "Acoustic Guitar (steel)", "String Ensemble 1", "Pad 1 (new age)"
]

melody_instruments = [
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Flute", "Violin",
    "Synth Brass 1", "Pad 8 (sweep)"
]

instrument_to_number = {name: i for i, name in enumerate(chord_instruments + melody_instruments)}

# ===== MIDI生成関数 =====
def generate_random_loop(output_path="temp_audio/random_loop.wav"):
    # 進行選択
    progression_name = random.choice(list(chord_progressions.keys()) + ["無音"])
    print(f"選択進行: {progression_name}")

    # 楽器選択
    chord_inst = random.choice(chord_instruments)
    melody_inst = random.choice(melody_instruments)
    while melody_inst == chord_inst:
        melody_inst = random.choice(melody_instruments)

    midi = MIDIFile(2)
    bpm = 100
    midi.addTempo(0, 0, bpm)
    midi.addTempo(1, 0, bpm)

    midi.addProgramChange(0, 0, 0, instrument_to_number[chord_inst])
    midi.addProgramChange(1, 1, 0, instrument_to_number[melody_inst])

    # コード進行
    if progression_name != "無音":
        pattern = chord_progressions[progression_name]
        chords = (pattern * 2)[:8]
    else:
        chords = [[] for _ in range(8)]

    # コード書き込み
    for i, chord in enumerate(chords):
        for note in chord:
            midi.addNote(0, 0, note, i*2, 2, 80)

    # メロディ書き込み
    scale = [0, 2, 4, 5, 7, 9, 11, 12]
    for bar in range(8):
        for beat in range(4):
            pitch = 60 + random.choice(scale)
            dur = random.choice([0.5, 1])
            vel = random.randint(70,110)
            midi.addNote(1, 1, pitch, bar*2 + beat*0.5, dur, vel)

    # MIDI保存
    mid_path = output_path.replace(".wav", ".mid")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(mid_path, "wb") as f:
        midi.writeFile(f)

    # ===== FluidSynth で音声化 =====
    soundfont = "soundfonts/GeneralUser.sf2"  # ここにsf2ファイルを置く
    cmd = [
        "fluidsynth", "-ni", soundfont, mid_path, "-F", output_path, "-r", "44100"
    ]
    subprocess.run(cmd, check=True)

    return {
        "file": output_path,
        "progression": progression_name,
        "chord_inst": chord_inst,
        "melody_inst": melody_inst
    }
