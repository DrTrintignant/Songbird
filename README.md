SONGBIRD PLUGIN FOR COVAS NEXT
================================

Voice-controlled sound effects for COVAS NEXT. Play sounds from Freesound, manage local audio files, and bind sounds to custom voice commands.

## What It Does

- Play sound effects from Freesound by voice
- Play custom audio files (drag-and-drop MP3, OGG, WAV)
- Control playback (pause, resume, stop, volume)
- **Bind sounds to custom phrases** - Say "kaboom" to instantly play your bound explosion sound
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

**Create a binding:**
1. Play any sound
2. Say: "Bind this to [phrase]"
   - Example: "Bind this to kaboom"

**Play bound sound:**
- Just say the phrase: "Kaboom"

**Manage bindings:**
```
"List bound sounds"
"Unbind kaboom"
"Unbind all sounds"
```

Bindings are stored in `bound_sounds.json` and work with punctuation/case variations.

### Custom Audio Files

Drop any MP3, OGG, or WAV file into the `sounds/` folder.

Example: Drop `My Song.mp3` → Say "Play my song"

## Advanced: Using Bindings with COVAS Memory

Combine bindings with COVAS instructions for advanced behaviors.

**Login System:**
```
Tell COVAS: "When I say 'Hello COVAS', ask for password. 
Password is 'Blue sky'. If correct, play welcome sound. 
If wrong, play denial sound."

Then bind sounds to "welcome" and "denial"
```

**Action Triggers:**
```
Tell COVAS: "When I say 'docking complete', play docking sound"
Then bind your docking sound to "docking complete"
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
- After updating to v1.1.0: Delete `bound_sounds.json` and rebind (new format)
- Bound phrases play immediately - no "play" command needed

**Sound not found**
- Try "play another [description]" for variety
- For custom files: Verify filename matches what you say
- Restart COVAS if you just added files

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

## Credits

**Author**: D. Trintignant  
**Version**: 1.1.0  
**COVAS NEXT**: https://ratherrude.github.io/Elite-Dangerous-AI-Integration/  
**Freesound API**: https://freesound.org/
**License**: MIT
