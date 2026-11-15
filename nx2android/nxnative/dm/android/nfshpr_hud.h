#pragma once
#include <stdint.h>

enum {
    HUD_LAYER_COP = 0,
    HUD_LAYER_RACER = 1,
    HUD_LAYER_MENU = 2,
    HUD_LAYER_COUNT = 3
};

enum {
    HUD_KIND_BTN = 0,
    HUD_KIND_STEER_L = 1,
    HUD_KIND_STEER_R = 2,
    HUD_KIND_STEER_STICK = 3,
    HUD_KIND_LAYER = 4,
    HUD_KIND_STICK_R = 5
};

#define HUD_MAX_BTNS 32

typedef struct {
    char id[24];
    char label[16];
    float x, y;    // centre in [0..1] of window W, H
    float w, h;    // size in design units / 360.0f (relative to window H)
    uint64_t btn;  // DM_BTN_*
    int kind;      // HUD_KIND_*
    int racer;     // 0 = police/blue accent, 1 = racer/orange accent
} hud_btn_t;

enum {
    DM_HUD_ST_READY      = 1ULL << 0,
    DM_HUD_ST_LOADED     = 1ULL << 1,
    DM_HUD_ST_COP        = 1ULL << 2,
    DM_HUD_ST_RACER      = 1ULL << 3,
    DM_HUD_ST_PLAYER_OK  = 1ULL << 4,
    DM_HUD_ST_WEAPONS_OK = 1ULL << 5,
    DM_HUD_ST_COP_CS     = 1ULL << 6,
    DM_HUD_ST_GARAGE     = 1ULL << 7,
    DM_HUD_ST_MOVIE      = 1ULL << 8,
    DM_HUD_ST_3D_SCENE   = 1ULL << 9,
    DM_HUD_ST_2D_ONLY    = 1ULL << 18,
};

enum {
    DM_HUD_W_HELI        = 1ULL << 10, // slot 1: Cop Helicopter
    DM_HUD_W_COP_EMP     = 1ULL << 11, // slot 2: Cop EMP
    DM_HUD_W_RACER_SPK   = 1ULL << 12, // slot 3: Racer Spike Strip
    DM_HUD_W_COP_SPK     = 1ULL << 13, // slot 4: Cop Spike Strip
    DM_HUD_W_TURBO       = 1ULL << 14, // slot 5: Racer Overdrive / Turbo
    DM_HUD_W_RACER_EMP   = 1ULL << 15, // slot 6: Racer EMP
    DM_HUD_W_JAMMER      = 1ULL << 16, // slot 8: Racer Jammer
    DM_HUD_W_ROADBLOCK   = 1ULL << 17, // slot 9: Cop Roadblock
};

uint64_t dm_nfshpr_hud_state(void);

void dm_hud_sig_note_draw(int is_3d, uint64_t vs_key, uint64_t fs_key);
void dm_hud_sig_frame_end(void);
void dm_hud_sig_note_movie(void);
void dm_hud_sig_snapshot(uint32_t *draws_out, uint32_t *draws3d_out, uint64_t *sh_xor_out);

int dm_hud_active(void);
int dm_hud_layer(void);
int dm_hud_ver(void);
int dm_hud_count(void);
const hud_btn_t *dm_hud_btns(void);
int dm_hud_visible(int idx);
int64_t dm_hud_pressed(int idx);
void dm_hud_stick(float *dx, float *dy);
void dm_hud_stick_ex(int idx, float *dx, float *dy);
