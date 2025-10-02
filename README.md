SONGBIRD PLUGIN FOR COVAS NEXT
================================

OVERVIEW
--------
Voice-controlled sound effects plugin for COVAS NEXT. Downloads sounds from Freesound API, manages local audio library, and provides sound binding system for custom voice commands.

NEW in v1.1.0: Drop any MP3, OGG, or WAV file into the sounds folder and play them by name - no renaming required!

IMPORTANT: See Prompt_examples.txt for advanced usage patterns including login/logout procedures, action-triggered sounds, and creative ways to use the binding system with COVAS's conversational memory.

INSTALLATION
------------

STEP 1: GET FREESOUND API KEY
1. Open your web browser and go to: https://freesound.org/
2. Click "Register" in the top right corner
3. Create a free account with username, email, and password
4. Check your email and click the confirmation link
5. Log back into Freesound
6. Click your username (top right) -> Settings -> API Keys
7. Click "Create new API Key"
8. Copy the long string of letters/numbers that appears

STEP 2: INSTALL PLUGIN IN COVAS NEXT
1. Download and extract the SONGBIRD plugin files
2. Open File Explorer and type in address bar: %appdata%
3. Navigate to: com.covas-next.ui -> plugins
4. Create new folder named "Songbird"
5. Copy all plugin files into the Songbird folder

STEP 3: CREATE API KEY FILE
1. Inside your Songbird plugin folder, right-click empty space
2. Choose New -> Text Document
3. Name it: api_key.txt
4. Open the file with Notepad
5. Paste your Freesound API key (no quotes, no extra spaces)
6. Save and close the file

STEP 4: TEST INSTALLATION
1. Restart COVAS NEXT completely
2. Say: "Test SONGBIRD plugin"
3. Should confirm plugin is active with API key loaded

VOICE COMMANDS
--------------
Sound Playback:
- "Play [description] sound" - Downloads and plays from Freesound
- "Play another [description]" - Gets different sound from Freesound
- "Play it again" - Replays last sound from cache
- "Play [your filename]" - Plays any custom audio file you've added
- Examples: "Play explosion sound", "Play jazz music", "Play my favorite song"

Sound Binding:
- "Bind this to [phrase]" - Bind current sound to custom phrase
- "[your phrase]" - Plays bound sound (case-insensitive)
- "List bound sounds" - Show all sound bindings
- "Unbind [phrase]" - Remove specific binding
- "Unbind all sounds" - Clear all bindings

Audio Control:
- "Stop sound"
- "Pause sound" 
- "Resume sound"
- "Mute" / "Unmute"
- "Volume up" / "Volume down"
- "Set volume to [number]%"

Testing:
- "Test SONGBIRD plugin" - Check plugin status and API key

FUNCTIONALITY
-------------
Sound Discovery:
- Multi-page Freesound search (up to 75 results per query)
- Random selection for variety
- Automatic download and caching
- Intelligent keyword detection ("another" vs "again")

Local Sound Management:
- Downloaded sounds saved to sounds/ folder
- Automatic cache replay for "play it again" requests
- Intelligent name matching (case-insensitive, partial matching)
- Supports MP3, OGG, WAV formats
- Universal filename support - any naming convention works

Sound Binding System:
- Bind any sound to custom voice commands
- Case-insensitive phrase matching ("HELLO COVAS" = "hello covas")
- Persistent storage in bound_sounds.json
- Survives COVAS restarts and computer reboots
- Unbind individual phrases or clear all bindings
- Works with both Freesound downloads and custom files

Audio Engine:
- Pygame-based audio playback
- Volume control (0-100%)
- Pause/resume/stop capability
- Multiple format support

CUSTOM AUDIO FILES (v1.1.0)
---------------------------
Drop Your Own Sounds:
- Simply drag-and-drop any MP3, OGG, or WAV file into the sounds/ folder
- No renaming required - plugin automatically handles any filename format
- Play by saying the filename without extension: "Play [your filename]"
- Examples:
  - File: "My Favorite Song.mp3" → Say: "Play my favorite song"
  - File: "alarm_sound.mp3" → Say: "Play alarm sound"
  - File: "SFX Explosion.mp3" → Say: "Play SFX explosion"
  - File: "piano birds.mp3" → Say: "Play piano birds"

How It Works:
- Plugin detects Freesound downloads (name_12345.mp3 format) and removes the ID
- User files keep their full names (underscores converted to spaces)
- Supports any filename - no special format required
- All custom files work with binding system ("Bind this to [phrase]")
- Case-insensitive matching for natural voice commands

FOLDER STRUCTURE
----------------
Songbird/
├── Songbird.py          # Main plugin code
├── manifest.json        # Plugin metadata
├── requirements.txt     # Dependencies list
├── __init__.py          # Module init
├── api_key.txt          # Your Freesound API key (you create this)
├── bound_sounds.json    # Sound bindings (auto-created)
├── deps/                # Bundled dependencies folder
│   ├── requests/        # HTTP library for API calls
│   └── requests-2.32.5.dist-info/
└── sounds/              # Downloaded audio files AND your custom files (auto-created)

FILE FORMATS
------------
Supported audio: .mp3, .ogg, .wav

Downloaded sounds (from Freesound):
- Format: [description]_[id].[extension]
- Example: explosion_sound_12345.mp3
- Plugin automatically removes ID when displaying name

User-provided sounds (drag-and-drop):
- Any filename works: My_Song.mp3, Track 01.mp3, alarm.wav, SFX_Explosion.mp3
- Plugin uses full filename (without extension) as sound name
- Underscores converted to spaces for natural voice commands
- No special naming format required

TROUBLESHOOTING
---------------
Plugin not loading:
- Check manifest.json syntax
- Verify Songbird.py has no syntax errors
- Restart COVAS NEXT completely
- Check COVAS logs for Python errors

No sounds playing:
- Check api_key.txt exists and contains valid key
- Verify internet connection (for Freesound downloads)
- Check COVAS NEXT logs for errors
- Ensure pygame is installed: pip install pygame

Permission errors:
- Ensure plugin folder is writable
- Check Windows audio permissions
- Verify pygame installation

Sound not found:
- Try different search terms
- Use "another [sound]" for variety
- Verify Freesound API key is valid
- For custom files, check filename matches your voice command

Binding issues:
- Phrases are case-insensitive (any case works)
- Use "list bound sounds" to see all bindings
- Unbind and rebind to update a phrase
- Check bound_sounds.json file exists

API key errors:
- Register at freesound.org
- Generate new API key in developer section
- Replace content in api_key.txt
- Restart COVAS NEXT

Custom file not recognized:
- Check file is in sounds/ folder
- Verify file extension is .mp3, .ogg, or .wav
- Say filename without extension
- Restart COVAS NEXT if file was just added

TECHNICAL NOTES
---------------
- Sounds downloaded to sounds/ folder
- Bindings stored in bound_sounds.json
- Both persist between sessions
- API calls limited by Freesound rate limits
- Audio playback uses system default device
- Case-insensitive phrase matching
- Multi-page search for variety (5 pages, 75 results)
- Intelligent filename parsing (Freesound vs user files)

TESTING
-------
1. Say: "Test SONGBIRD plugin"
2. Should confirm API key status and plugin version
3. Try: "Play explosion sound"
4. Try: "Bind this to test phrase"
5. Try: "test phrase" (should play bound sound)
6. Drop a custom MP3 in sounds/ folder and play it by name
7. Check COVAS NEXT logs for detailed information

LOG INFORMATION
---------------
All plugin activity logged with "SONGBIRD:" prefix
Check logs for:
- API key loading status
- Sound search results (pages searched, results found)
- Download progress
- Playback status
- Binding operations
- Local sound file detection
- Error details

VERSION INFORMATION
-------------------
Plugin Version: 1.1.0
Author: D. Trintignant
Compatible with: COVAS NEXT (source installations)
Dependencies: pygame, requests
API: Freesound.org v2

FEATURES
--------
- Natural language sound search
- Multi-page Freesound search (75 results per query)
- Random sound selection for variety
- Local sound caching
- Intelligent replay detection
- Sound binding to custom phrases
- Case-insensitive phrase matching
- Unbind functionality (specific or all)
- Volume control
- Pause/resume/stop controls
- Universal filename support - drag-and-drop any audio file
- Automatic filename parsing (Freesound vs user files)

CHANGELOG
---------
v1.1.0:
- Added universal filename support for custom audio files
- Intelligent parsing detects Freesound downloads vs user files
- No renaming required for drag-and-drop files
- Improved filename matching (underscores to spaces)

v1.0.0:
- Initial release
- Freesound API integration
- Sound binding system
- Local caching
- Volume control
