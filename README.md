# Need for Speed: Hot Pursuit Remastered — Android Native Port (`v1.0-beta`)

Форк [nx2android](https://github.com/seedds/nx2android) (MIT License) с кастомным Android-лаунчером, сенсорным HUD и автоопределением GPU/CPU (Snapdragon Adreno / MediaTek Mali) для **Need for Speed: Hot Pursuit Remastered** (`010029B0118E8000`).

> [!IMPORTANT]
> **Игровые файлы и ключи в репозиторий не включены.** Для запуска требуется `RomFS` из вашей собственной легальной копии игры. `prod.keys` на телефон копировать не нужно — он нужен только один раз при извлечении `RomFS` на ПК.

## Установка (готовый APK из Releases)
1. Скачайте `NFSHPR_Unified_v1.0-beta.apk` из раздела **Releases** (`v1.0-beta`).
2. Извлеките `RomFS` из вашего `.nsp` и поместите на устройство по пути:
   `/sdcard/Games/NFSHPR/RomFS`
3. Установите APK, выдайте доступ к хранилищу и запустите игру через лаунчер.

## Автоопределение железа
- **Snapdragon (Adreno 6xx/7xx):** Turnip (`libvulkan.purple.so`), `GMEM ON` (`TU_DEBUG=startup,nocb`).
- **MediaTek (Mali / Immortalis):** Системный Vulkan, `GMEM OFF` (`TU_DEBUG=startup,nocb,sysmem`), нативные Mali-фиксы (`spv_no_clip`, фоллбэк `dualSrcBlend`, `gralloc_extra`).
- **Adreno 8xx / прочие:** Системный Vulkan.

## Структура
- `nx2android/` — нативный хост и Vulkan-бэкенд (с патчами HUD, FSR, иконок и обновлённым Mali-рендером)
- `launcher/` — исходники Android-лаунчера (`org.nx2a.nfshpr.launcher`)
- `LICENSE` — MIT License (`Copyright (c) 2026 seedds`)

## Авторы и благодарности
- **Базовый проект и движок порта:** [nx2android](https://github.com/seedds/nx2android) (`seedds`)
- **Рендер под MediaTek (Mali):** огромная благодарность **lesad** ([https://github.com/lesad710](https://github.com/lesad710)) за доработку Vulkan-рендера под MTK.
