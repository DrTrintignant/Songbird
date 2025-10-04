SONGBIRD PLUGIN FOR COVAS NEXT
================================

Voice-controlled sound effects for COVAS NEXT. Play sounds from Freesound, manage local audio files, and bind sounds to custom voice commands with random playback.

## What It Does

- Play sound effects from Freesound by voice
- Play custom audio files (drag-and-drop MP3, OGG, WAV)
- Control playback (pause, resume, stop, volume)
- **Bind multiple sounds to one phrase** - Create variety packs that play randomly
- **Instant phrase triggers** - Say "kaboom" to instantly play your bound explosion sound
- Cache sounds locally for instant replay

## Installation

### 1. Get Freesound API Key

1. Go to [Freesound.org](https://freesound.org/) and register
2. Go to Settings → API Keys
3. Click "Create new API Key"
4. Copy the API key

### 2. Install Plugin

1. Place the `Songbird` folder in: `%appdata%\com.covas-next.ui\plugins\`

2. Create `api_key.txt` in the plugin folder and paste your API key (no quotes, just the key)

3. Restart COVAS NEXT

4. Test with: "Test SONGBIRD plugin"

## Voice Commands

### Playing Sounds

```
"Play explosion sound"
"Play another explosion"
"Play it again"
"Play [your filename]"
"Play wrong one"  (matches "Wrong 1.mp3")
```

### Playback Control

```
"Stop sound"
"Pause sound" / "Resume sound"
"Volume up" / "Volume down"
"Set volume to 50%"
"Mute" / "Unmute"
```

### Binding System

**Create a single binding:**
1. Play any sound
2. Say: "Bind this to [phrase]"
   - Example: "Bind this to kaboom"

**Create a multi-sound binding (random playback):**
Say: "Bind [sound1], [sound2], [sound3] to [phrase]"
- Example: "Bind Login 1, Login 2, Login 3 to login sound"
- Each time you say "login sound", a random Login sound plays

**Play bound sound:**
- Just say the phrase: "Kaboom" or "Login sound"
- If multiple sounds are bound, one plays randomly each time

**Manage bindings:**
```
"List bound sounds"
"List cached sounds"  (see what's available to bind)
"Unbind kaboom"
"Unbind all sounds"
```

Bindings are stored in `bound_sounds.json` and work with punctuation/case variations.

### Custom Audio Files

Drop any MP3, OGG, or WAV file into the `sounds/` folder.

Example: Drop `My Song.mp3` → Say "Play my song"

## Advanced Features

### Random Sound Variety

Create variety packs by binding multiple sounds to one phrase:

**Example: Login sounds**
```
YOU: "Bind Login 1, Login 2, Login 3, Login 4, Login 5 to password correct"
COVAS: "Bound 5 sounds to phrase 'password correct'"

YOU: "Password correct"
COVAS: [plays random login sound]

YOU: "Password correct"
COVAS: [plays different random login sound]
```

**Example: Building a variety pack progressively**
```
1. "Play explosion sound"
2. "Bind this to kaboom"
3. "Play another explosion"
4. "Bind this to kaboom"  (adds to existing phrase)
5. Repeat for variety
6. Say "Kaboom" → random explosion each time
```

### Using Bindings with COVAS Memory

Combine bindings with COVAS instructions for advanced behaviors.

**Login System:**
```
Tell COVAS: "When I say 'Hello COVAS', ask for password. 
Password is 'Blue sky'. If correct, say 'password correct'. 
If wrong, say 'access denied'."

Then bind sounds:
- "Bind Login 1, Login 2, Login 3 to password correct"
- "Bind Wrong 1, Wrong 2, Wrong 3 to access denied"
```

**Action Triggers:**
```
Tell COVAS: "When I say 'docking complete', trigger docking sound"
Then bind your docking sounds to "docking sound"
```

**Note**: COVAS instructions exist only in session memory (lost on restart). Sound bindings persist permanently. To make instructions permanent, add them to COVAS's system prompt.

## Troubleshooting

**Plugin won't load**
- Restart COVAS NEXT completely
- Check COVAS logs for errors

**No sounds playing**
- Verify `api_key.txt` contains your Freesound API key
- Check internet connection (required for downloads)
- Try different search terms

**Bindings not working**
- Say "List bound sounds" to verify binding exists
- After updating to v1.2.0: Old bindings still work (backwards compatible)
- Bound phrases play immediately - no "play" command needed

**Can't find my custom files**
- Say "List cached sounds" to see all available files
- Verify filename matches what you say
- Restart COVAS if you just added files
- Try variations: "dial-up" vs "dial up"

**Random selection not working**
- Verify multiple sounds are bound: "List bound sounds"
- Check COVAS logs to confirm plugin version 1.2.0+
- Restart COVAS to reload updated plugin

## Files

```
Songbird/
├── Songbird.py          # Main plugin
├── manifest.json        # Plugin metadata
├── api_key.txt          # Your API key (create this)
├── bound_sounds.json    # Your bindings (auto-created)
├── deps/                # Bundled dependencies
└── sounds/              # Audio files (auto-created)
```

## What's New in v1.2.0

- **Multi-sound bindings**: Bind multiple sounds to one phrase
- **Random selection**: Automatically picks different sound each time
- **Batch binding**: Bind many sounds at once with one command
- **Better matching**: Improved file name recognition ("wrong one" finds "Wrong 1.mp3")
- **List cached sounds**: See all available audio files

## Credits

**Author**: D. Trintignant  
**Version**: 1.2.0  
**COVAS NEXT**: https://ratherrude.github.io/Elite-Dangerous-AI-Integration/  
**Freesound API**: https://freesound.org/
**License**: MIT
