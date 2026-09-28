package com.nuvio.app.features.player

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
