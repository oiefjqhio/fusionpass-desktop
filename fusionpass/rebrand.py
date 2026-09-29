#!/usr/bin/env python3
"""Apply the Fusion Pass branding and lock-down to a NuvioDesktop checkout (Windows, macOS, Linux).
Idempotent: run after every upstream sync (git merge upstream/Dev, then this, commit).

GPL-3.0: this fork's source stays public; README and About credit Nuvio.
"""
import glob, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = f'{ROOT}/composeApp/src'
ICONS = f'{APP}/desktopMain/resources/icons'
D = f'{APP}/desktopMain/kotlin/com/nuvio/app'
WF = f'{ROOT}/.github/workflows/desktop-release.yml'
G = f'{ROOT}/composeApp/build.gradle.kts'
CR = f'{APP}/commonMain/composeResources'
K = f'{APP}/commonMain/kotlin/com/nuvio/app'
OUT = f'{ROOT}/fusionpass/brand/out'
changed = []


def edit(path, pairs):
    s = open(path, encoding='utf8').read()
    orig = s
    for a, b in pairs:
        if a in b and b in s:
            continue  # already applied; b extends a, so replacing again would repeat it
        if a not in s and b not in s:
            sys.exit(f'rebrand: anchor not found in {path}: {a[:80]!r} (upstream changed; update rebrand.py)')
        s = s.replace(a, b)
    if s != orig:
        open(path, 'w', encoding='utf8').write(s)
        changed.append(os.path.relpath(path, ROOT))


def put(src, dst_no_ext):
    """Write our PNG at dst (.png), removing a same-named .webp so the resource is not duplicated."""
    for old in glob.glob(dst_no_ext + '.webp'):
        os.remove(old)
        changed.append(os.path.relpath(old, ROOT) + ' (removed)')
    dst = dst_no_ext + '.png'
    if not os.path.exists(dst) or open(dst, 'rb').read() != open(src, 'rb').read():
        shutil.copyfile(src, dst)
        changed.append(os.path.relpath(dst, ROOT))



def sub_all(path, pairs):
    """Plain replace-all for names that repeat (asset names, paths); idempotent because the targets never contain the source."""
    s = open(path, encoding='utf8').read()
    n = s
    for a, b in pairs:
        n = n.replace(a, b)
    if n != s:
        open(path, 'w', encoding='utf8').write(n)
        changed.append(os.path.relpath(path, ROOT))


# 1. Icons: the installer/window icon in every format, and the in-app logos.
DI = f'{OUT}/desktop'
for base in ['nuvio-app-icon-transparent', 'app-icon-original-transparent']:
    for ext, src in [('icns', 'app.icns'), ('ico', 'app.ico'), ('png', 'icon-512.png')]:
        dst = f'{ICONS}/{base}.{ext}'
        if open(dst, 'rb').read() != open(f'{DI}/{src}', 'rb').read():
            shutil.copyfile(f'{DI}/{src}', dst)
            changed.append(os.path.relpath(dst, ROOT))
for f in glob.glob(f'{CR}/drawable/app_icon_*.png'):
    put(f'{OUT}/app_icon_original.png', os.path.splitext(f)[0])
for f in glob.glob(f'{CR}/drawable/app_logo_wordmark*.png'):
    put(f'{OUT}/app_logo_wordmark.png', os.path.splitext(f)[0])

# 2. Visible text: Nuvio -> Fusion Pass in every language.
for path in glob.glob(f'{CR}/values*/strings.xml'):
    s = open(path, encoding='utf8').read()
    n = re.sub(r'(<(?:string|item)[^>]*>)([^<]*)(<)', lambda m: m.group(1) + m.group(2).replace('Nuvio', 'Fusion Pass') + m.group(3), s)
    if n != s:
        open(path, 'w', encoding='utf8').write(n)
        changed.append(os.path.relpath(path, ROOT))

# 3. Installer identity: our name, ids and upgrade code (a real Nuvio install is left alone),
#    and the release file names (FusionPass-<OS>-<arch>-<version>.<ext>) in the build and workflow.
edit(G, [
    ('            packageName = "Nuvio"\n', '            packageName = "FusionPass"\n'),
    ('            vendor = "Nuvio Media"\n', '            vendor = "Fusion Pass"\n'),
    ('val windowsMsiUpgradeUuid = "395990ee-9b8a-3548-922c-e7a23a495b8d"', 'val windowsMsiUpgradeUuid = "6f1c2a4e-3d7b-4b8e-9a51-2c0f5e8d7b31" // Fusion Pass'),
    ('                                    <string>nuvio</string>\n                                    <string>stremio</string>\n', '                                    <string>fusionpass</string>\n'),
    ('                debMaintainer = "contact@nuvio.tv"', '                debMaintainer = "support@fusionpass.shop"'),
])
sub_all(G, [('com.nuvio.media.desktop', 'shop.fusionpass.desktop'), ('menuGroup = "Nuvio"', 'menuGroup = "Fusion Pass"'), ('"Nuvio-', '"FusionPass-')])
sub_all(WF, [
    ('com.nuvio.media.desktop', 'shop.fusionpass.desktop'),
    ('/app/Nuvio/Nuvio"', '/app/FusionPass/FusionPass"'),
    ('/app/Nuvio"', '/app/FusionPass"'),
    ('/bin/Nuvio"', '/bin/FusionPass"'),
    ('Nuvio-Linux-', 'FusionPass-Linux-'), ('Nuvio-Windows-', 'FusionPass-Windows-'), ('Nuvio-macOS-', 'FusionPass-macOS-'),
])

# 3b. No crash reporting (no Sentry project; nothing leaves the user's machine) and no Trakt keys
#     (tracking is hidden): the upstream workflow requires both, so drop those requirements and uploads.
sub_all(WF, [
    ('            SENTRY_AUTH_TOKEN\n            SENTRY_DESKTOP_DSN\n', ''),
    ('            TRAKT_CLIENT_ID\n            TRAKT_CLIENT_SECRET\n', ''),
    ('            :desktopSentry:sentryUploadSourceBundleJava \\\n', ''),
    ('            :desktopSentry:sentryUploadSourceBundleJava `\n', ''),
])

# 4. Update channel: this fork's releases.
edit(f'{D}/features/updater/AppUpdaterPlatform.desktop.kt', [
    ('        owner = "NuvioMedia",\n        repo = "NuvioDesktop",', '        owner = "oiefjqhio",\n        repo = "fusionpass-desktop",'),
])

# 5. Lock-down: never P2P (owner rule), no plugins, no donation or supporter pages for another
#    project under our name, no custom servers.
edit(f'{D}/core/build/AppFeaturePolicy.desktop.kt', [
    ('actual val pluginsEnabled: Boolean = true', 'actual val pluginsEnabled: Boolean = false'),
    ('actual val supportersContributorsPageEnabled: Boolean = true', 'actual val supportersContributorsPageEnabled: Boolean = false'),
    ('actual val donationActionsEnabled: Boolean = true', 'actual val donationActionsEnabled: Boolean = false'),
    ('actual val p2pEnabled: Boolean = true', 'actual val p2pEnabled: Boolean = false'),
    ('actual val customServerConnectionsEnabled: Boolean = true', 'actual val customServerConnectionsEnabled: Boolean = false'),
])

# 6. Window title, own data folders (never shares a real Nuvio install's data), no Discord presence
#    (it would announce "Nuvio" under Nuvio's Discord app).
edit(f'{D}/Main.kt', [('title = if (smokePlayerUrl == null) "Nuvio" else', 'title = if (smokePlayerUrl == null) "Fusion Pass" else')])
sub_all(f'{D}/core/storage/DesktopStorage.kt', [
    ('"Library/Application Support/Nuvio"', '"Library/Application Support/Fusion Pass"'),
    ('"Library/Caches/Nuvio"', '"Library/Caches/Fusion Pass"'),
    ('.resolve("Nuvio/Cache")', '.resolve("Fusion Pass/Cache")'),
    ('.resolve("Nuvio")', '.resolve("Fusion Pass")'),
    ('.resolve("nuvio")', '.resolve("fusionpass")'),
])
edit(f'{K}/features/settings/DiscordRichPresenceRepository.kt', [
    ('        get() = DiscordRichPresencePlatform.isSupported', '        get() = false // Fusion Pass: no Discord presence'),
])
edit(f'{D}/core/auth/DeviceSessionRegistration.desktop.kt', [('        clientName = "Nuvio Desktop",', '        clientName = "Fusion Pass Desktop",')])

# 5. The account comes fully configured: no addon manager, no debrid/metadata integrations, no
#    tracking services (Trakt/Simkl need our own API apps; owner chose to hide them).
def drop_row(path, handler, label):
    """Remove the settings row whose onClick is `handler` (and the divider above it)."""
    s = open(path, encoding='utf8').read()
    marker = f'// Fusion Pass: {label} row removed'
    pat = re.compile(r'\n([ ]*)SettingsGroupDivider\(isTablet = isTablet\)\n\1SettingsNavigationRow\(\n(?:\1    .*\n)*?\1    onClick = ' + handler + r',\n\1\)')
    n, c = pat.subn(lambda m: '\n' + m.group(1) + marker, s)
    if not c and marker not in s:
        sys.exit(f'rebrand: settings row {handler} not found in {path} (upstream changed; update rebrand.py)')
    if n != s:
        open(path, 'w', encoding='utf8').write(n)
        changed.append(os.path.relpath(path, ROOT))


SR = f'{K}/features/settings/SettingsRootPage.kt'
drop_row(SR, 'onContentDiscoveryClick', 'content discovery')
drop_row(SR, 'onIntegrationsClick', 'integrations')
drop_row(SR, 'onTrackingClick', 'tracking services')

# 6. Our own links.
edit(f'{K}/features/settings/SettingsRootPage.kt', [('"https://nuvio.tv/privacy-policy"', '"https://fusionpass.shop/privacy"')])
edit(f'{K}/features/auth/AuthScreen.kt', [('"https://nuvio.tv/terms"', '"https://fusionpass.shop/terms"')])
edit(f'{K}/core/auth/DeviceLinkAuthRepository.kt', [('"https://nuvio.tv/link"', '"https://sync.fusionpass.shop/link"')])

# 7. Names a user can see outside the string resources.
edit(f'{K}/features/settings/TrackingProviderCards.kt', [('    NUVIO("Nuvio"),', '    NUVIO("Fusion Pass"),')])
edit(f'{K}/features/library/LibraryRepository.kt', [('DEFAULT_LOCAL_LIBRARY_TAB_TITLE = "Nuvio Library"', 'DEFAULT_LOCAL_LIBRARY_TAB_TITLE = "Library"')])

# 8. No tracking services (Trakt/Simkl need our own API apps; owner chose to hide them). Library and
#    watch progress stay on our sync server. Settings search must not reopen any hidden page.
edit(f'{K}/features/settings/SettingsSearch.kt', [
    ("""    return entries
}

private data class PlaybackSearchRow(""", """    // Fusion Pass: pages removed from the settings root stay out of search too.
    val hidden = setOf(SettingsPage.ContentDiscovery, SettingsPage.Integrations, SettingsPage.TraktAuthentication, SettingsPage.Debrid)
    return entries.filterNot { e ->
        val p = (e.target as? SettingsSearchTarget.Page)?.page
        p != null && (p in hidden || p.parentPage in hidden)
    }
}

private data class PlaybackSearchRow("""),
])

# 9. Audio and subtitles (owner decision 2026-09-28): by default English audio, or Japanese for anime, with English
#    subtitles on. Nuvio defaults to the device language (Spanish on some dual-audio releases for Filipino-locale
#    phones) and subtitles off. The default is a setting of its own ("Auto"); a language the user picks still wins.
PL = f'{K}/features/player'
P = f'{PL}/PlayerSettingsRepository.kt'
edit(P, [
    ('    val preferredAudioLanguage: String = AudioLanguageOption.DEVICE,', '    val preferredAudioLanguage: String = AudioLanguageOption.FP_AUTO, // Fusion Pass'),
    ('    private var preferredAudioLanguage = AudioLanguageOption.DEVICE\n', '    private var preferredAudioLanguage = AudioLanguageOption.FP_AUTO // Fusion Pass\n'),
    ('        preferredAudioLanguage = AudioLanguageOption.DEVICE\n        secondaryPreferredAudioLanguage = null', '        preferredAudioLanguage = AudioLanguageOption.FP_AUTO // Fusion Pass\n        secondaryPreferredAudioLanguage = null'),
    ('            normalizeLanguageCode(PlayerSettingsStorage.loadPreferredAudioLanguage())\n                ?: AudioLanguageOption.DEVICE', '            normalizeLanguageCode(PlayerSettingsStorage.loadPreferredAudioLanguage())\n                ?: AudioLanguageOption.FP_AUTO // Fusion Pass'),
    ('    val preferredSubtitleLanguage: String = SubtitleLanguageOption.NONE,', '    val preferredSubtitleLanguage: String = "en", // Fusion Pass: English subtitles on'),
    ('    private var preferredSubtitleLanguage = SubtitleLanguageOption.NONE\n', '    private var preferredSubtitleLanguage = "en" // Fusion Pass\n'),
    ('        preferredSubtitleLanguage = SubtitleLanguageOption.NONE\n        secondaryPreferredSubtitleLanguage = null', '        preferredSubtitleLanguage = "en" // Fusion Pass\n        secondaryPreferredSubtitleLanguage = null'),
    ('            normalizeLanguageCode(PlayerSettingsStorage.loadPreferredSubtitleLanguage())\n                ?: SubtitleLanguageOption.NONE', '            normalizeLanguageCode(PlayerSettingsStorage.loadPreferredSubtitleLanguage())\n                ?: "en" // Fusion Pass'),
])
edit(f'{PL}/PlayerLanguagePreferences.kt', [
    ('    const val ORIGINAL = "original"\n}\n', '    const val ORIGINAL = "original"\n    const val FP_AUTO = "fpauto" // Fusion Pass: English, Japanese for anime (same value in every app: settings sync)\n    const val FP_AUTO_LABEL = "Auto (English, Japanese for anime)"\n}\n'),
    ('    contentOriginalLanguage: String? = null,\n): List<String> {', '    contentOriginalLanguage: String? = null,\n    isAnime: Boolean = false, // Fusion Pass\n): List<String> {'),
    ('    return when (primary) {\n        AudioLanguageOption.DEFAULT -> listOfNotNull(\n            normalize(secondaryPreferredAudioLanguage),\n        ).distinct()\n',
     '    return when (primary) {\n        AudioLanguageOption.FP_AUTO -> listOfNotNull(\n            "ja".takeIf { isAnime }, "en", normalize(secondaryPreferredAudioLanguage),\n        ).distinct() // Fusion Pass\n\n        AudioLanguageOption.DEFAULT -> listOfNotNull(\n            normalize(secondaryPreferredAudioLanguage),\n        ).distinct()\n'),
    ('    code.equals(AudioLanguageOption.DEFAULT, ignoreCase = true) ->\n        stringResource(Res.string.settings_playback_option_default)',
     '    code.equals(AudioLanguageOption.FP_AUTO, ignoreCase = true) -> AudioLanguageOption.FP_AUTO_LABEL // Fusion Pass\n    code.equals(AudioLanguageOption.DEFAULT, ignoreCase = true) ->\n        stringResource(Res.string.settings_playback_option_default)'),
    ('    code.equals(AudioLanguageOption.DEFAULT, ignoreCase = true) ->\n        getString(Res.string.settings_playback_option_default)',
     '    code.equals(AudioLanguageOption.FP_AUTO, ignoreCase = true) -> AudioLanguageOption.FP_AUTO_LABEL // Fusion Pass\n    code.equals(AudioLanguageOption.DEFAULT, ignoreCase = true) ->\n        getString(Res.string.settings_playback_option_default)'),
])
edit(f'{PL}/PlayerScreenRuntimeAudioPreferences.kt', [
    ('        contentOriginalLanguage = contentLanguage,\n    )\n', '        contentOriginalLanguage = contentLanguage,\n        isAnime = fpIsAnime, // Fusion Pass\n    )\n'),
])
FP_ANIME = '''package com.nuvio.app.features.player

// Fusion Pass: anime detection for the "Auto" audio default (Japanese audio; English subtitles come
// from the subtitle default). Written by fusionpass/rebrand.py.
internal val PlayerScreenRuntime.fpIsAnime: Boolean
    get() {
        val ids = listOfNotNull(activeVideoId, parentMetaId)
        if (ids.any { id -> listOf("kitsu:", "mal:", "anilist:", "anidb:").any { id.startsWith(it) } }) return true
        val meta = listOfNotNull(metaUiState.meta, playerMeta).firstOrNull { it.id == parentMetaId }
        val genres = meta?.genres.orEmpty()
        if (genres.any { it.equals("anime", ignoreCase = true) }) return true
        val animation = genres.any { it.equals("animation", ignoreCase = true) }
        return animation && (meta?.country?.contains("Japan", ignoreCase = true) == true || contentLanguage == "ja")
    }
'''
if not os.path.exists(f'{PL}/FusionPassAnimeAudio.kt') or open(f'{PL}/FusionPassAnimeAudio.kt', encoding='utf8').read() != FP_ANIME:
    open(f'{PL}/FusionPassAnimeAudio.kt', 'w', encoding='utf8').write(FP_ANIME)
    changed.append('features/player/FusionPassAnimeAudio.kt')
edit(f'{K}/features/settings/PlaybackSettingsPage.kt', [
    ('                        AudioLanguageOption.DEFAULT -> stringResource(Res.string.settings_playback_option_default)\n',
     '                        AudioLanguageOption.FP_AUTO -> AudioLanguageOption.FP_AUTO_LABEL // Fusion Pass\n                        AudioLanguageOption.DEFAULT -> stringResource(Res.string.settings_playback_option_default)\n'),
    ('            options = listOf(\n                LanguageSelectionOption(AudioLanguageOption.DEFAULT, stringResource(Res.string.settings_playback_option_default)),\n                LanguageSelectionOption(AudioLanguageOption.DEVICE,',
     '            options = listOf(\n                LanguageSelectionOption(AudioLanguageOption.FP_AUTO, AudioLanguageOption.FP_AUTO_LABEL), // Fusion Pass\n                LanguageSelectionOption(AudioLanguageOption.DEFAULT, stringResource(Res.string.settings_playback_option_default)),\n                LanguageSelectionOption(AudioLanguageOption.DEVICE,'),
])

# No debrid names anywhere (owner 2026-09-28): the account's sources are ours, so the cloud library
# (connect TorBox / Premiumize), their credits on Licenses, and the Connected Services page are gone.
import re as _re
def drop(path, pattern, what):
    s = open(path, encoding='utf8').read()
    n = _re.subn(pattern, '', s, flags=_re.S)
    if n[1] == 0 and not _re.search(r'Fusion Pass: no debrid', s):
        sys.exit(f'rebrand: {what} not found in {path} (upstream changed; update rebrand.py)')
    if n[1]:
        s = n[0]
        if 'Fusion Pass: no debrid' not in s:
            s = s.rstrip('\n') + '\n// Fusion Pass: no debrid credits or rows (rebrand.py)\n'
        open(path, 'w', encoding='utf8').write(s)
        changed.append(os.path.relpath(path, ROOT))
drop(f'{K}/features/settings/LicensesAttributionsPage.kt',
     r'    AttributionItem\(\n        titleRes = Res\.string\.settings_licenses_attributions_(?:premiumize|torbox)_title,.*?\n    \),\n',
     'Premiumize/TorBox attribution items')
drop(f'{K}/features/settings/SettingsSearch.kt',
     r'        PlaybackSearchRow\("(?:premiumize|torbox)-attribution".*?\n', 'Premiumize/TorBox search rows')
edit(f'{K}/features/library/LibraryScreen.kt', [
    ('private fun LibrarySourceSwitch(\n    selectedMode: LibraryViewMode,\n    onModeSelected: (LibraryViewMode) -> Unit,\n    modifier: Modifier = Modifier,\n) {\n',
     'private fun LibrarySourceSwitch(\n    selectedMode: LibraryViewMode,\n    onModeSelected: (LibraryViewMode) -> Unit,\n    modifier: Modifier = Modifier,\n) {\n    if (true) return // Fusion Pass: no cloud library (debrid accounts)\n'),
])

# 12. Linux (owner 2026-09-29): DEB, RPM and AppImage under our name; no Flatpak (sandboxed, cannot
#     self-update, and its AppStream file is all upstream branding). jpackage installs to
#     /opt/fusionpass with the launcher bin/FusionPass and icon lib/FusionPass.png (packageName).
L = f'{ROOT}/scripts/linux'
edit(f'{L}/configure-desktop-runtime.sh', [
    ('    SENTRY_AUTH_TOKEN\n    SENTRY_DESKTOP_DSN\n', ''),
    ('    TRAKT_CLIENT_ID\n    TRAKT_CLIENT_SECRET\n', ''),
])
edit(f'{L}/linux-shortcut-definition.sh', [
    ('NUVIO_LINUX_SHORTCUT_RELATIVE_PATH="usr/share/applications/nuvio.desktop"', 'NUVIO_LINUX_SHORTCUT_RELATIVE_PATH="usr/share/applications/fusionpass.desktop"'),
    ('NUVIO_LINUX_SHORTCUT_NAME="Nuvio"', 'NUVIO_LINUX_SHORTCUT_NAME="Fusion Pass"'),
    ('NUVIO_LINUX_SHORTCUT_COMMENT="Nuvio Media Player"', 'NUVIO_LINUX_SHORTCUT_COMMENT="Movies, series and anime"'),
    ('NUVIO_LINUX_SHORTCUT_MIME_TYPES="x-scheme-handler/nuvio;x-scheme-handler/stremio;"', 'NUVIO_LINUX_SHORTCUT_MIME_TYPES="x-scheme-handler/fusionpass;"'),
    ('"/opt/nuvio/bin/Nuvio %u" "/opt/nuvio/lib/Nuvio.png"', '"/opt/fusionpass/bin/FusionPass %u" "/opt/fusionpass/lib/FusionPass.png"'),
])
# AppImage: file names without the space in "Fusion Pass"; the menu name stays in Name=.
edit(f'{L}/build-appimage.sh', [
    ('app_dir="$work_dir/Nuvio.AppDir"', 'app_dir="$work_dir/FusionPass.AppDir"'),
    ('desktop_file="$app_dir/${NUVIO_LINUX_SHORTCUT_NAME}.desktop"\nnuvio_linux_write_desktop_entry_file "$desktop_file" "AppRun %u" "$NUVIO_LINUX_SHORTCUT_NAME"',
     'desktop_file="$app_dir/fusionpass.desktop"\nnuvio_linux_write_desktop_entry_file "$desktop_file" "AppRun %u" "fusionpass"'),
    ('icon_source="$app_dir/lib/Nuvio.png"', 'icon_source="$app_dir/lib/FusionPass.png"'),
    ('cp "$icon_source" "$app_dir/${NUVIO_LINUX_SHORTCUT_NAME}.png"\nln -sf "${NUVIO_LINUX_SHORTCUT_NAME}.png" "$app_dir/.DirIcon"',
     'cp "$icon_source" "$app_dir/fusionpass.png"\nln -sf "fusionpass.png" "$app_dir/.DirIcon"'),
    ('executable_path="$here/bin/Nuvio"\nif [[ ! -x "$executable_path" ]]; then\n    executable_path="$here/bin/nuvio"',
     'executable_path="$here/bin/FusionPass"\nif [[ ! -x "$executable_path" ]]; then\n    executable_path="$here/bin/fusionpass"'),
])
edit(f'{L}/patch-linux-rpm.sh', [('    summary="Nuvio"', '    summary="Fusion Pass"'), ('    vendor="Nuvio Media"', '    vendor="Fusion Pass"')])
# The package checks expect our maintainer and vendor (set in build.gradle.kts, section 3).
edit(f'{L}/verify-linux-deb.sh', [('expected_maintainer="Nuvio Media <contact@nuvio.tv>"', 'expected_maintainer="Fusion Pass <support@fusionpass.shop>"')])
edit(f'{L}/verify-linux-rpm.sh', [('if [[ "$vendor" != "Nuvio Media" ]]; then', 'if [[ "$vendor" != "Fusion Pass" ]]; then'), ('    echo "Expected: \'Nuvio Media\'" >&2', '    echo "Expected: \'Fusion Pass\'" >&2')])
edit(WF, [
    ("    name: Linux x64 - Flatpak\n    if: inputs.mode != 'dry-run' && (inputs.target == 'all' || inputs.target == 'linux')",
     "    name: Linux x64 - Flatpak\n    if: false # Fusion Pass: no Flatpak"),
    ('      - linux_flatpak\n      - linux_deb', '      - linux_deb'),
    ('APPIMAGE_WEBSITE_URL="https://github.com/NuvioMedia/NuvioDesktop"', 'APPIMAGE_WEBSITE_URL="https://fusionpass.shop"'),
])

print('rebrand: ok,', len(changed), 'changes')
for c in changed[:60]:
    print('  ', c)
