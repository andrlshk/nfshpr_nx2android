# Need for Speed: Hot Pursuit Remastered — Android Native Port (`v1.0-beta`)

[English](#english) | [Русский](#русский)

---

## English

A fork of [nx2android](https://github.com/seedds/nx2android) (MIT License) with a custom Android launcher, touch HUD, and automatic GPU/CPU detection (Snapdragon Adreno / MediaTek Mali) for **Need for Speed: Hot Pursuit Remastered** (`010029B0118E8000`).

> [!IMPORTANT]
> **No game files or decryption keys are included.** You must dump `RomFS` from your own legally owned copy of the game. `prod.keys` does **not** need to be placed on your phone — it is only required once on PC when extracting `RomFS`.

### Installation (Prebuilt APK from Releases)
1. Download `NFSHPR_Unified_v1.0-beta.apk` from **Releases** (`v1.0-beta`).
2. Extract `RomFS` from your `.nsp` dump and copy it to your device at:
   `/sdcard/Games/NFSHPR/RomFS`
3. Install the APK, grant storage permission, and launch the game from the launcher.

### Hardware Auto-Detection
- **Snapdragon (Adreno 6xx/7xx):** Turnip (`libvulkan.purple.so`), `GMEM ON` (`TU_DEBUG=startup,nocb`).
- **MediaTek (Mali / Immortalis):** System Vulkan, `GMEM OFF` (`TU_DEBUG=startup,nocb,sysmem`), native Mali fixes (`spv_no_clip`, `dualSrcBlend` fallback, `gralloc_extra`).
- **Adreno 8xx / Others:** System Vulkan.

### Repository Structure
- `nx2android/` — native host & Vulkan backend (including HUD, FSR, icon patches, and updated Mali renderer)
- `launcher/` — Android launcher source code (`org.nx2a.nfshpr.launcher`)
- `LICENSE` — MIT License (`Copyright (c) 2026 seedds`)

### Credits & Acknowledgements
- **Original port author & engine:** [nx2android](https://github.com/seedds/nx2android) (`seedds`)
- **MediaTek (Mali) renderer:** huge thanks to **lesad** ([https://github.com/lesad710](https://github.com/lesad710)) for implementing the MTK Vulkan renderer fixes.

### Beta Status & Known Issues
This port is currently in **beta**, so crashes, stutters, and unexpected quirks are possible. Known issues right now: audio crackling and relatively low FPS. Updates will keep coming — the entire project was built end-to-end with AI, so development goes on as long as there are tokens left :)

If you know your way around this or have a Claude subscription and want to tinker — feel free to reach out via GitHub Issues. We can debug together, and if your fix genuinely helps, I will definitely add you to the credits on GitHub.

When reporting bugs, please include your **phone model / SoC** and attach the **log** (it can be copied to the clipboard with one button right inside the launcher).

---

## Русский

Форк [nx2android](https://github.com/seedds/nx2android) (MIT License) с кастомным Android-лаунчером, сенсорным HUD и автоопределением GPU/CPU (Snapdragon Adreno / MediaTek Mali) для **Need for Speed: Hot Pursuit Remastered** (`010029B0118E8000`).

> [!IMPORTANT]
> **Игровые файлы и ключи в репозиторий не включены.** Для запуска требуется `RomFS` из вашей собственной легальной копии игры. `prod.keys` на телефон копировать не нужно — он нужен только один раз при извлечении `RomFS` на ПК.

### Установка (готовый APK из Releases)
1. Скачайте `NFSHPR_Unified_v1.0-beta.apk` из раздела **Releases** (`v1.0-beta`).
2. Извлеките `RomFS` из вашего `.nsp` и поместите на устройство по пути:
   `/sdcard/Games/NFSHPR/RomFS`
3. Установите APK, выдайте доступ к хранилищу и запустите игру через лаунчер.

### Автоопределение железа
- **Snapdragon (Adreno 6xx/7xx):** Turnip (`libvulkan.purple.so`), `GMEM ON` (`TU_DEBUG=startup,nocb`).
- **MediaTek (Mali / Immortalis):** Системный Vulkan, `GMEM OFF` (`TU_DEBUG=startup,nocb,sysmem`), нативные Mali-фиксы (`spv_no_clip`, фоллбэк `dualSrcBlend`, `gralloc_extra`).
- **Adreno 8xx / прочие:** Системный Vulkan.

### Структура
- `nx2android/` — нативный хост и Vulkan-бэкенд (с патчами HUD, FSR, иконок и обновлённым Mali-рендером)
- `launcher/` — исходники Android-лаунчера (`org.nx2a.nfshpr.launcher`)
- `LICENSE` — MIT License (`Copyright (c) 2026 seedds`)

### Авторы и благодарности
- **Базовый проект и движок порта:** [nx2android](https://github.com/seedds/nx2android) (`seedds`)
- **Рендер под MediaTek (Mali):** огромная благодарность **lesad** ([https://github.com/lesad710](https://github.com/lesad710)) за доработку Vulkan-рендера под MTK.

### Статус бета-версии и известные проблемы
Данный порт является бета-версией, поэтому возможны вылеты, лаги и много чего ещё непонятного. На данный момент из известного: звук похрипывает, а FPS маловат. Обновления будут выходить — весь проект от и до сделан с помощью ИИ, так что работа идёт, пока не закончатся токены :)

Все, кто в этом хорошо понимает или у кого есть подписка на Claude и желание поковыряться — смело пишите в GitHub Issues! Изучим проблему вместе, и если ваша правка реально поможет, обязательно впишу вас в кредиты на GitHub.

При баг-репортах желательно сразу указывать **модель телефона / процессора** и прикладывать **лог** (он копируется в буфер обмена одной кнопкой прямо в лаунчере).
