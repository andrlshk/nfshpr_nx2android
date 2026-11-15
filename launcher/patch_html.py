#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(r"c:\Users\Andrew\Downloads\nfs_hot_pursuit_remastered_android_launcher(2).html")
dst = Path(__file__).resolve().parent / "assets" / "index.html"

html = src.read_text(encoding="utf-8")

# Use local bundled tailwind.js for instant offline startup
html = html.replace("https://cdn.tailwindcss.com", "tailwind.js")

# 1. Strict Android WebView fullscreen + anti-scroll/pan CSS overrides
android_css = """
        /* Android Fullscreen WebView Overrides (No Internal Panning/Bounce) */
        html, body {
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
            overscroll-behavior: none !important;
            touch-action: none !important;
            user-select: none !important;
            -webkit-user-select: none !important;
        }
        body > header {
            display: none !important;
        }
        #workspaceContainer {
            position: fixed !important;
            inset: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            max-width: none !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
            overscroll-behavior: none !important;
            touch-action: none !important;
        }
        .device-frame {
            aspect-ratio: auto !important;
            width: 100vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            background: #0d1015 !important;
            overflow: hidden !important;
        }
        .device-screen {
            border-radius: 0 !important;
            border: none !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        .hp-scroll {
            touch-action: pan-y !important;
            overscroll-behavior: contain !important;
        }
    </style>"""

assert "    </style>" in html
html = html.replace("    </style>", android_css, 1)

# 2. Default background to bg.png (user's new NFSHPR screenshot), add musicSkip to defaultRaceLayout, and clean up top row positions
assert "customBgUrl: null," in html
html = html.replace("customBgUrl: null,", "customBgUrl: 'bg.png',", 1)

old_top_row = """            siren:       { id: 'siren',       label: 'Сирена',     tag: 'СИРЕНА',   icon: 'siren',      accent: 'scpd',    group: 'common',  x: 32, y: 20, baseSize: 50, scale: 1 },
            headlights:  { id: 'headlights',  label: 'Фары',       tag: 'ФАРЫ',     icon: 'headlights', accent: 'amber',   group: 'common',  x: 41, y: 20, baseSize: 50, scale: 1 },
            pause:       { id: 'pause',       label: 'Пауза',      tag: 'ПАУЗА',    icon: 'pause',      accent: 'neutral', group: 'common',  x: 50, y: 19, baseSize: 50, scale: 1 },
            camera:      { id: 'camera',      label: 'Камера',     tag: 'КАМЕРА',   icon: 'camera',     accent: 'neutral', group: 'common',  x: 59, y: 20, baseSize: 50, scale: 1 },
            lookBack:    { id: 'lookBack',    label: 'Назад',      tag: 'НАЗАД',    icon: 'lookback',   accent: 'neutral', group: 'common',  x: 68, y: 20, baseSize: 50, scale: 1 }"""

new_top_row = """            siren:       { id: 'siren',       label: 'Сирена',     tag: 'СИРЕНА',   icon: 'siren',      accent: 'scpd',    group: 'common',  x: 30, y: 20, baseSize: 50, scale: 1 },
            headlights:  { id: 'headlights',  label: 'Фары',       tag: 'ФАРЫ',     icon: 'headlights', accent: 'amber',   group: 'common',  x: 38, y: 20, baseSize: 50, scale: 1 },
            musicSkip:   { id: 'musicSkip',   label: 'Трек →',     tag: 'ТРЕК →',   icon: 'music',      accent: 'neutral', group: 'common',  x: 46, y: 20, baseSize: 50, scale: 1 },
            pause:       { id: 'pause',       label: 'Пауза',      tag: 'ПАУЗА',    icon: 'pause',      accent: 'neutral', group: 'common',  x: 54, y: 19, baseSize: 50, scale: 1 },
            camera:      { id: 'camera',      label: 'Камера',     tag: 'КАМЕРА',   icon: 'camera',     accent: 'neutral', group: 'common',  x: 62, y: 20, baseSize: 50, scale: 1 },
            lookBack:    { id: 'lookBack',    label: 'Назад',      tag: 'НАЗАД',    icon: 'lookback',   accent: 'neutral', group: 'common',  x: 70, y: 20, baseSize: 50, scale: 1 }"""

assert old_top_row in html
html = html.replace(old_top_row, new_top_row, 1)

# Add musicSkip English label and GMEM i18n strings
assert "steerLeft: 'Steer Left'," in html
html = html.replace(
    "lookBack: 'Look Back',",
    "lookBack: 'Look Back', musicSkip: 'Next Track',",
    1
)

# 3. Replace state.graphics defaults to only real supported settings + GMEM toggle
old_gfx_state = re.search(r"graphics:\s*\{[^}]+\}", html)
assert old_gfx_state is not None
new_gfx_state = """graphics: {
                gmem: true,             // true = TU_DEBUG=startup,nocb (Adreno), false = TU_DEBUG=startup,nocb,sysmem (MTK)
                resolution: '720p',     // '540p' | '720p' | '1080p'
                fpsLimit: '60',         // '30' | '60' | 'unlimited'
                anisotropic: '4x',      // 'off' | '2x' | '4x' | '8x' | '16x'
                vulkanDriver: 'turnip', // 'turnip' | 'system'
                shaderCache: true,
                dmVkNocull: true
            }"""
html = html[:old_gfx_state.start()] + new_gfx_state + html[old_gfx_state.end():]

# Update getTelemetrySummary to reflect real settings (no fake FSR)
old_telemetry = re.search(r"function getTelemetrySummary\(\)\s*\{.*?\n        \}", html, re.S)
assert old_telemetry is not None
new_telemetry = """function getTelemetrySummary() {
            const g = state.graphics;
            const c = state.controls;
            const steerLabels = {
                buttons: t('buttons'),
                stick: t('stick'),
                gyro: t('gyro')
            };
            const inputLabel = c.device === 'gamepad' ? t('gamepad') : (steerLabels[c.steering] || t('buttons'));
            const fpsLabel = g.fpsLimit === 'unlimited' ? '120 FPS' : `${g.fpsLimit} FPS`;
            const gmemLabel = g.gmem ? 'GMEM' : 'Sysmem';
            const drvLabel = g.vulkanDriver === 'turnip' ? 'Turnip' : 'System VK';
            return `${g.resolution} • ${fpsLabel} • ${gmemLabel} • ${drvLabel} • ${inputLabel}`;
        }"""
html = html[:old_telemetry.start()] + new_telemetry + html[old_telemetry.end():]

# 4. Replace renderGraphicsScreen with ONLY real working NFSHPR settings + prominent GMEM toggle
old_gfx_screen = re.search(r"function renderGraphicsScreen\(\)\s*\{.*?\n        \}\n\n        // =====", html, re.S)
assert old_gfx_screen is not None
new_gfx_screen = """function renderGraphicsScreen() {
            const g = state.graphics;
            const animClass = state.animateScreen ? 'screen-enter' : '';
            const gmemLabel = state.lang === 'ru' ? 'GMEM (Память тайлов)' : 'GMEM (Tile Memory)';
            const gmemOnLabel = state.lang === 'ru' ? 'Вкл (Adreno)' : 'On (Adreno)';
            const gmemOffLabel = state.lang === 'ru' ? 'Выкл (MTK)' : 'Off (MTK)';
            return `
                <div class="device-screen">
                    ${renderWallpaperLayers()}

                    <div class="relative z-10 flex-1 min-h-0 p-3 sm:p-4 flex flex-col">
                        <div class="hp-glass-panel ${animClass} flex-1 min-h-0 p-3.5 sm:p-4 flex flex-col justify-between gap-2.5 overflow-hidden">
                            ${renderSettingsHeader('graphics')}

                            <div class="flex-1 min-h-0 overflow-y-auto hp-scroll grid grid-cols-1 md:grid-cols-2 gap-x-3 gap-y-2 content-center">
                                <!-- Левая колонка -->
                                <div class="flex flex-col gap-2">
                                    ${renderSettingRow(gmemLabel, renderAngledSelector([
                                        { id: 'on',  label: gmemOnLabel },
                                        { id: 'off', label: gmemOffLabel }
                                    ], g.gmem ? 'on' : 'off', 'setGfxGmem', 'racer'))}

                                    ${renderSettingRow(t('resolution'), renderAngledSelector([
                                        { id: '540p',  label: '540p' },
                                        { id: '720p',  label: '720p' },
                                        { id: '1080p', label: '1080p' }
                                    ], g.resolution, 'setGfxResolution', 'scpd'))}

                                    ${renderSettingRow(t('fpsLimit'), renderAngledSelector([
                                        { id: '30',        label: '30' },
                                        { id: '60',        label: '60' },
                                        { id: 'unlimited', label: '120' }
                                    ], g.fpsLimit, 'setGfxFps', 'racer'))}

                                    ${renderSettingRow(t('aniso'), renderAngledSelector([
                                        { id: 'off', label: t('off') },
                                        { id: '2x',  label: '2x' },
                                        { id: '4x',  label: '4x' },
                                        { id: '8x',  label: '8x' },
                                        { id: '16x', label: '16x' }
                                    ], g.anisotropic, 'setGfxAniso', 'scpd'))}
                                </div>

                                <!-- Правая колонка -->
                                <div class="flex flex-col gap-2">
                                    <div class="px-3 py-1.5 rounded bg-white/5 border border-white/10 text-[11px] text-slate-300 flex items-center justify-between gap-2">
                                        <span class="truncate" title="Auto-detected Hardware">${(window.__hwInfo && (window.__hwInfo.socModel || window.__hwInfo.gpuRenderer)) ? ((window.__hwInfo.socModel || 'CPU') + ' • ' + (window.__hwInfo.gpuRenderer || 'GPU')) : 'Snapdragon / MTK Auto'}</span>
                                        <span class="shrink-0 font-bold text-cyan-300">${(window.__hwInfo && window.__hwInfo.gpuProfile === 'mali_mtk') ? 'MTK/Mali' : (g.vulkanDriver === 'turnip' ? 'Adreno Turnip' : 'System VK')}</span>
                                    </div>
                                    ${renderSettingRow(t('vulkanDriver'), renderAngledSelector([
                                        { id: 'turnip', label: 'Turnip' },
                                        { id: 'system', label: t('system') }
                                    ], g.vulkanDriver, 'setGfxVulkan', 'racer'))}

                                    ${renderSettingRow(t('shaderCache'), renderAngledSelector([
                                        { id: 'on',  label: t('on') },
                                        { id: 'off', label: t('off') }
                                    ], g.shaderCache ? 'on' : 'off', 'setGfxShaderCache', 'scpd'))}

                                    ${renderSettingRow('DM_VK_NOCULL', renderAngledSelector([
                                        { id: 'on',  label: t('on') },
                                        { id: 'off', label: t('off') }
                                    ], g.dmVkNocull ? 'on' : 'off', 'setGfxDmVkNocull', 'racer'))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // ====="""
html = html[:old_gfx_screen.start()] + new_gfx_screen + html[old_gfx_screen.end():]

# Clean up generateDiagnosticLog references to removed fake graphics fields
old_diag_gfx = re.search(r"\[\$\{ts\}\] \[GFX\]   Resolution=.*?\[AUDIO\]", html, re.S)
if old_diag_gfx:
    new_diag_gfx = """[${ts}] [GFX]   GMEM=${g.gmem ? 'ON (Adreno)' : 'OFF (MTK/Sysmem)'} | Resolution=${g.resolution} | FPS=${g.fpsLimit}
[${ts}] [GFX]   Anisotropic=${g.anisotropic} | Vulkan=${g.vulkanDriver} | ShaderCache=${g.shaderCache ? 'ON' : 'OFF'} | DM_VK_NOCULL=${g.dmVkNocull ? '1' : '0'}
[${ts}] [AUDIO]"""
    html = html[:old_diag_gfx.start()] + new_diag_gfx + html[old_diag_gfx.end():]

# Add setGfxGmem handler & mark manual overrides
assert "function setGfxResolution(v)" in html
html = html.replace(
    "function setGfxResolution(v)",
    "function setGfxGmem(v) { state.graphics.gmem = (v === 'on'); state.graphics.autoProfile = false; renderApp(); }\n        function setGfxResolution(v)",
    1
)
html = html.replace(
    "function setGfxVulkan(v) {",
    "function setGfxVulkan(v) { state.graphics.autoProfile = false;",
    1
)

# 5. Inject AndroidBridge integration
bridge_js = """
        // =========================================================================
        // ANDROID BRIDGE INTEGRATION (org.nx2a.nfshpr)
        // =========================================================================
        function buildEnvText() {
            const g = state.graphics;
            const fpsPin = g.fpsLimit === '30' ? '30' : (g.fpsLimit === '60' ? '60' : '120');
            const anisoMap = { 'off': '1.0', '2x': '2.0', '4x': '4.0', '8x': '8.0', '16x': '16.0' };
            const anisoVal = anisoMap[g.anisotropic] || '4.0';
            const dmLang = state.lang === 'ru' ? 'ru' : 'en-US';
            const lines = [
                '# Need for Speed: Hot Pursuit Remastered — Native Android Runtime Config',
                'DM_LANG=' + dmLang,
                'DM_SHARED_FONT_EXT=/sdcard/Android/data/org.nx2a.nfshpr/files/nintendo_ext.ttf',
                'DM_ROMFS=/sdcard/Games/NFSHPR/RomFS',
            ];
            const hw = window.__hwInfo || {};
            const isMali = (hw.gpuProfile === 'mali_mtk') || (g.vulkanDriver === 'system' && !g.gmem);
            if (g.vulkanDriver === 'turnip') {
                lines.push('DM_VK_DRIVER=libvulkan.purple.so');
            }
            lines.push(g.gmem ? 'TU_DEBUG=startup,nocb' : 'TU_DEBUG=startup,nocb,sysmem');
            if (g.vulkanDriver === 'turnip') {
                lines.push(
                    'DM_VK_RP=1',
                    'DM_VK_LRZ_TOUCH=0',
                    'DM_VK_FDZ=0',
                    'DM_VK_FLIP_FRONT=1',
                    'DM_VK_UBWC=3',
                    'DM_VK_SETSPLIT=1',
                    'DM_VK_PRESENT=mailbox'
                );
            } else if (!isMali) {
                lines.push(
                    'DM_VK_RP=1',
                    'DM_VK_LRZ_TOUCH=0',
                    'DM_VK_FDZ=0',
                    'DM_VK_FLIP_FRONT=1',
                    'DM_VK_SETSPLIT=1',
                    'DM_VK_PRESENT=mailbox'
                );
            } else {
                lines.push('DM_VK_PRESENT=fifo');
            }
            lines.push(
                'DM_NVN_ASYNC=1',
                'DM_NVN_ACQ_REPLAYED=0',
                'DM_PIN_REPLAY=big',
                'DM_GPU_TURBO=1',
                'DM_ADAPTIVE_FPS=0',
                'DM_FPS_PIN=' + fpsPin,
                'DM_VK_FIT=fill',
                'DM_ULTRAWIDE=1',
                'DM_OPMODE=' + (g.resolution === '1080p' ? '1' : '0')
            );
            if (g.resolution === '540p') {
                lines.push('DM_RES=540p');
            } else {
                lines.push('DM_RES=720p');
            }
            if (!g.shaderCache) {
                lines.push('DM_VK_NOPCACHE=1');
            }
            lines.push(
                'DM_VK_NOCULL=' + (g.dmVkNocull ? '1' : '0'),
                'DM_VK_MT_REPLAY=0',
                'DM_VK_CB_DRAWS=0',
                'DM_VK_SUBMIT_SPLIT=0',
                'DM_VK_ASYNC_PIPE=0',
                'DM_VK_PACE=0',
                'DM_WINDOW_FPS=120',
                'DM_VK_PASS_TIMES=0',
                'DM_VK_PROF_SLOW=0',
                'DM_VK_FP16=0',
                'DM_AUDIO_BURSTS=48',
                'DM_VK_MAX_ANISO=' + anisoVal
            );
            return lines.join('\\n') + '\\n';
        }

        function buildSettingsText() {
            const c = state.controls;
            const g = state.graphics;
            const overlay = c.device === 'touch' ? 1 : 0;
            const rumble = c.vibration ? 1 : 0;
            const docked = g.resolution === '1080p' ? 1 : 0;
            const steer = c.steering === 'buttons' ? 0 : (c.steering === 'stick' ? 1 : 2);
            const lines = [
                'overlay=' + overlay,
                'rumble=' + rumble,
                'docked=' + docked,
                'fps=1',
                'opacity=' + c.hudOpacity,
                'grid=0',
                'steer=' + steer
            ];
            return lines.join('\\n') + '\\n';
        }

        function buildUiJson() {
            const c = state.controls;
            const toNativeBtn = (b, isMenu) => {
                const sc = (c.hudSize / 100.0) * (b.scale || 1.0);
                const base = b.baseSize || 64;
                const w = Math.max(36, Math.min(160, Math.round(base * sc)));
                const h = Math.max(36, Math.min(160, Math.round(base * sc)));
                const x = Math.max(4, Math.min(96, Math.round(b.x)));
                const y = Math.max(6, Math.min(94, Math.round(b.y)));
                return {
                    id: b.id,
                    label: b.tag || b.label || b.id,
                    x: x,
                    y: y,
                    w: w,
                    h: h,
                    racer: !isMenu
                };
            };
            const allRace = Object.values(c.raceLayout)
                .filter(b => b.group === 'common' || b.group === c.steering);
            const copBtns = allRace
                .filter(b => b.id !== 'turbo' && b.id !== 'jammer')
                .map(b => toNativeBtn(b, false));
            const racerBtns = allRace
                .filter(b => b.id !== 'roadblock' && b.id !== 'heli' && b.id !== 'siren')
                .map(b => toNativeBtn(b, false));
            const menuBtns = Object.values(c.menuLayout)
                .map(b => toNativeBtn(b, true));
            return JSON.stringify({
                cop: copBtns,
                racer: racerBtns,
                menu: menuBtns,
                nfshprState: {
                    schemaVersion: 2,
                    lang: state.lang,
                    controls: state.controls,
                    graphics: state.graphics
                }
            });
        }

        function syncToAndroid() {
            if (typeof AndroidBridge === 'undefined') return 'ok';
            try {
                return AndroidBridge.saveConfig(buildEnvText(), buildSettingsText(), buildUiJson());
            } catch (e) {
                return 'err:' + e;
            }
        }

        function loadFromAndroid() {
            if (typeof AndroidBridge === 'undefined') return;
            try {
                const stRaw = AndroidBridge.getStatus && AndroidBridge.getStatus();
                let hwProfile = 'adreno_turnip';
                if (stRaw) {
                    const st = JSON.parse(stRaw);
                    window.__hwInfo = st;
                    if (st.gpuProfile) hwProfile = st.gpuProfile;
                    if (st.storage === false && AndroidBridge.requestStoragePermission) {
                        setTimeout(() => AndroidBridge.requestStoragePermission(), 400);
                    }
                }
                const applyAutoHw = () => {
                    if (state.graphics.autoProfile === false) return;
                    if (hwProfile === 'mali_mtk') {
                        state.graphics.vulkanDriver = 'system';
                        state.graphics.gmem = false;
                    } else if (hwProfile === 'adreno_sys' || hwProfile === 'system') {
                        state.graphics.vulkanDriver = 'system';
                        state.graphics.gmem = true;
                    } else {
                        state.graphics.vulkanDriver = 'turnip';
                        state.graphics.gmem = true;
                    }
                };
                applyAutoHw();
                const cfgRaw = AndroidBridge.loadConfig && AndroidBridge.loadConfig();
                if (!cfgRaw) return;
                const cfg = JSON.parse(cfgRaw);
                if (cfg.ui) {
                    try {
                        const parsedUi = JSON.parse(cfg.ui);
                        if (parsedUi && parsedUi.nfshprState && parsedUi.nfshprState.schemaVersion === 2) {
                            if (parsedUi.nfshprState.lang) {
                                state.lang = parsedUi.nfshprState.lang;
                            }
                            if (parsedUi.nfshprState.controls) {
                                const sc = parsedUi.nfshprState.controls;
                                const savedRace = sc.raceLayout || {};
                                const savedMenu = sc.menuLayout || {};
                                Object.assign(state.controls, sc);
                                const cleanRace = JSON.parse(JSON.stringify(defaultRaceLayout));
                                for (const k of Object.keys(cleanRace)) {
                                    if (savedRace[k]) Object.assign(cleanRace[k], savedRace[k]);
                                }
                                const cleanMenu = JSON.parse(JSON.stringify(defaultGarageMenuLayout));
                                for (const k of Object.keys(cleanMenu)) {
                                    if (savedMenu[k]) Object.assign(cleanMenu[k], savedMenu[k]);
                                }
                                state.controls.raceLayout = cleanRace;
                                state.controls.menuLayout = cleanMenu;
                            }
                            if (parsedUi.nfshprState.graphics) {
                                Object.assign(state.graphics, parsedUi.nfshprState.graphics);
                                if (!['540p', '720p', '1080p'].includes(state.graphics.resolution)) {
                                    state.graphics.resolution = '720p';
                                }
                                applyAutoHw();
                            }
                        }
                    } catch (e) {}
                }
            } catch (e) {}
        }

        window.onAndroidBack = function() {
            const logModal = document.getElementById('logModal');
            if (logModal && !logModal.classList.contains('hidden')) {
                toggleLogModal(false);
                return;
            }
            if (state.showAtlasDrawer) {
                toggleAtlasDrawer(false);
                return;
            }
            if (state.isLaunching) {
                cancelLaunch();
                return;
            }
            if (state.currentScreen === 'hud') {
                navigateTo('controls');
                return;
            }
            if (state.currentScreen !== 'main') {
                navigateTo('main');
            }
        };
"""

target_copy = """        function copyDiagnosticLog() {
            const logText = generateDiagnosticLog();
            const ta = document.createElement('textarea');"""
assert target_copy in html
html = html.replace(target_copy, bridge_js + "\n" + target_copy, 1)

# Wire copyDiagnosticLog to AndroidBridge.copyLog
old_copy_fn = re.search(r"function copyDiagnosticLog\(\)\s*\{.*?\n        \}", html, re.S)
assert old_copy_fn is not None
new_copy_fn = """let _syncTimer = null;
        function scheduleSyncToAndroid() {
            if (_syncTimer) clearTimeout(_syncTimer);
            _syncTimer = setTimeout(syncToAndroid, 250);
        }

        function copyDiagnosticLog() {
            const logPath = '/sdcard/Android/data/org.nx2a.nfshpr/files/log.txt';
            if (typeof AndroidBridge !== 'undefined' && AndroidBridge.copyLog) {
                const res = AndroidBridge.copyLog();
                if (res && res.startsWith('ok:')) {
                    state.logCopied = true;
                    renderApp();
                    const parts = res.split(':');
                    showFacetedToast(t('logCopied'), parts[1] + ' lines • ' + logPath, 'confirm');
                    setTimeout(() => {
                        state.logCopied = false;
                        renderApp();
                    }, 2200);
                } else {
                    showFacetedToast('Log', (res ? res.replace('err:', '') : 'Launch game first') + ' • ' + logPath, 'scpd');
                }
                return;
            }
            const logText = generateDiagnosticLog();
            const ta = document.createElement('textarea');
            ta.value = logText;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand('copy');
                state.logCopied = true;
                renderApp();
                showFacetedToast(t('logCopied'), getTelemetrySummary(), 'confirm');
                setTimeout(() => {
                    state.logCopied = false;
                    renderApp();
                }, 2200);
            } catch (err) {
                toggleLogModal(true);
            }
            document.body.removeChild(ta);
        }"""
html = html[:old_copy_fn.start()] + new_copy_fn + html[old_copy_fn.end():]

# Wire startGameLaunch to AndroidBridge.launchGame
target_launch = """        function startGameLaunch() {
            launchTimers.forEach(t => clearTimeout(t));
            launchTimers = [];
            state.isLaunching = true;"""
replacement_launch = """        function startGameLaunch() {
            syncToAndroid();
            if (typeof AndroidBridge !== 'undefined' && AndroidBridge.launchGame) {
                const res = AndroidBridge.launchGame(buildEnvText(), buildSettingsText(), buildUiJson());
                if (res !== 'ok') {
                    showFacetedToast('Error', res.replace('err:', ''), 'racer');
                }
                return;
            }
            launchTimers.forEach(t => clearTimeout(t));
            launchTimers = [];
            state.isLaunching = true;"""
assert target_launch in html
html = html.replace(target_launch, replacement_launch, 1)

# Sync on renderApp (debounced) and load on DOMContentLoaded
assert "function renderApp() {" in html
html = html.replace("function renderApp() {", "function renderApp() {\n            scheduleSyncToAndroid();", 1)

# Add touch-action: none to HUD dropzone & nodes and disable CSS animations/transitions to prevent screen flicker
html = html.replace("</style>", ".hud-dropzone, .hud-node { touch-action: none; -webkit-user-select: none; user-select: none; }\n        *, *::before, *::after { animation: none !important; transition: none !important; }\n    </style>", 1)

# Fix HUD drag: do NOT call renderApp() inside startHudDrag (destroying touched DOM node breaks touchmove in WebView)
old_start_drag = """        function startHudDrag(event, btnId) {
            event.preventDefault();
            const zone = event.currentTarget.closest('.hud-dropzone');
            if (!zone) return;
            const rect = zone.getBoundingClientRect();
            state.selectedHudId = btnId;
            activeDrag = { btnId, rect };
            renderApp();
        }"""
new_start_drag = """        function startHudDrag(event, btnId) {
            if (event.cancelable) event.preventDefault();
            const zone = event.currentTarget.closest('.hud-dropzone');
            if (!zone) return;
            const rect = zone.getBoundingClientRect();
            state.selectedHudId = btnId;
            activeDrag = { btnId, rect };
            const mapObj = getActiveHudMap();
            const btn = mapObj[btnId];
            if (btn) {
                document.querySelectorAll('[data-hud-coords]').forEach(el => {
                    el.textContent = `${getHudNodeLabel(btn)} • X:${btn.x}% Y:${btn.y}%`;
                });
            }
        }"""
assert old_start_drag in html
html = html.replace(old_start_drag, new_start_drag, 1)

old_move_drag = """        function handleHudDragMove(event) {
            if (!activeDrag) return;"""
new_move_drag = """        function handleHudDragMove(event) {
            if (!activeDrag) return;
            if (event.cancelable) event.preventDefault();"""
assert old_move_drag in html
html = html.replace(old_move_drag, new_move_drag, 1)

html = html.replace(
    "window.addEventListener('touchend', stopHudDrag);",
    "window.addEventListener('touchend', stopHudDrag);\n        window.addEventListener('touchcancel', stopHudDrag);",
    1,
)

# Wire external GitHub link through AndroidBridge.openUrl
html = html.replace(
    '<a href="https://github.com/andrlshk" target="_blank" rel="noopener noreferrer"',
    '<a href="https://github.com/andrlshk" target="_blank" rel="noopener noreferrer" onclick="if(window.AndroidBridge&&AndroidBridge.openUrl){event.preventDefault();AndroidBridge.openUrl(this.href);}"',
)

# Show exact Android log path in downloadDiagnosticLog & toggleLogModal
old_dl_log = """        function downloadDiagnosticLog() {
            const blob = new Blob([generateDiagnosticLog()], { type: 'text/plain;charset=utf-8' });
            triggerDownload(blob, 'nx2android_runtime.log');
            showFacetedToast(t('toastLogSaved'), 'nx2android_runtime.log', 'scpd');
        }"""
new_dl_log = """        function downloadDiagnosticLog() {
            const logPath = '/sdcard/Android/data/org.nx2a.nfshpr/files/log.txt';
            if (typeof AndroidBridge !== 'undefined' && AndroidBridge.copyLog) {
                AndroidBridge.copyLog();
            }
            showFacetedToast(t('toastLogSaved'), logPath, 'scpd');
        }"""
assert old_dl_log in html
html = html.replace(old_dl_log, new_dl_log, 1)

html = html.replace(
    "document.getElementById('logModalContent').textContent = generateDiagnosticLog();",
    "document.getElementById('logModalContent').textContent = 'Runtime log path: /sdcard/Android/data/org.nx2a.nfshpr/files/log.txt\\n\\n' + generateDiagnosticLog();",
    1,
)

target_dom = """        window.addEventListener('DOMContentLoaded', () => {
            state.animateScreen = true;
            renderApp();"""
replacement_dom = """        window.addEventListener('DOMContentLoaded', () => {
            loadFromAndroid();
            state.animateScreen = false;
            renderApp();"""
assert target_dom in html
html = html.replace(target_dom, replacement_dom, 1)

dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(html, encoding="utf-8")
print(f"Successfully patched NFSHPR {dst} ({len(html)} chars)")
