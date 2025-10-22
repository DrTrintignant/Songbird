from typing import override
import json
import os
import sys
import string  # Added for punctuation stripping
import re  # Moved from inside function
import random  # For random sound selection in bindings

# Set up deps path BEFORE importing pygame and requests
current_dir = os.path.dirname(os.path.abspath(__file__))
deps_path = os.path.join(current_dir, 'deps')
if deps_path not in sys.path:
    sys.path.insert(0, deps_path)

# NOW import pygame and requests (they'll be found in deps/)
import pygame
import requests

from lib.PluginHelper import PluginHelper, PluginManifest
from lib.PluginSettingDefinitions import PluginSettings, SettingsGrid, TextSetting, ToggleSetting
from lib.Logger import log
from lib.EventManager import Projection
from lib.PluginBase import PluginBase
from lib.Event import Event

# Main plugin class
class SONGBIRD(PluginBase):
    def __init__(self, plugin_manifest: PluginManifest):
        super().__init__(plugin_manifest)
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            log('info', 'SONGBIRD: pygame mixer initialized')
        except Exception as e:
            log('error', f'SONGBIRD: Failed to initialize pygame mixer: {str(e)}')

        # Track currently playing sound for binding system
        self.current_playing = None
        self.last_played_description = None

        # Minimal empty settings configuration (required for COVAS NEXT)
        self.settings_config: PluginSettings | None = PluginSettings(
            key="SONGBIRDPlugin",
            label="SONGBIRD Sound Integration",
            icon="volume_up",
            grids=[]
        )
    
    def normalize_phrase(self, phrase: str) -> str:
        """Normalize phrase for matching: lowercase + strip punctuation + trim whitespace"""
        if not phrase:
            return ""
        # Remove punctuation
        cleaned = phrase.translate(str.maketrans('', '', string.punctuation))
        # Remove extra whitespace and lowercase
        return ' '.join(cleaned.lower().split())
    
    def convert_word_numbers_to_digits(self, text: str) -> str:
        """Convert word numbers (one, two, three) to digit numbers (1, 2, 3)"""
        word_to_digit = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20'
        }
        
        words = text.split()
        converted = []
        for word in words:
            if word.lower() in word_to_digit:
                converted.append(word_to_digit[word.lower()])
            else:
                converted.append(word)
        
        return ' '.join(converted)
    
    @override
    def register_actions(self, helper: PluginHelper):
        helper.register_action(
            'songbird_play_sound', 
            "Play any sound request including: new sounds from Freesound, replay requests (play again, replay, play it again, replay last song, replay it), and cached sound playback. Use cache for replay requests, Freesound for new/different sounds.", 
            {
                "type": "object",
                "properties": {
                    "sound_description": {
                        "type": "string",
                        "description": "Natural language description of the sound to play, including replay requests like 'last song', 'it', 'that sound'"
                    },
                    "replay_mode": {
                        "type": "string",
                        "description": "Whether this is a replay request ('again', 'same') or new request ('another', 'different', 'new')",
                        "enum": ["again", "new", "auto"]
                    },
                    "context": {
                        "type": "string", 
                        "description": "Optional context about when/why this sound should play"
                    }
                },
                "required": ["sound_description"]
            }, 
            self.songbird_play_sound, 
            'global'
        )

        helper.register_action(
            'songbird_control', 
            "Control audio playback with voice commands like stop, pause, resume, volume up/down, or set specific volume levels.", 
            {
                "type": "object",
                "properties": {
                    "voice_command": {
                        "type": "string",
                        "description": "The complete voice command as spoken by the user"
                    }
                },
                "required": ["voice_command"]
            }, 
            self.songbird_control, 
            'global'
        )

        helper.register_action(
            'songbird_test', 
            "Test the SONGBIRD plugin functionality.", 
            {
                "type": "object",
                "properties": {}
            }, 
            self.songbird_test, 
            'global'
        )

        helper.register_action(
            'songbird_bind_sound', 
            "Bind the last played sound to a specific command phrase for future replay. If the phrase already exists, adds this sound to that phrase's sound list (for random selection).", 
            {
                "type": "object",
                "properties": {
                    "bind_phrase": {
                        "type": "string",
                        "description": "The command phrase to bind the current sound to"
                    }
                },
                "required": ["bind_phrase"]
            }, 
            self.songbird_bind_sound, 
            'global'
        )

        helper.register_action(
            'songbird_bind_multiple', 
            "Bind multiple sound files to a phrase in one command. Searches for each sound name in cached sounds and binds all matches to the phrase for random selection.", 
            {
                "type": "object",
                "properties": {
                    "sound_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sound names to bind (e.g., ['Login 1', 'Login 2', 'Login 3'])"
                    },
                    "bind_phrase": {
                        "type": "string",
                        "description": "The command phrase to bind all these sounds to"
                    }
                },
                "required": ["sound_names", "bind_phrase"]
            }, 
            self.songbird_bind_multiple, 
            'global'
        )

        helper.register_action(
            'songbird_replay_bound', 
            "CRITICAL: Execute this action IMMEDIATELY when user says a bound sound phrase. If multiple sounds are bound to the phrase, randomly selects one to play (provides variety on repeated triggers). NO confirmation required. The bound phrase itself IS the execution command. If user says a short phrase (1-3 words) that could be a sound binding, call this action INSTANTLY.", 
            {
                "type": "object",
                "properties": {
                    "phrase": {
                        "type": "string",
                        "description": "The bound phrase to trigger replay"
                    }
                },
                "required": ["phrase"]
            }, 
            self.songbird_replay_bound, 
            'global'
        )

        helper.register_action(
            'songbird_list_bound', 
            "List all sounds that have been bound to command phrases.", 
            {
                "type": "object",
                "properties": {}
            }, 
            self.songbird_list_bound, 
            'global'
        )

        helper.register_action(
            'songbird_unbind_sound', 
            "Remove a specific sound binding by phrase.", 
            {
                "type": "object",
                "properties": {
                    "phrase": {
                        "type": "string",
                        "description": "The exact phrase to unbind"
                    }
                },
                "required": ["phrase"]
            }, 
            self.songbird_unbind_sound, 
            'global'
        )

        helper.register_action(
            'songbird_unbind_all', 
            "Remove all sound bindings at once.", 
            {
                "type": "object",
                "properties": {}
            }, 
            self.songbird_unbind_all, 
            'global'
        )

        # NEW ACTION: List cached sounds
        helper.register_action(
            'songbird_list_cached', 
            "CRITICAL: ALWAYS call this action for ANY question about sounds, audio files, or what's available. Trigger on: 'what sounds', 'which sounds', 'how many sounds', 'do you have sounds', 'sounds saved', 'sounds cached', 'sounds downloaded', 'list sounds', 'show sounds', 'see sounds', 'check sounds', 'sounds in cache', 'available sounds', 'my sounds', 'sound files', 'audio files', 'what audio', 'sound list', or ANY variation asking about sound availability. DO NOT respond with 'I don't know' or 'no sounds' without calling this action first. This checks actual sound files in the sounds folder.", 
            {
                "type": "object",
                "properties": {}
            }, 
            self.songbird_list_cached, 
            'global'
        )

        log('info', f"SONGBIRD actions registered successfully")
        
    @override
    def register_projections(self, helper: PluginHelper):
        pass

    @override
    def register_sideeffects(self, helper: PluginHelper):
        pass
        
    @override
    def register_prompt_event_handlers(self, helper: PluginHelper):
        pass
        
    @override
    def register_status_generators(self, helper: PluginHelper):
        pass

    @override
    def register_should_reply_handlers(self, helper: PluginHelper):
        pass
    
    @override
    def on_plugin_helper_ready(self, helper: PluginHelper):
        log('info', 'SONGBIRD plugin helper is ready')
        
        # Check for API key file
        api_key = self.get_api_key_from_file()
        if not api_key:
            log('warning', 'SONGBIRD: No API key found. Create api_key.txt file in the Songbird plugin folder.')
            log('info', f'SONGBIRD: Plugin folder should be: {self.get_plugin_folder_path()}')
        else:
            log('info', f'SONGBIRD: API key loaded from file (length: {len(api_key)} characters)')
    
    @override
    def on_chat_stop(self, helper: PluginHelper):
        log('info', 'SONGBIRD: Chat stopped')

    def get_plugin_folder_path(self) -> str:
        """Get the path to the plugin folder"""
        try:
            # Method 1: Get directory of current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return current_dir
        except:
            try:
                # Method 2: Construct from APPDATA
                appdata = os.getenv('APPDATA')
                if appdata:
                    return os.path.join(appdata, 'com.covas-next.ui', 'plugins', 'Songbird')
            except:
                pass
        return ""

    def get_api_key_from_file(self) -> str:
        """Read API key from api_key.txt file"""
        try:
            plugin_folder = self.get_plugin_folder_path()
            if not plugin_folder:
                log('error', 'SONGBIRD: Could not determine plugin folder path')
                return ""
            
            api_key_file = os.path.join(plugin_folder, 'api_key.txt')
            
            if not os.path.exists(api_key_file):
                log('info', f'SONGBIRD: api_key.txt not found at: {api_key_file}')
                return ""
            
            with open(api_key_file, 'r', encoding='utf-8') as f:
                api_key = f.read().strip()
                if api_key:
                    log('info', 'SONGBIRD: API key successfully loaded from api_key.txt')
                    return api_key
                else:
                    log('warning', 'SONGBIRD: api_key.txt file is empty')
                    return ""
                    
        except Exception as e:
            log('error', f'SONGBIRD: Error reading API key file: {str(e)}')
            return ""

    def search_freesound(self, query: str, api_key: str, page: int = 1) -> dict:
        """Search Freesound API for sounds matching the query"""
        try:
            url = "https://freesound.org/apiv2/search/text/"
            headers = {
                "Authorization": f"Token {api_key}"
            }
            params = {
                "query": query,
                "page": page,
                "page_size": 15,
                "fields": "id,name,previews,download,url,username"
            }
            
            log('info', f"SONGBIRD: Searching Freesound for '{query}' (page {page})")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                log('info', f"SONGBIRD: Found {count} total sounds for '{query}' (page {page})")
                return data
            elif response.status_code == 401:
                log('error', f"SONGBIRD: Invalid API key (401 Unauthorized)")
                return {"error": "Invalid API key"}
            else:
                log('error', f"SONGBIRD: API request failed with status {response.status_code}: {response.text}")
                return {"error": f"API request failed: {response.status_code}"}
                
        except Exception as e:
            log('error', f"SONGBIRD: Search error - {str(e)}")
            return {"error": str(e)}

    def get_varied_freesound_results(self, query: str, api_key: str) -> list:
        """Get varied results from multiple pages of Freesound"""
        try:
            all_results = []
            
            # Search first 5 pages to get more variety
            for page in range(1, 6):
                search_results = self.search_freesound(query, api_key, page)
                
                if "error" in search_results:
                    if page == 1:  # If first page fails, return error
                        return [{"error": search_results["error"]}]
                    else:  # If later pages fail, just use what we have
                        break
                
                results = search_results.get('results', [])
                if not results:
                    break  # No more results
                
                all_results.extend(results)
                
                # If we have enough results, stop searching
                if len(all_results) >= 75:
                    break
            
            log('info', f"SONGBIRD: Collected {len(all_results)} total results from multiple pages")
            return all_results
            
        except Exception as e:
            log('error', f"SONGBIRD: Error getting varied results: {str(e)}")
            return [{"error": str(e)}]

    def select_random_sound(self, results: list) -> dict:
        """Select a random sound from results"""
        try:
            if not results:
                return {"error": "No results to select from"}
            
            # Randomly select from available results
            selected = random.choice(results)
            
            log('info', f"SONGBIRD: Randomly selected '{selected.get('name', 'Unknown')}' from {len(results)} options")
            return selected
            
        except Exception as e:
            log('error', f"SONGBIRD: Error selecting random sound: {str(e)}")
            return results[0] if results else {"error": "No results available"}

    def download_and_play_sound(self, sound_data: dict) -> str:
        """Download and play a sound file using pygame"""
        try:
            # Get preview URL - simplified with priority list
            previews = sound_data.get('previews', {})
            preview_url = None
            file_extension = '.mp3'
            
            # Priority list: best quality first
            PREVIEW_PRIORITY = [
                ('preview-hq-mp3', '.mp3'),
                ('preview-lq-mp3', '.mp3'),
                ('preview-hq-ogg', '.ogg'),
                ('preview-lq-ogg', '.ogg')
            ]
            
            for preview_key, ext in PREVIEW_PRIORITY:
                if preview_key in previews and previews[preview_key]:
                    preview_url = previews[preview_key]
                    file_extension = ext
                    break
            
            if not preview_url:
                return "No preview available for this sound"
            
            log('info', f"SONGBIRD: Downloading from {preview_url}")
            
            # Download the sound file
            response = requests.get(preview_url, timeout=30)
            if response.status_code != 200:
                return f"Failed to download sound (HTTP {response.status_code})"
            
            # Create sounds folder in plugin directory
            plugin_folder = self.get_plugin_folder_path()
            sounds_folder = os.path.join(plugin_folder, 'sounds')
            
            # Create sounds directory if it doesn't exist
            if not os.path.exists(sounds_folder):
                os.makedirs(sounds_folder)
                log('info', f"SONGBIRD: Created sounds folder at {sounds_folder}")
            
            # Create filename based on sound info
            sound_name = sound_data.get('name', 'unknown_sound')
            sound_id = sound_data.get('id', 'unknown')
            # Clean filename (remove invalid characters)
            safe_name = "".join(c for c in sound_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_{sound_id}{file_extension}"
            filepath = os.path.join(sounds_folder, filename)
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            log('info', f"SONGBIRD: Sound saved to {filepath}")
            
            # Play the sound using pygame (invisible playback)
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                
                log('info', f"SONGBIRD: Playing sound invisibly: {sound_name}")
                return f"Playing '{sound_name}'"
                
            except Exception as play_error:
                log('error', f"SONGBIRD: Error playing sound with pygame: {str(play_error)}")
                return f"Downloaded '{sound_name}' to sounds folder but failed to play: {str(play_error)}"
                    
        except Exception as e:
            log('error', f"SONGBIRD: Error in download_and_play_sound: {str(e)}")
            return f"Error downloading/playing sound: {str(e)}"

    def songbird_control(self, args, projected_states) -> str:
        """Handle voice commands for audio playback control"""
        try:
            voice_command = args.get('voice_command', '').lower().strip()
            
            log('info', f"SONGBIRD: Voice command received: '{voice_command}'")
            
            # Stop commands
            if any(word in voice_command for word in ['stop', 'halt', 'end']):
                pygame.mixer.music.stop()
                return "SONGBIRD: Audio stopped"
                
            # Pause commands  
            elif any(word in voice_command for word in ['pause', 'hold']):
                pygame.mixer.music.pause()
                return "SONGBIRD: Audio paused"
                
            # Resume commands
            elif any(word in voice_command for word in ['resume', 'continue', 'unpause', 'play']):
                pygame.mixer.music.unpause()
                return "SONGBIRD: Audio resumed"
                
            # Mute commands
            elif 'mute' in voice_command:
                pygame.mixer.music.set_volume(0.0)
                return "SONGBIRD: Audio muted"
                
            # Unmute commands
            elif 'unmute' in voice_command:
                pygame.mixer.music.set_volume(0.7)
                return "SONGBIRD: Audio unmuted"
                
            # Volume commands
            elif 'volume' in voice_command:
                # Extract numbers from the command (using re from module level now)
                numbers = re.findall(r'\d+', voice_command)
                
                if 'up' in voice_command or 'increase' in voice_command or 'higher' in voice_command:
                    current_volume = pygame.mixer.music.get_volume()
                    new_volume = min(1.0, current_volume + 0.1)
                    pygame.mixer.music.set_volume(new_volume)
                    return f"SONGBIRD: Volume increased to {int(new_volume * 100)}%"
                    
                elif 'down' in voice_command or 'decrease' in voice_command or 'lower' in voice_command:
                    current_volume = pygame.mixer.music.get_volume()
                    new_volume = max(0.0, current_volume - 0.1)
                    pygame.mixer.music.set_volume(new_volume)
                    return f"SONGBIRD: Volume decreased to {int(new_volume * 100)}%"
                    
                elif numbers:
                    # Set specific volume
                    try:
                        target_volume = int(numbers[0])
                        pygame_volume = max(0.0, min(1.0, target_volume / 100.0))
                        pygame.mixer.music.set_volume(pygame_volume)
                        return f"SONGBIRD: Volume set to {int(pygame_volume * 100)}%"
                    except (ValueError, IndexError):
                        pass
                        
                # Fallback for generic volume commands
                return "SONGBIRD: Volume command unclear. Try 'volume up', 'volume down', or 'volume to 50%'"
                
            else:
                return f"SONGBIRD: Command '{voice_command}' not recognized. Available: stop, pause, resume, volume up/down/to X%, mute, unmute"
                
        except Exception as e:
            log('error', f"SONGBIRD control error: {str(e)}")
            return f"SONGBIRD: Control error - {str(e)}"

    def should_use_freesound(self, sound_description: str, replay_mode: str = "auto") -> bool:
        """Determine whether to use Freesound or check local cache"""
        # If explicit replay mode specified
        if replay_mode == "again":
            return False  # Check cache first
        elif replay_mode == "new":
            return True   # Always use Freesound
        
        # Auto-detect from description
        description_lower = sound_description.lower()
        
        # Words that indicate wanting a new/different sound
        freesound_keywords = [
            'another', 'different', 'new', 'fresh', 'other'
        ]
        
        # Words that indicate replay request
        replay_keywords = [
            'again', 'same', 'repeat', 'replay', 'once more', 'it'
        ]
        
        # Check for explicit indicators
        for keyword in freesound_keywords:
            if keyword in description_lower:
                log('info', f"SONGBIRD: Detected Freesound keyword '{keyword}'")
                return True
        
        for keyword in replay_keywords:
            if keyword in description_lower:
                log('info', f"SONGBIRD: Detected replay keyword '{keyword}'")
                return False
        
        # Default: check cache first for efficiency
        return False

    def get_local_sounds(self) -> list:
        """Get list of locally cached sound files"""
        try:
            plugin_folder = self.get_plugin_folder_path()
            sounds_folder = os.path.join(plugin_folder, 'sounds')
            
            if not os.path.exists(sounds_folder):
                return []
            
            sound_files = []
            supported_extensions = ['.mp3', '.ogg', '.wav']
            
            for filename in os.listdir(sounds_folder):
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    filepath = os.path.join(sounds_folder, filename)
                    # Remove extension first
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # Check if this is a Freesound file (ends with underscore + numbers)
                    name_parts = name_without_ext.rsplit('_', 1)
                    if len(name_parts) == 2 and name_parts[1].isdigit():
                        # Freesound format: soundname_12345
                        readable_name = name_parts[0].replace('_', ' ')
                    else:
                        # User file: use full filename without extension
                        readable_name = name_without_ext.replace('_', ' ')
                    
                    sound_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'readable_name': readable_name
                    })
            
            return sound_files
            
        except Exception as e:
            log('error', f"SONGBIRD: Error getting local sounds: {str(e)}")
            return []

    def find_local_sound(self, search_term: str):
        """Find a local sound file that matches the search term - IMPROVED VERSION with number conversion"""
        try:
            sound_files = self.get_local_sounds()
            
            if not sound_files:
                return None
            
            search_lower = search_term.lower().strip()
            
            # Handle "it again" or replay requests using last played description
            if ('it' in search_lower or 'again' in search_lower) and self.last_played_description:
                search_lower = self.last_played_description.lower()
                log('info', f"SONGBIRD: Using last played description '{self.last_played_description}' for replay")
            
            # Convert word numbers to digits (e.g., "wrong one" becomes "wrong 1")
            search_with_digits = self.convert_word_numbers_to_digits(search_lower)
            
            # Normalize search term: remove hyphens, underscores, extra spaces
            search_normalized = search_with_digits.replace('-', ' ').replace('_', ' ')
            search_words = set(search_normalized.split())
            
            log('info', f"SONGBIRD: Searching for '{search_lower}' (normalized: '{search_normalized}') among {len(sound_files)} local sounds")
            
            # Try exact match first (with normalization)
            for sound in sound_files:
                sound_normalized = sound['readable_name'].lower().replace('-', ' ').replace('_', ' ')
                if search_normalized == sound_normalized:
                    log('info', f"SONGBIRD: Exact match found: {sound['readable_name']}")
                    return sound
            
            # Try word-based matching (all search words present)
            for sound in sound_files:
                sound_normalized = sound['readable_name'].lower().replace('-', ' ').replace('_', ' ')
                sound_words = set(sound_normalized.split())
                if search_words.issubset(sound_words):
                    log('info', f"SONGBIRD: Word match found: {sound['readable_name']}")
                    return sound
            
            # Try partial matching (any search word matches)
            for sound in sound_files:
                sound_normalized = sound['readable_name'].lower().replace('-', ' ').replace('_', ' ')
                if any(word in sound_normalized for word in search_words):
                    log('info', f"SONGBIRD: Partial match found: {sound['readable_name']}")
                    return sound
            
            # Try matching against original filename too
            for sound in sound_files:
                filename_lower = sound['filename'].lower()
                if search_normalized in filename_lower or any(word in filename_lower for word in search_words):
                    log('info', f"SONGBIRD: Filename match found: {sound['filename']}")
                    return sound
            
            log('info', f"SONGBIRD: No local sound found matching '{search_lower}'")
            return None
                
        except Exception as e:
            log('error', f"SONGBIRD: Error finding local sound: {str(e)}")
            return None

    def play_local_sound(self, sound_info: dict) -> str:
        """Play a local sound file using pygame"""
        try:
            filepath = sound_info['filepath']
            readable_name = sound_info['readable_name']
            
            if not os.path.exists(filepath):
                return f"Sound file not found: {readable_name}"
            
            # Play the sound using pygame
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            log('info', f"SONGBIRD: Playing local sound: {readable_name}")
            return f"Playing cached sound: '{readable_name}'"
            
        except Exception as e:
            log('error', f"SONGBIRD: Error playing local sound: {str(e)}")
            return f"Error playing local sound: {str(e)}"

    def songbird_play_sound(self, args, projected_states) -> str:
        """Play sound using hybrid approach: cache for replay, Freesound for new sounds"""
        try:
            sound_description = args.get('sound_description', '')
            replay_mode = args.get('replay_mode', 'auto')
            context = args.get('context', '')
            
            log('info', f"SONGBIRD: Request for '{sound_description}' (mode: {replay_mode})")
            
            if not sound_description:
                return "SONGBIRD: No sound description provided."
            
            # Determine whether to check cache or use Freesound
            use_freesound = self.should_use_freesound(sound_description, replay_mode)
            
            if not use_freesound:
                # Try to find in local cache first
                local_match = self.find_local_sound(sound_description)
                
                if local_match is not None:
                    # Found in cache, play it
                    log('info', f"SONGBIRD: Playing from cache: {local_match['readable_name']}")
                    play_result = self.play_local_sound(local_match)
                    
                    # Update current playing for binding
                    self.current_playing = {
                        'sound_name': local_match['readable_name'],
                        'filepath': local_match['filepath'],
                        'description_used': sound_description,
                        'username': 'Local Cache'
                    }
                    
                    return f"SONGBIRD: {play_result}"
                else:
                    log('info', f"SONGBIRD: No cached sound found, falling back to Freesound")
            else:
                log('info', f"SONGBIRD: Using Freesound for new/different sound")
            
            # No cached match found OR user wants new sound - search Freesound
            api_key = self.get_api_key_from_file()
            if not api_key:
                return "SONGBIRD: Please create api_key.txt file in the Songbird plugin folder with your Freesound API key."
            
            # Get varied results from multiple pages
            all_results = self.get_varied_freesound_results(sound_description, api_key)
            
            if not all_results or (len(all_results) == 1 and "error" in all_results[0]):
                if all_results and "error" in all_results[0]:
                    error = all_results[0]["error"]
                    if error == "Invalid API key":
                        return "SONGBIRD: Invalid Freesound API key. Please check your api_key.txt file."
                    return f"SONGBIRD: Search failed - {error}"
                return f"SONGBIRD: No sounds found for '{sound_description}'. Try a different description."
            
            # Always use random selection for variety
            selected_sound = self.select_random_sound(all_results)
            
            if "error" in selected_sound:
                return f"SONGBIRD: Error selecting sound - {selected_sound['error']}"
            
            sound_name = selected_sound.get('name', 'Unknown')
            username = selected_sound.get('username', 'Unknown')
            
            # Download and play the sound
            play_result = self.download_and_play_sound(selected_sound)
            
            # Build filepath for tracking
            plugin_folder = self.get_plugin_folder_path()
            sounds_folder = os.path.join(plugin_folder, 'sounds')
            sound_id = selected_sound.get('id', 'unknown')
            safe_name = "".join(c for c in sound_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            # Determine file extension
            previews = selected_sound.get('previews', {})
            file_extension = '.mp3'
            if 'preview-hq-mp3' in previews or 'preview-lq-mp3' in previews:
                file_extension = '.mp3'
            elif 'preview-hq-ogg' in previews or 'preview-lq-ogg' in previews:
                file_extension = '.ogg'
            
            filename = f"{safe_name}_{sound_id}{file_extension}"
            filepath = os.path.join(sounds_folder, filename)
            
            # Track current playing sound for binding system
            self.current_playing = {
                'sound_data': selected_sound,
                'sound_name': sound_name,
                'username': username,
                'description_used': sound_description,
                'filepath': filepath
            }
            
            # Track last played for replay functionality
            self.last_played_description = sound_description
            
            log('info', f"SONGBIRD: Set current playing sound: {sound_name}")
            
            return f"SONGBIRD: Found '{sound_name}' by {username}. {play_result}"
            
        except Exception as e:
            log('error', f"SONGBIRD error: {str(e)}")
            return f"SONGBIRD: Error - {str(e)}"

    def songbird_test(self, args, projected_states) -> str:
        try:
            log('info', 'SONGBIRD: Running test')
            
            version = self.plugin_manifest.version
            name = self.plugin_manifest.name
            
            # Check API key file
            api_key = self.get_api_key_from_file()
            plugin_folder = self.get_plugin_folder_path()
            
            if api_key:
                result = f"SONGBIRD Test: {name} v{version} - Active with Freesound API integration. API key loaded from file."
            else:
                result = f"SONGBIRD Test: {name} v{version} - Active but no API key found. Create api_key.txt in: {plugin_folder}"
            
            log('info', 'SONGBIRD: Test completed')
            return result
            
        except Exception as e:
            log('error', f"SONGBIRD test error: {str(e)}")
            return f"SONGBIRD: Test failed - {str(e)}"

    def get_bound_sounds_file(self) -> str:
        """Get path to bound sounds configuration file"""
        plugin_folder = self.get_plugin_folder_path()
        return os.path.join(plugin_folder, 'bound_sounds.json')

    def load_bound_sounds(self) -> dict:
        """Load bound sounds from configuration file"""
        try:
            bound_file = self.get_bound_sounds_file()
            if os.path.exists(bound_file):
                with open(bound_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log('error', f"SONGBIRD: Error loading bound sounds: {str(e)}")
            return {}

    def save_bound_sounds(self, bound_sounds: dict) -> bool:
        """Save bound sounds to configuration file"""
        try:
            bound_file = self.get_bound_sounds_file()
            with open(bound_file, 'w', encoding='utf-8') as f:
                json.dump(bound_sounds, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            log('error', f"SONGBIRD: Error saving bound sounds: {str(e)}")
            return False

    def songbird_bind_sound(self, args, projected_states) -> str:
        """Bind the last played sound to a command phrase - supports multiple sounds per phrase"""
        try:
            bind_phrase = args.get('bind_phrase', '').strip()
            
            # Normalize phrase (lowercase + strip punctuation)
            normalized_phrase = self.normalize_phrase(bind_phrase)
            
            if not normalized_phrase:
                return "SONGBIRD: Please specify a phrase to bind the sound to."
            
            log('info', f"SONGBIRD: Binding request for phrase: '{bind_phrase}' (normalized: '{normalized_phrase}')")
            
            if not self.current_playing:
                return "SONGBIRD: No sound has been played yet to bind. Play a sound first, then bind it."
            
            sound_name = self.current_playing.get('sound_name')
            filepath = self.current_playing.get('filepath')
            
            if not sound_name or not filepath:
                return "SONGBIRD: Current sound information incomplete. Try playing a sound again."
            
            if not os.path.exists(filepath):
                return f"SONGBIRD: Sound file not found. Try playing the sound again."
            
            # Load existing bound sounds
            bound_sounds = self.load_bound_sounds()
            
            # Check if phrase already exists
            if normalized_phrase in bound_sounds:
                # Phrase exists - check if it's a list or single sound
                existing_binding = bound_sounds[normalized_phrase]
                
                # Convert old single-sound format to list format
                if not isinstance(existing_binding, list):
                    bound_sounds[normalized_phrase] = [existing_binding]
                
                # Add new sound to the list
                new_sound_entry = {
                    'sound_name': sound_name,
                    'filepath': filepath,
                    'description_used': self.current_playing.get('description_used', ''),
                    'username': self.current_playing.get('username', 'Unknown')
                }
                
                # Check if this exact sound is already in the list
                already_exists = False
                for sound_entry in bound_sounds[normalized_phrase]:
                    if sound_entry['filepath'] == filepath:
                        already_exists = True
                        break
                
                if already_exists:
                    return f"SONGBIRD: '{sound_name}' is already bound to phrase '{bind_phrase}'"
                
                bound_sounds[normalized_phrase].append(new_sound_entry)
                
                # Save bound sounds
                if self.save_bound_sounds(bound_sounds):
                    count = len(bound_sounds[normalized_phrase])
                    log('info', f"SONGBIRD: Added '{sound_name}' to phrase '{normalized_phrase}' (now {count} sounds)")
                    return f"SONGBIRD: Added '{sound_name}' to phrase '{bind_phrase}' (now {count} sounds total)"
                else:
                    return "SONGBIRD: Error saving bound sound"
            else:
                # New phrase - create as a list with one sound
                bound_sounds[normalized_phrase] = [{
                    'sound_name': sound_name,
                    'filepath': filepath,
                    'description_used': self.current_playing.get('description_used', ''),
                    'username': self.current_playing.get('username', 'Unknown')
                }]
                
                # Save bound sounds
                if self.save_bound_sounds(bound_sounds):
                    log('info', f"SONGBIRD: Bound '{sound_name}' to phrase '{normalized_phrase}'")
                    return f"SONGBIRD: Bound '{sound_name}' to phrase '{bind_phrase}'"
                else:
                    return "SONGBIRD: Error saving bound sound"
            
        except Exception as e:
            log('error', f"SONGBIRD bind error: {str(e)}")
            return f"SONGBIRD: Bind error - {str(e)}"

    def songbird_bind_multiple(self, args, projected_states) -> str:
        """Bind multiple sounds to a phrase in one command"""
        try:
            sound_names = args.get('sound_names', [])
            bind_phrase = args.get('bind_phrase', '').strip()
            
            # Normalize phrase
            normalized_phrase = self.normalize_phrase(bind_phrase)
            
            if not normalized_phrase:
                return "SONGBIRD: Please specify a phrase to bind the sounds to."
            
            if not sound_names or len(sound_names) == 0:
                return "SONGBIRD: Please specify at least one sound name to bind."
            
            log('info', f"SONGBIRD: Multiple bind request for {len(sound_names)} sounds to phrase '{bind_phrase}'")
            
            # Get all cached sounds
            all_sounds = self.get_local_sounds()
            
            if not all_sounds:
                return "SONGBIRD: No cached sounds available to bind."
            
            # Find matching sounds
            found_sounds = []
            not_found = []
            
            for sound_name in sound_names:
                # Try to find this sound
                found = False
                search_normalized = sound_name.lower().replace('-', ' ').replace('_', ' ')
                search_words = set(search_normalized.split())
                
                for sound in all_sounds:
                    sound_normalized = sound['readable_name'].lower().replace('-', ' ').replace('_', ' ')
                    sound_words = set(sound_normalized.split())
                    
                    # Check for match using word-based matching (more accurate)
                    # Match if: exact match OR all search words are present in sound name
                    if (search_normalized == sound_normalized or 
                        search_words.issubset(sound_words)):
                        found_sounds.append(sound)
                        found = True
                        log('info', f"SONGBIRD: Found match for '{sound_name}': {sound['readable_name']}")
                        break
                
                if not found:
                    not_found.append(sound_name)
                    log('info', f"SONGBIRD: No match found for '{sound_name}'")
            
            if len(found_sounds) == 0:
                return f"SONGBIRD: None of the specified sounds were found in cache. Not found: {', '.join(not_found)}"
            
            # Load existing bound sounds
            bound_sounds = self.load_bound_sounds()
            
            # Initialize or convert existing binding to list format
            if normalized_phrase in bound_sounds:
                existing = bound_sounds[normalized_phrase]
                if not isinstance(existing, list):
                    bound_sounds[normalized_phrase] = [existing]
            else:
                bound_sounds[normalized_phrase] = []
            
            # Add all found sounds
            added_count = 0
            skipped_count = 0
            
            for sound in found_sounds:
                # Check if already in the list
                already_exists = False
                for existing_sound in bound_sounds[normalized_phrase]:
                    if existing_sound['filepath'] == sound['filepath']:
                        already_exists = True
                        break
                
                if not already_exists:
                    bound_sounds[normalized_phrase].append({
                        'sound_name': sound['readable_name'],
                        'filepath': sound['filepath'],
                        'description_used': '',
                        'username': 'Local Cache'
                    })
                    added_count += 1
                else:
                    skipped_count += 1
            
            # Save bound sounds
            if self.save_bound_sounds(bound_sounds):
                total = len(bound_sounds[normalized_phrase])
                result_parts = [f"SONGBIRD: Bound {added_count} sound(s) to phrase '{bind_phrase}' (total: {total})"]
                
                if skipped_count > 0:
                    result_parts.append(f"Skipped {skipped_count} duplicate(s)")
                
                if len(not_found) > 0:
                    result_parts.append(f"Not found: {', '.join(not_found)}")
                
                log('info', f"SONGBIRD: Successfully bound {added_count} sounds to '{normalized_phrase}'")
                return ". ".join(result_parts)
            else:
                return "SONGBIRD: Error saving bound sounds"
            
        except Exception as e:
            log('error', f"SONGBIRD bind multiple error: {str(e)}")
            return f"SONGBIRD: Bind multiple error - {str(e)}"

    def songbird_replay_bound(self, args, projected_states) -> str:
        """Replay a sound bound to a specific phrase - randomly selects if multiple sounds"""
        try:
            phrase = args.get('phrase', '').strip()
            
            # Normalize phrase for matching
            normalized_phrase = self.normalize_phrase(phrase)
            
            if not normalized_phrase:
                return "SONGBIRD: Please specify the bound phrase."
            
            log('info', f"SONGBIRD: Replay bound sound for phrase: '{phrase}' (normalized: '{normalized_phrase}')")
            
            # Load bound sounds
            bound_sounds = self.load_bound_sounds()
            
            # Check if phrase exists
            if normalized_phrase not in bound_sounds:
                return f"SONGBIRD: No sound bound to phrase '{phrase}'. Use 'list bound sounds' to see available phrases."
            
            bound_data = bound_sounds[normalized_phrase]
            
            # Handle both old single-sound format and new list format
            if isinstance(bound_data, list):
                # Multiple sounds - randomly select one
                selected = random.choice(bound_data)
                filepath = selected['filepath']
                sound_name = selected['sound_name']
                log('info', f"SONGBIRD: Randomly selected '{sound_name}' from {len(bound_data)} sounds for phrase '{normalized_phrase}'")
            else:
                # Old format - single sound (backwards compatibility)
                filepath = bound_data['filepath']
                sound_name = bound_data['sound_name']
            
            # Check if file still exists
            if not os.path.exists(filepath):
                return f"SONGBIRD: Bound sound file not found: {sound_name}"
            
            # Play the bound sound
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                
                log('info', f"SONGBIRD: Playing bound sound: {sound_name}")
                return f"SONGBIRD: Playing bound sound '{sound_name}'"
                
            except Exception as play_error:
                log('error', f"SONGBIRD: Error playing bound sound: {str(play_error)}")
                return f"SONGBIRD: Error playing bound sound: {str(play_error)}"
            
        except Exception as e:
            log('error', f"SONGBIRD replay bound error: {str(e)}")
            return f"SONGBIRD: Replay bound error - {str(e)}"

    def songbird_list_bound(self, args, projected_states) -> str:
        """List all bound sound phrases with sound counts"""
        try:
            log('info', 'SONGBIRD: Listing bound sounds')
            
            bound_sounds = self.load_bound_sounds()
            
            if not bound_sounds:
                return "SONGBIRD: No sounds bound to phrases yet. Use 'bind this to [phrase]' to create bindings."
            
            bound_list = []
            for phrase, data in bound_sounds.items():
                # Handle both list format (new) and single sound format (old)
                if isinstance(data, list):
                    sound_count = len(data)
                    if sound_count == 1:
                        sound_name = data[0]['sound_name']
                        bound_list.append(f"- '{phrase}' -> {sound_name}")
                    else:
                        sound_names = [s['sound_name'] for s in data]
                        bound_list.append(f"- '{phrase}' -> {sound_count} sounds: {', '.join(sound_names)}")
                else:
                    # Old format - single sound
                    sound_name = data['sound_name']
                    bound_list.append(f"- '{phrase}' -> {sound_name}")
            
            result = f"SONGBIRD: Found {len(bound_sounds)} bound phrases:\n" + "\n".join(bound_list)
            
            log('info', f'SONGBIRD: Listed {len(bound_sounds)} bound phrases')
            return result
            
        except Exception as e:
            log('error', f"SONGBIRD list bound error: {str(e)}")
            return f"SONGBIRD: Error listing bound sounds - {str(e)}"

    def songbird_unbind_sound(self, args, projected_states) -> str:
        """Remove a specific sound from a binding, or the entire phrase if only one sound"""
        try:
            phrase = args.get('phrase', '').strip()
            
            # Normalize phrase for matching
            normalized_phrase = self.normalize_phrase(phrase)
            
            if not normalized_phrase:
                return "SONGBIRD: Please specify the phrase to unbind."
            
            log('info', f"SONGBIRD: Unbind request for phrase: '{phrase}' (normalized: '{normalized_phrase}')")
            
            # Load bound sounds
            bound_sounds = self.load_bound_sounds()
            
            # Check if phrase exists
            if normalized_phrase not in bound_sounds:
                return f"SONGBIRD: No sound bound to phrase '{phrase}'."
            
            bound_data = bound_sounds[normalized_phrase]
            
            # Handle both formats
            if isinstance(bound_data, list):
                sound_count = len(bound_data)
                sound_names = [s['sound_name'] for s in bound_data]
                sounds_text = ', '.join(sound_names)
            else:
                sound_count = 1
                sounds_text = bound_data['sound_name']
            
            # Remove the entire phrase binding
            del bound_sounds[normalized_phrase]
            
            # Save updated bindings
            if self.save_bound_sounds(bound_sounds):
                log('info', f"SONGBIRD: Unbound phrase '{normalized_phrase}' ({sound_count} sound(s))")
                return f"SONGBIRD: Unbound phrase '{phrase}' ({sound_count} sound(s): {sounds_text})"
            else:
                return "SONGBIRD: Error saving updated bindings"
            
        except Exception as e:
            log('error', f"SONGBIRD unbind error: {str(e)}")
            return f"SONGBIRD: Unbind error - {str(e)}"

    def songbird_unbind_all(self, args, projected_states) -> str:
        """Remove all sound bindings"""
        try:
            log('info', 'SONGBIRD: Unbind all request')
            
            # Load current bindings to count them
            bound_sounds = self.load_bound_sounds()
            count = len(bound_sounds)
            
            if count == 0:
                return "SONGBIRD: No sound bindings to remove."
            
            # Clear all bindings
            if self.save_bound_sounds({}):
                log('info', f'SONGBIRD: Removed all {count} sound bindings')
                return f"SONGBIRD: Removed all {count} sound bindings"
            else:
                return "SONGBIRD: Error clearing bindings"
            
        except Exception as e:
            log('error', f"SONGBIRD unbind all error: {str(e)}")
            return f"SONGBIRD: Unbind all error - {str(e)}"

    def songbird_list_cached(self, args, projected_states) -> str:
        """List all locally cached sound files - NEW METHOD"""
        try:
            log('info', 'SONGBIRD: Listing cached sounds')
            
            sound_files = self.get_local_sounds()
            
            if not sound_files:
                plugin_folder = self.get_plugin_folder_path()
                sounds_folder = os.path.join(plugin_folder, 'sounds')
                return f"SONGBIRD: No sounds cached yet. Sounds folder: {sounds_folder}"
            
            cached_list = []
            for sound in sound_files:
                cached_list.append(f"- '{sound['readable_name']}' ({sound['filename']})")
            
            result = f"SONGBIRD: Found {len(sound_files)} cached sounds:\n" + "\n".join(cached_list)
            
            log('info', f'SONGBIRD: Listed {len(sound_files)} cached sounds')
            return result
            
        except Exception as e:
            log('error', f"SONGBIRD list cached error: {str(e)}")
            return f"SONGBIRD: Error listing cached sounds - {str(e)}"