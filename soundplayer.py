import logging
import platform
import subprocess
from typing import List
from pathlib import Path
import platform
from pydub import AudioSegment
from abc import ABC
import os
import edge_tts

logger = logging.getLogger(__name__)

class Player(ABC):
    

    def playback_wav_mp3(self, out_file):

        system = platform.system()
        file_ext = os.path.splitext(out_file)[1].lower()        

        try:
            if system == "Windows":
                if file_ext == ".wav":
                    console_str=f"(New-Object Media.SoundPlayer '{out_file}').PlaySync();"
                    subprocess.run(["powershell", "-c", console_str], check=True)

                elif file_ext == ".mp3":                                    
                    #does not work..         
                    #soundfile = AudioSegment.from_mp3(out_file)                    
                    #out_file=soundfile.export(out_file, format="wav")
                    
                    os.startfile(out_file)
                else:
                    # Use Windows Media Player or ffplay for mp3
                    print(f"[Player] unknown file format : {file_ext} - try media player")                    
                    os.startfile(out_file)

            else:  # Linux
                subprocess.run(
                    ["play", "-q", str(out_file)], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

        except FileNotFoundError:
            print("[Player ERROR] 'play' command not found. Please install SoX.")
        except subprocess.CalledProcessError as e:
            print(f"[Player ERROR] Failed to play {out_file}: {e}")
        except Exception as e:
            print(f"[Player ERROR] Unexpected error: {e}")

#Microsoft TextToSpeach Player, alternative google gTTS
class EdgeTTSPlayer(Player):
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    async def play_message(self, msg: str):
        out_file = self.temp_dir / "wind_message.mp3"
        try:
            communicate = edge_tts.Communicate(
                text=msg,
                voice="de-DE-KatjaNeural",  
                rate="+0%",                  
                pitch="-5Hz"                 
            )
            await communicate.save(out_file)

            self.playback_wav_mp3(out_file)

        except Exception as e:
            print(f"ERROR from Edge-TTS: {e}")
        
        #alternative voices:
        #de-DE-ConradNeural
        #de-DE-KatjaNeural
        #de-DE-KillianNeural
        #de-DE-AmalaNeural

#Soundblock System
class SoundBlockPlayer(Player):
    def __init__(self, sound_dir, temp_dir):                
        self.sound_dir = Path(sound_dir)
        self.temp_dir =Path(temp_dir)        

    def create_sound_files_array(self, message: List[str]) -> List[Path]:
        #map to wav files. Raise error if file not found
        files = []
        
        for part in message:                        

            #if numeric
            if part.isnumeric():
                value = int(part)

                if 100 <= value <= 300:
                    hundreds = (value // 100) * 100
                    hundreds_file=self.sound_dir / f"{hundreds}"
                    
                    if hundreds_file.is_file():
                        files.append(hundreds_file)
                    else:
                        raise FileNotFoundError(f"Missing hundreds file: {hundreds}")

                    value %= 100

                elif value > 300:
                    raise ValueError(f"Value too high: {value}")                    

                #get nearest higher (some files missing)
                if value <= 99:
                    for i in range(value, 100):
                        tens_file=self.sound_dir / f"{i}"                    
                        if tens_file.is_file():
                            files.append(tens_file)
                            break
                    else:
                        raise FileNotFoundError(f"Missing value file: {value}")
                
            #if text
            else:
                word_file = self.sound_dir / f'{part}'
                if word_file.is_file():
                    files.append(word_file)
                else:
                    logger.warning(f"Missing word file: {part}")        
                    raise FileNotFoundError(f"Missing word file: {part}")
        

        for file in files:
            logger.info(f"file {file}")

        return files
    
    def join_and_convert(self, files: List[Path], output: Path):
        
        if not files:
            raise ValueError("No WAV files to join")

        combined = AudioSegment.from_wav(files[0])

        for f in files[1:]:
            seg = AudioSegment.from_wav(f)            
            seg = seg.set_frame_rate(combined.frame_rate).set_channels(combined.channels).set_sample_width(combined.sample_width)
            combined += seg
        
        combined.export(output, format="wav")

    def play_message(self, files: List[Path]):
            
            if not files:
                print("[SoundBlockPlayer ERROR] No sound files to play.")
                return

            out_file = self.temp_dir / "wind_message.wav"

            try:
                self.join_and_convert(files, out_file)
            
            except Exception as e:
                print(f"[SoundBlockPlayer ERROR] Failed to join WAV files: {e}")
                return

            self.playback_wav_mp3(out_file)
            
            