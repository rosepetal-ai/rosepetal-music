# Sonidos

## SFXMint · CC0 · generados por IA

Descargados el 2026-11-04 con el conector de SFXMint (`https://sfxmint.com/mcp`), sin clave.

- **Licencia:** CC0 1.0, sin atribución obligatoria. Se pueden usar en los vídeos de Rosepetal sin restricciones.
- **Generados por IA:** si algo hecho con ellos se publica en Steam o itch.io, hay que declararlo. Guía: https://sfxmint.com/guides/steam-ai-disclosure-sound-effects
- **Ubicación:** [samples/SFXMint/](samples/SFXMint/). Son los originales sin procesar (WAV de 44,1 kHz, 16 bits, estéreo). El servidor sirve cada uno como un banco `sfx_<nombre>`.

| Banco Strudel | Archivo | Duración | Afinación medida | Página | SHA-256 |
|---|---|---|---|---|---|
| `sfx_ambience_rain_21` | ambience-rain-21.wav | 10,0 s | — | https://sfxmint.com/sounds/ambience-rain-21 | `515a07cdb881f6f2f1c62a9a25e8023ecfb7ba3721095e7ed877ca67d2e71541` |
| `sfx_ambience_fireplace_42` | ambience-fireplace-42.wav | 11,0 s | — | https://sfxmint.com/sounds/ambience-fireplace-42 | `d7494bf290cadcb1185573530e0dbbf74b3c569858f792b3c361770a6af346d6` |
| `sfx_piano_major_chord_01` | piano-major-chord-01.wav | 3,3 s | Do mayor (Do4) | https://sfxmint.com/sounds/piano-major-chord-01 | `232114ce4fa4697c06c93110fd540672539382320ff0aef679ff362920d13083` |
| `sfx_flute_note_01` | flute-note-01.wav | 3,4 s | Do5 (entra un poco alta y se asienta) | https://sfxmint.com/sounds/flute-note-01 | `0e6c8aeea26040a6cdf074f7b127683e78779268578766f0b99acc65e9b4036f` |
| `sfx_wind_chimes_settle_01` | wind-chimes-settle-01.wav | 2,5 s | — | https://sfxmint.com/sounds/wind-chimes-settle-01 | `4ffc39afc02877f611c4344791972ee64f102f1233427f3be66fe59d410dc1b0` |
| `sfx_violin_sting_09` | violin-sting-09.wav | 1,0 s | La4 (pizzicato) | https://sfxmint.com/sounds/violin-sting-09 | `fa9248f3762fad66628e6a647315a19b73cd1da91a6db05d978c38b2cec7d531` |
| `sfx_acoustic_drum_kit_kick_01` | acoustic-drum-kit-kick-01.wav | 1,25 s | — | https://sfxmint.com/sounds/acoustic-drum-kit-kick-01 | `c84647c8f7f2ee8b3a5d0e2f74813a609b8cd4de912fcffaf727e96c05d7ce61` |
| `sfx_acoustic_drum_kit_floor_tom_01` | acoustic-drum-kit-floor-tom-01.wav | 3,0 s | Do2 | https://sfxmint.com/sounds/acoustic-drum-kit-floor-tom-01 | `e485426278abe5f0dd5dd0f36f803e1a9df6fd7513124f0c617f7ecaa1ea0c8a` |
| `sfx_acoustic_drum_kit_snare_01` | acoustic-drum-kit-snare-01.wav | 1,5 s | — | https://sfxmint.com/sounds/acoustic-drum-kit-snare-01 | `467bf419366117e66d4047161ebcce9dc29616b57b931d1afb1e67f38fc27e33` |
| `sfx_acoustic_drum_kit_snare_cross_stick_01` | acoustic-drum-kit-snare-cross-stick-01.wav | 2,0 s | — | https://sfxmint.com/sounds/acoustic-drum-kit-snare-cross-stick-01 | `874ca9f42f2d08ef7f91c2dc6eb8f4ce1ef1e5b068f0efead62ca3b6c16ab04e` |
| `sfx_acoustic_drum_kit_crash_01` | acoustic-drum-kit-crash-01.wav | 6,0 s | — | https://sfxmint.com/sounds/acoustic-drum-kit-crash-01 | `c5876f39c6a2010f4f23bea3a03d2e699f63fb254685ac084076ff7de8d7b946` |

Para afinar un sample melódico en Strudel: `speed = 2^(semitonos / 12)` desde su nota medida.

## VCSL · CC0 · piano Steinway B

- **Origen:** [Versilian Community Sample Library](https://github.com/sgossner/VCSL) (VCSL), carpeta `Chordophones/Zithers/Grand Piano, Steinway B/Sus`, capa de dinámica `vl4`, primera variación (`rr1`). Descargado el 2026-11-04.
- **Licencia:** CC0 1.0 (archivo LICENSE de VCSL), sin atribución obligatoria.
- **Procesado:** los originales son WAV de 24 bits y hasta ~25 s (134 MB las 22 notas). Se recortaron a 5 s con un fundido de 0,6 s y se pasaron a 16 bits, misma frecuencia (44,1 kHz) y estéreo. Nombre nuevo: `steinway_<nota>.wav`, con `s` por sostenido (`steinway_Fs4.wav` = Fa#4). Do4 medido después: Do4 exacto.
- **Ubicación:** [samples/VCSL/steinway/](samples/VCSL/steinway/): 22 notas, de Sol#2 a Re6, cada una tercera mayor. El servidor las sirve como un solo banco afinado, `steinway`: con `note("c4 e4").s("steinway")` Strudel elige la muestra más cercana y la transpone.

| Archivo | SHA-256 (procesado) |
|---|---|
| steinway_As2.wav | `6bbacb54df37c50f47c3f77911e892a4e1e0d151ff3267310716b16981ff1d66` |
| steinway_As3.wav | `e5a3dd1aee0bcc02b89c1eb5247de8f1862315ab7c981b401e33f70a46c3c4d3` |
| steinway_As4.wav | `693f72d7ced66e450b4702f2311b8ed996ad007736f373a92b5c00834f690019` |
| steinway_As5.wav | `313a4cbc1eea40aa0e5ce66d3e6d285d22a9e65488332651ce99d822d1e4aea9` |
| steinway_C3.wav | `7e5748232e65d9ee505db7edfbe265d890aa947116e395b65038da9a172e2846` |
| steinway_C4.wav | `be281c6965193ec677cf0c490ceaaf3b7c9b6cba17e8122c8a7288e8812ac7c4` |
| steinway_C5.wav | `0647f93472ddb6cfdb39f482b5772e926a50efd8b050c0a6e1906062f9782053` |
| steinway_C6.wav | `da531da83260ff993ca516ba4b581fd0145131a861da4c1b208e8ccda092dbdf` |
| steinway_D3.wav | `64ac91f56c52a6ba11720f1ad9e04f454e6458c239ec6ce4dbeafa7efe2f016d` |
| steinway_D4.wav | `9f6367156032d4e8e5f36899ea3be2cc44562eb3554eae5cbe05e081682b1004` |
| steinway_D5.wav | `6c8f2ee341133ea8a91475c4fd18471795ddfeab67e531ead44790a2709dc7f3` |
| steinway_D6.wav | `f243f8cf31b5e131b50987961fba57aa6fa21db141b3ea8b9ba747e00d703501` |
| steinway_E3.wav | `ecfe88cc443b3419a1ca0cb918a3931fa541cd8b84f833733caf777c187fb454` |
| steinway_E4.wav | `a92b91b30209bfb4db1a802affc544429d30dd519e1a4ebc612151fd23bcb25f` |
| steinway_E5.wav | `cc40f93a748bd77e155ee6bc4978e454bf73f77676f2ec80bd240b1d5dc9de5b` |
| steinway_Fs3.wav | `75f0ab68d7bab6d737e8cedc29edb8be645476d6a0859a21f989fd31a6b1a25b` |
| steinway_Fs4.wav | `cac2cb093359e0c8bf081268427dd55e27aad14114037aa5d08c7302f59b94f9` |
| steinway_Fs5.wav | `d5877dfd06c28e1227e0ca88bf29fd7600b8f36274a35d0c1a5d14eb2e674c21` |
| steinway_Gs2.wav | `72549f7c47d63f70212a280e56bda49ca21071595f67cfef9f4d25a4cc362ab3` |
| steinway_Gs3.wav | `42d1df972e67f1048823fad81c02204af10fe9e7f95b2a7d03aecd5f4d0bd6d8` |
| steinway_Gs4.wav | `daccb54ac3c8b5281e86585b2a8aea63898a44ac97258c1e4b825681e427da0d` |
| steinway_Gs5.wav | `03f3c642cafd68a9bd3a8338b02436d458bef0702aaee5b8843b6a849a0bbd18` |

## Missing

- **Nota suelta de piano:** SFXMint solo tiene acordes; se usa el Steinway de VCSL. Para generarla en SFXMint Studio: https://sfxmint.com/s/e7e5493175
- **Nota de cello:** ni SFXMint ni VCSL la tienen; en las piezas 02, 03 y 04 los cellos son sintetizados (diente de sierra filtrado con vibrato) y hacen de sustitutos.
- **Nota de violín sostenida:** SFXMint solo tiene golpes cortos de violín; en la 04 el violín del estribillo es sintetizado. Para generarla en SFXMint Studio: https://sfxmint.com/s/7495da6924 Para generarla en SFXMint Studio: https://sfxmint.com/s/627945ff78
- **Pizzicato de contrabajo:** se usa como sustituto el pizzicato de violín (`violin-sting-09`) transpuesto hacia abajo, con un seno grave debajo.
