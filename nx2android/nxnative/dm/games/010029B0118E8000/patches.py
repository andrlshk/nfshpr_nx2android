# Need for Speed: Hot Pursuit Remastered (010029B0118E8000): the rewriter's patches of this game's own builds. dm/tools/patch_nso.py loads every profile's patches.py and applies those of a
# module's NSO build ID; CUTS, OBS and FRAME_STEP as described there ("Registered patches"). Patches of Nintendo SDK module builds are in dm/tools/sdk_patches.py
CUTS = {
  # 1.0.3 (v196608) main: the frame limiter. The loop at main+0x483588 calls the system tick (main+0x86f070) until the frame's deadline ([x19+0x20] ticks per frame, from the frame
  # count at [x19+0x2c]) has passed, a busy spin at 30 fps. The host paces presents itself (present_interval display) and writes the engine's 60 fps frame time (hle_fpslock.c), so the
  # spin's branch back is cut, as masagrator's FPSLocker config for this build does (FPSLocker-Warehouse, patches/010029B0118E8000/799D1061182C1302.yaml)
  '799d1061182c1302e08e706b84ce76e5': [
    (0x4835a4, '2cffff54', '1f2003d5', 'frame limiter spin: b.gt main+0x483588 → nop (the host paces the frames)'),
    (0x3e00ac, '08102e1e', '08102c1e', 'physics delta time: 1/30 (0.0333s) → 1/60 (0.0166s) for 60 fps'),
    (0x7ebf2c, 'e1031f32', '21008052', 'present interval: mov w1, #2 → mov w1, #1 (60 Hz interval)'),
  ],
}

# How general each patch is and could be (dm/tools/docs_patches.py "Binding", listed in docs/agents/game-patches.md): what, its binding now, the loosest it could have (goal),
# purpose, why; blocked or kept: why the gap stays open (cannot close yet, or left open on purpose); checked: what was checked on game files (else a judgement)
BINDING = [
    {'what': 'frame limiter spin: its branch back cut', 'now': 'build', 'goal': 'game', 'purpose': 'frame rate',
     'why': "the engine's own spin limiter; a function-matched rule could carry it over the game's updates"},
]
