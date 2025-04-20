import os
os.environ["PATH"] += os.pathsep + r'ffmpeg\bin'
import base64
import requests
import librosa
import random
import string
import subprocess
import textwrap
from manim import *
from groq import Groq
import gradio as gr
from bs4 import BeautifulSoup
from together import Together
from pydub import AudioSegment
from moviepy import VideoFileClip, AudioFileClip
from dotenv import load_dotenv
load_dotenv(override=True)

my_dict = {
    "Q":"N",
    "V":"Example",
    "BG":"A bright sunny vast cinematic view of just the sky with loads of white clouds 4K HD",
    "Text":"NULL",
    "FinalVerse":0,
    "CurrentVerse":0,
    "Chapter":0,
    "bg_enhance":"N",
    "Language":"Both"
}

_Voice_Settings={
    "voice_id":"iiidtqDt9FBdT1vfBluA",
    "User_Given_Api" : "",
    "_stability" : 0.7,
    "_similarity_boost" : 0.7,
    "_speed" : 0.85 
}

Text_Lines = []
Line_count = 0

class fn:
    def __init__(self):
        def toggle_inputs(show_advanced):
            if show_advanced:
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
            else:
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)

        def toggle_voice_settings(show_settings):
            return gr.update(visible=show_settings)

        def toggle_buttons(enable):
            return gr.Button(interactive=enable), gr.Button(interactive=enable)

        def toggle_Bg_Enhancer(state):
            if state:
                my_dict["bg_enhance"]="Y"
            else:
                my_dict["bg_enhance"]="N"

        theme = gr.themes.Default(
            font=[gr.themes.GoogleFont("Roboto"), "Arial", "sans-serif"]
        )

        js = """
        function createGradioAnimation() {
            var container = document.createElement('div');
            container.id = 'gradio-animation';
            container.style.fontSize = '2em';
            container.style.fontWeight = 'bold';
            container.style.textAlign = 'center';
            container.style.marginTop = '20px';
            container.style.marginBottom = '0px';

            var text = 'FNv3';
            for (var i = 0; i < text.length; i++) {
                (function(i){
                    setTimeout(function(){
                        var letter = document.createElement('span');
                        letter.style.opacity = '0';
                        letter.style.transition = 'opacity 0.5s';
                        letter.innerText = text[i];

                        container.appendChild(letter);

                        setTimeout(function() {
                            letter.style.opacity = '1';
                        }, 50);
                    }, i * 250);
                })(i);
            }

            var gradioContainer = document.querySelector('.gradio-container');
            gradioContainer.insertBefore(container, gradioContainer.firstChild);

            return 'Animation created';
        }
        """
 
        css = """ 
            /* Main container */
            .gradio-container {
                zoom: 0.75 !important;
                width: 100% !important;
                background-color: transparent !important;
                background-image: url('https://images.pexels.com/photos/236296/pexels-photo-236296.jpeg') !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                transform: scale(1) !important;
                transform-origin: 0 0 !important;
                min-height: 100vh !important;
                margin: 0 !important;
            }

            /* Universal text size (applies to nearly everything except animation) */
            body,
            .gradio-container *:not(#gradio-animation):not(#gradio-animation *):not(.icon):not(.symbol):not(i):not(.material-symbols-outlined),
            input,
            textarea,
            select,
            button,
            label,
            .gradio-textbox,
            .gradio-textarea,
            .gradio-number,
            .gradio-dropdown,
            .gradio-checkbox,
            .gradio-radio,
            .gradio-slider,
            .gradio-button {
                font-size: 17px !important;
            }

            /* Input fields */
            input[type="text"],
            input[type="number"],
            textarea,
            select,
            .gradio-textbox input,
            .gradio-textarea textarea,
            .gradio-number input,
            .gradio-dropdown select {
                height: auto !important;
            }

            /* Output textbox */
            #custom-textbox,
            #custom-textbox input {
                border: 1px solid #439CEF !important;
                background-color: #020202 !important;
                color: #020202
                font-size: 17px !important;
                padding: 0 !important;
            }

            /* Labels */
            .label,
            .gradio-label,
            .gradio-checkbox label,
            .gradio-radio label,
            .gradio-slider .label {
                font-size: 17px !important;
                margin-bottom: 6px !important;
            }

            /* Dropdown options */
            .gradio-dropdown-options {
                font-size: 17px !important;
            }

            /* Buttons */
            .gradio-button {
                padding: 10px 18px !important;
            }

            /* Checkboxes and Radios */
            .gradio-checkbox input[type="checkbox"],
            .gradio-radio input[type="radio"] {
                width: 17px !important;
                height: 17px !important;
                margin-right: 8px !important;
            }

            /* Sliders */
            .gradio-slider input[type="range"] {
                height: 25px !important;
            }
            .gradio-slider .value {
                font-size: 17px !important;
            }

            /* Group borders */
            #Row {
                border: 3px solid #27272A !important;
            }

            #Input_Group {
                border: 0px solid #439CEF !important;
            }

            /* Buttons */
            #Submit_Btn {
                background-color: #439CEF !important;
                color: #FFFFFF !important;
                border-style: none !important;
            }
            #Submit_Btn2 {
                background-color: #D6B4FC !important;
                color: #000000 !important;
                border-style: none !important;
            }
            #Input_Box {
                border: 0px solid #439CEF !important;
            }
            """

        with gr.Blocks(theme=theme,css=css,js=js) as demo:
            # Output component at the top
            with gr.Row(elem_id="Input_Group"):
                output = gr.Textbox(label="",show_label=False, lines=1,elem_id="custom-textbox",placeholder="The link to your video will be shown here...")       
            Input_Group = gr.Group(elem_id="Input_Group")
            with Input_Group:
                with gr.Row(elem_id="Row"):
                    show_advanced = gr.Checkbox(label="Non-Quranic Text")
                    Bg_Enhancer = gr.Checkbox(label="Enhance background prompt with AI")
                with gr.Row(elem_id="Row"):
                    # Basic inputs (shown by default)
                    Quran_inputs = gr.Group()
                    with Quran_inputs:
                        BG_Prompt = gr.TextArea(label="",show_label=False,placeholder="Background Prompt (Optional)",elem_id="Input_Box",max_lines=6)
                        
                        # Put chapter and verse inputs in one row
                        with gr.Row():
                            Languages = gr.Dropdown(label="Select Language",choices=["English","Arabic","Both"],value="Both")
                            Chapter = gr.Number(label="Chapter",elem_id="Input_Box")
                            Starting_Verse = gr.Number(label="Initial Verse",elem_id="Input_Box")
                            Final_Verse = gr.Number(label="Final Verse",elem_id="Input_Box")
                            
                    
                    # Advanced inputs (hidden by default)
                    Normal_Text_inputs = gr.Group(visible=False)
                    with Normal_Text_inputs:
                        with gr.Row():
                            Text = gr.TextArea(label="",show_label=False,placeholder="Enter your text here...",max_lines=6)
                            BG_Prompt2 = gr.TextArea(label="",show_label=False,placeholder="Background Prompt (Optional)",max_lines=6)
                        with gr.Row():
                            API_Key = gr.Textbox(label="",show_label=False,placeholder="Elevenlabs API Key (May be required)",max_lines=1)
                            Voice_ID = gr.Textbox(label="",show_label=False,placeholder="Voice ID (Optional)")
                        # Voice settings with expand/collapse option
                        show_voice_settings = gr.Checkbox(label="Show Voice Settings")
                        
                        voice_settings = gr.Group(visible=False)
                        with voice_settings:
                            with gr.Row():
                                Stability = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=0.7, label="Stability")
                                Similarity = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=0.7, label="Similarity Boost")
                                Speed = gr.Slider(minimum=0.0, maximum=1.2, step=0.01, value=0.85, label="Speed")
                        
                        # Connect checkbox to show/hide voice settings
                        show_voice_settings.change(
                            fn=toggle_voice_settings,
                            inputs=show_voice_settings,
                            outputs=voice_settings
                        )
                
            # Create separate submit buttons for each input type
            with gr.Row():
                quran_submit = gr.Button("Generate Video", visible=True, elem_id="Submit_Btn")
                normal_submit = gr.Button("Generate Video", visible=False, elem_id="Submit_Btn2")
            
            # Connect the toggle function to show/hide both inputs and corresponding buttons
            show_advanced.change(
                fn=toggle_inputs,
                inputs=show_advanced,
                outputs=[Normal_Text_inputs, Quran_inputs, quran_submit, normal_submit]
            )
            Bg_Enhancer.change(
                fn=toggle_Bg_Enhancer,
                inputs=Bg_Enhancer,
                outputs=None
            )
            
            # NEW: Disable both buttons on click, then process, then re-enable
            quran_submit.click(
                fn=lambda: toggle_buttons(False),  # Disable both
                outputs=[quran_submit, normal_submit]
            ).then(
                fn=self.process_quran_inputs,
                inputs=[BG_Prompt, Chapter, Starting_Verse, Final_Verse,Languages],
                outputs=output
            ).then(
                fn=lambda: toggle_buttons(True),  # Re-enable both
                outputs=[quran_submit, normal_submit]
            )
            
            normal_submit.click(
                fn=lambda: toggle_buttons(False),  # Disable both
                outputs=[quran_submit, normal_submit]
            ).then(
                fn=self.process_normal_text,
                inputs=[Text, BG_Prompt2, Voice_ID, API_Key, Stability, Similarity, Speed],
                outputs=output
            ).then(
                fn=lambda: toggle_buttons(True),  # Re-enable both
                outputs=[quran_submit, normal_submit]
            )
            
        
        demo.queue()
        demo.launch()
    
    def Pipe_Line(self):
        if os.path.isfile("output_video.mp4"):
            os.remove("output_video.mp4")
        while my_dict["Q"]=="N" or my_dict["CurrentVerse"]<=my_dict["FinalVerse"]:
            try:
                self.image_gen()
            except:
                return "Error : Couldn't generate image..."
            try:
                self.audio_gen()
            except:
                return "Error : Either your voice ID is incorrect or the API Key has insufficient tokens. Try again leaving the voice ID empty and if the error still persists, provide an API from a free account..."
            if my_dict["Q"]=="Y":
                try:
                    self.text_grab()
                except:
                    return "Error : Couldn't get the text files for your verses. Please check if your verses exist..."
                try:
                    self.video_gen_Q()
                except:
                    return "Error : Couldn't generate video..."
            else:
                try:
                    self.video_gen_S()
                except:
                    return "Error : Couldn't generate video..."
            try:
                self.aud_vid_merger()
            except:
                return "Error : Couldn't merge the audio and video files..."
            try:
                self.delete_files()
            except:
                return "Error : Couldn't delete files..."
            global Text_Lines
            global Line_count
            Line_count +=1
            try:
                if(my_dict["CurrentVerse"]==my_dict["FinalVerse"]) and my_dict["Q"]=="Y" :
                    downloadURl=self.file_hoster()
                    return f"Link to your file: {downloadURl}"
                if len(Text_Lines)==Line_count and my_dict["Q"]=="N":
                    downloadURl=self.file_hoster()
                    return f"Link to your file: {downloadURl}"

            except:
                return "Error : Couldn't upload files to filebin. Please try again..."

            my_dict["CurrentVerse"] += 1
            my_dict["V"] = f"{my_dict['Chapter']}:{my_dict['CurrentVerse']}"
            if my_dict["Q"]=="N":
                my_dict["Text"]=Text_Lines[Line_count]

    def process_quran_inputs(self,bg_prompt, chapter, start_verse, end_verse,Lang):
        # Your Quran processing logic here
        if chapter and start_verse and end_verse:
            if chapter<1 or chapter>114:
                return "Error : Incorrect Chapter Number..."
            if start_verse>end_verse:
                return "Error : Your initial verse comes after the final verse..."
            my_dict["Q"]="Y"
            my_dict["V"]=f"{chapter}:{start_verse}"
            if bg_prompt:
                if my_dict["bg_enhance"]=="Y":
                    my_dict["BG"]=self.bg_prompt_enhancer(bg_prompt)
                else:
                    my_dict["BG"]=bg_prompt
            my_dict["Chapter"]=chapter
            my_dict["CurrentVerse"]=start_verse
            my_dict["FinalVerse"]=end_verse
            my_dict["Language"]=Lang
            return self.Pipe_Line()
        else:
            return "Error : Insufficient information..."

    def process_normal_text(self,text, bg_prompt, voice_id, api_key, stability, similarity, speed):
        # Your normal text processing logic here
        my_dict["Q"]="N"
        if bg_prompt:
            if my_dict["bg_enhance"]=="Y":
                my_dict["BG"]=self.bg_prompt_enhancer(bg_prompt)
            else:
                my_dict["BG"]=bg_prompt
        if text:
            global Line_count
            global Text_Lines
            Text_Lines = text.splitlines()
            my_dict["Text"]=Text_Lines[0]
            Line_count=0
        else:
            return "Error : No text..."
        if voice_id:
            _Voice_Settings["voice_id"]=voice_id
        if api_key:
            _Voice_Settings["User_Given_Api"]=api_key
        if stability:
            _Voice_Settings["_stability"]=stability
        if similarity:
            _Voice_Settings["_similarity_boost"]=similarity
        if speed:
            _Voice_Settings["_speed"]=speed
        return self.Pipe_Line()

    def bg_prompt_enhancer(self, bg_prompt):
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        messages = [{"role": "user", "content": f"Give me as response only an extremely enhanced version of the following prompt for image generation, just the prompt and nothing else. The prompt is'{bg_prompt}"}]
        completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=1,
                max_tokens=1024,
                top_p=1,
            )
        return completion.choices[0].message.content

    def image_gen(self):
        client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        response = client.images.generate(
            prompt=my_dict["BG"],
            model="black-forest-labs/FLUX.1-schnell-Free",
            width=1792,
            height=1024,
            steps=1,
            n=1,
            response_format="b64_json",
            stop=[]
        )
        # Extract Base64 string
        b64_data = response.data[0].b64_json
        # Decode and save image
        image_data = base64.b64decode(b64_data)
        with open("generated_image.png", "wb") as img_file:
            img_file.write(image_data)

    def audio_gen(self):
        if my_dict["Q"]=="Y":
            # Split the string at ':'
            part1, part2 = my_dict["V"].split(":")
            # Pad both parts with leading zeros to ensure 3 digits each
            url_ = "https://everyayah.com/data/Alafasy_128kbps/" + part1.zfill(3) + part2.zfill(3) + ".mp3"
            # Path where the file will be saved
            save_path = "quran_arabic.mp3"
            self.Q_Aud_Downloader(url_,save_path)
            url_2 = "https://everyayah.com/data/English/Sahih_Intnl_Ibrahim_Walk_192kbps/" + part1.zfill(3) + part2.zfill(3) + ".mp3"
            # Path where the file will be saved
            save_path2 = "quran_english.mp3"
            self.Q_Aud_Downloader(url_2,save_path2)
            self.audio_merger()

        else:
            API_KEY = os.getenv("ELEVENLABS_API_KEYS", "").split(",")

            def check_elevenlabs_credits(api_key):
                headers = {
                    "xi-api-key": api_key
                }
                
                try:
                    response = requests.get(
                        "https://api.elevenlabs.io/v1/user/subscription",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        #print(f"Used characters: {data.get('character_count')}")
                        #print(f"Total limit: {data.get('character_limit')}")
                        #print(f"Next reset: {data.get('next_character_count_reset_unix')}\n")
                        if data.get('character_count') + len(my_dict["Text"]) < data.get('character_limit'):
                            return True
                        else:
                            return False
                    else:
                        print(f"Error: {response.status_code} - {response.text}")
                        return None
                        
                except Exception as e:
                    print(f"Request failed: {str(e)}")
                    return False

            PROXY = {
                'http': '', 
                'https': ''
            }
            def __audio_gen():
                proxy_works = False
                made_audio = False
                proxy_count = 0
                while made_audio == False:
                    while proxy_works == False:
                        line_to_keep = ""
                        with open('working_proxies.txt', 'r') as file:   
                            if file:
                                for line in file:
                                    PROXY["http"]=line.strip()
                                    PROXY["https"]=line.strip()
                                    print(f"trying {line.strip()}")
                                    try:
                                        ip_check = requests.get("https://api.ipify.org?format=json", 
                                                            proxies=PROXY, 
                                                            timeout=15).json()
                                        print(f"Current IP: {ip_check['ip']}")
                                        proxy_works = True
                                        line_to_keep += line
                                        break  # Exit the file reading loop if successful
                                    except:
                                        print(f"Proxy {line} failed, trying next...")
                                        continue
                        if proxy_works == False:
                            with open('working_proxies.txt', 'w') as file:
                                file.write(line_to_keep)
                            # Get a list of current working proxies
                            response = requests.get("https://www.sslproxies.org/")
                            soup = BeautifulSoup(response.content, 'html.parser')
                            proxies = []

                            for row in soup.find("table", attrs={"class":"table"}).find_all("tr")[1:]:
                                tds = row.find_all("td")
                                try:
                                    ip = tds[0].text.strip()
                                    port = tds[1].text.strip()
                                    proxies.append(f"{ip}:{port}")
                                except:
                                    continue

                            # Test proxies until one works
                            for p in proxies[proxy_count:]:  # Now testing last 50
                                if proxy_count < len(proxies):
                                    proxy_count+=1
                                else: 
                                    proxy_count =0
                                proxy = f"http://{p}"
                                try:
                                    print(f"Testing {proxy}...")
                                    response = requests.get("https://api.ipify.org?format=json", 
                                                        proxies={"http": proxy, "https": proxy},
                                                        timeout=15)
                                    if response.status_code == 200:
                                        with open('working_proxies.txt', 'a') as file:
                                            file.write(f"{proxy}\n")
                                    break 
                                except:
                                    continue
                    with open('working_proxies.txt', 'w') as file:
                        file.write(line_to_keep)

                    with open('working_proxies.txt', 'r') as file:
                        for line in file:  # Bella voice
                            url = f"https://api.elevenlabs.io/v1/text-to-speech/iiidtqDt9FBdT1vfBluA"
                            # Usage
                            Usable_Api = ""
                            for Key in API_KEY:
                                if check_elevenlabs_credits(Key):
                                    Usable_Api = Key
                                    break
                            if not Usable_Api:
                                if check_elevenlabs_credits(_Voice_Settings["User_Given_Api"]):
                                    Usable_Api = _Voice_Settings["User_Given_Api"]

                            if not Usable_Api:
                                return

                            headers = {
                                "xi-api-key": Usable_Api,  # ← Replace this!
                                "Content-Type": "application/json"
                            }
                            
                            data = {
                                "text": my_dict["Text"],
                                "voice_settings": {
                                    "stability": _Voice_Settings["_stability"],
                                    "similarity_boost": _Voice_Settings["_similarity_boost"],
                                    "speed":_Voice_Settings["_speed"]
                                }
                            }
                            PROXY["http"] = line.strip()
                            PROXY["https"] = line.strip()
                            try:
                                response = requests.post(url, json=data, headers=headers, proxies=PROXY, timeout=10)
                                
                                if response.status_code == 200:
                                    with open("audio.mp3", "wb") as f:
                                        f.write(response.content)
                                    print("✅ Audio saved successfully!")
                                    with open("working_proxies.txt","w") as F:
                                        F.write(line)
                                        made_audio = False
                                        proxy_works = False
                                    return 
                                else:
                                    print(f"❌ Error {response.status_code}: {response.text}\n{line}")
                                    proxy_works = False
                                    with open("working_proxies.txt","w") as F:
                                        F.write("1")
                                    
                            except Exception as e:
                                print(f"⚠️ Request failed: {str(e)}\n{line}")
                                proxy_works = False
                                with open("working_proxies.txt","w") as F:
                                        F.write("1")
            __audio_gen()
            audio1 = AudioSegment.from_file("audio.mp3")
            # Create silence duration
            delay_seconds=1
            silence1 = AudioSegment.silent(duration=delay_seconds * 500)
            silence2 = AudioSegment.silent(duration=delay_seconds * 300)
              # Convert seconds to milliseconds
            # Combine the audio files with silence in between
            if my_dict["Q"]=="Y":
                combined_audio = silence1 + audio1 + silence1
            else:
                combined_audio = silence2 + audio1 + silence2
            # Export the combined audio
            combined_audio.export("audio.mp3", format="wav")
                  
    def Q_Aud_Downloader(self,url,save_path):
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        # Check if the request was successful
        response.raise_for_status()
        # Open the output file in write-binary mode
        with open(save_path, 'wb') as file:
            # Write the content to the file
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    def audio_merger(self, delay_seconds=1):
        # Load the audio files
        audio1 = AudioSegment.from_file("quran_arabic.mp3")
        audio2 = AudioSegment.from_file("quran_english.mp3")
        # Create silence duration
        silence = AudioSegment.silent(duration=delay_seconds * 1000)  # Convert seconds to milliseconds
        silence2 = AudioSegment.silent(duration=delay_seconds * 100)  # Convert seconds to milliseconds
        # Combine the audio files with silence in between
        combined_audio = audio1 + silence + audio2 + silence2
        # Export the combined audio
        combined_audio.export("audio.mp3", format="wav")

    def text_grab(self):
        """""Arabic"""""
        part1, part2 = my_dict["V"].split(":")
        image_url = "https://everyayah.com/data/images_png/" + part1 + "_" + part2 + ".png"
        # Send a request to fetch the image
        response = requests.get(image_url)
        with open("Arabic_Text.png", "wb") as file:
            file.write(response.content)

        """""English"""""
        # Set a user agent
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # URL of the verse
        url = "https://quranenc.com/en/browse/english_saheeh/" + my_dict["V"].replace(":","/")
        # Make the request
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find the translation text
        translation_div = soup.find('span', class_='ttc')
        result = ""
        bracket_content = ""
        inside_brackets = False
            
        for char in translation_div.text:
            if char == '[':
                inside_brackets = True
                bracket_content = ""
            elif char == ']' and inside_brackets:
                inside_brackets = False
                # Check if the bracket content contains any digits
                if any(c.isdigit() for c in bracket_content):
                    # If it contains digits, don't add it to the result
                    pass
                else:
                    # If it doesn't contain digits, add the full bracketed content to the result
                    result += '[' + bracket_content + ']'
            elif inside_brackets:
                bracket_content += char
            else:
                result += char
        my_dict["Text"] = result
        
    def video_gen_Q(self):
        def create_animation_sequence():
            # Configure output settings
            config.output_file = "animation_sequence.mp4"
            config.frame_rate = 30

            class AnimationSequence(Scene):
                def construct(self):
                    def wrap_text(text, width, spaces=6):
                        # Split the text into lines of approximately equal width
                        wrapped_lines = textwrap.wrap(text, width=width)
                        
                        # Add spaces to every line except the first one
                        wrapped_lines = [wrapped_lines[0]] + [f"{' ' * spaces}{line}" for line in wrapped_lines[1:]]
                        
                        # Join the lines with newline characters
                        return '\n'.join(wrapped_lines)

                    # Example for Manim
                    def get_wrapped_text_for_manim( text, width):
                        return wrap_text(text, width)
                    
                    # Get audio durations (replace with your actual audio files)
                    audio_file1 = "quran_arabic.mp3"
                    audio_file2 = "quran_english.mp3"
                    
                    duration1 = librosa.get_duration(filename=audio_file1)
                    duration2 = librosa.get_duration(filename=audio_file2)
                    
                    # Load background image
                    background = ImageMobject("generated_image.png")
                
                    # Force the background to cover the entire screen initially (without distortion)
                    background.set_height(config.frame_height)  # Scale to fit the height of the screen
                    background.set_width(config.frame_width)    # Scale to fit the width of the screen
                    self.add(background)
                    # Create overlay image (centered but initially not visible)
                    if my_dict["Language"]=="Arabic" or my_dict["Language"]=="Both":
                        overlay = ImageMobject("Arabic_Text.png")
                        overlay.scale(1.6)
                        overlay.move_to(ORIGIN)
                    
                    # Create the text (initially not visible)
                    if my_dict["Language"]=="English" or my_dict["Language"]=="Both":
                        wrapped_text = get_wrapped_text_for_manim(my_dict["Text"], 90)
                        text = Text(wrapped_text, font="Arial", color=BLACK, font_size=24, line_spacing=1 ).scale(0.8).move_to(ORIGIN)
                    
                    # Calculate total animation time
                    if my_dict["Language"]=="Both":
                        total_time = duration1 + duration2 + 3
                    elif my_dict["Language"]=="English":
                        total_time = duration2 + 3
                    else:
                        total_time = duration1 + 3
                    
                    # Define a function that updates the background scale continuously
                    def update_scale(mob, dt):
                        # Calculate scale factor based on elapsed time
                        elapsed_time = self.renderer.time
                        # Scale from 1.0 to 1.3 over the total duration
                        scale_factor = 1 + 0.3 * (elapsed_time / total_time)
                        # Apply the scaling relative to the original size
                        mob.set_height(config.frame_height * scale_factor)  # Maintain height
                        mob.set_width(config.frame_width * scale_factor)  # Maintain width
                    
                    # Start continuous update of background scale
                    background.add_updater(update_scale)
                    
                    # Now run the other animations independently
                    if my_dict["Language"]=="Arabic" or my_dict["Language"]=="Both":
                        self.play(FadeIn(overlay, run_time=0.5))
                        self.wait(duration1 - 1)
                        self.play(FadeOut(overlay, run_time=0.5))
                    if my_dict["Language"]=="English" or my_dict["Language"]=="Both":
                        self.play(Write(text, run_time=max(duration2 - 2, 0.5)))
                        self.wait(2.5)
                        self.play(FadeOut(text, run_time=0.5))
                        self.wait(0.1)
                    
                    # Remove the updater at the end
                    background.remove_updater(update_scale)


            
            # Create and render the scene
            scene = AnimationSequence()
            scene.render()

        # Execute the function
        create_animation_sequence()

    def video_gen_S(self):
        def create_animation_sequence():
            # Configure output settings
            config.output_file = "animation_sequence.mp4"
            config.frame_rate = 30

            class AnimationSequence(Scene):
                def construct(self):
                    def wrap_text(text, width, spaces=5):
                        # Split the text into lines of approximately equal width
                        wrapped_lines = textwrap.wrap(text, width=width)
                        
                        # Add spaces to every line except the first one
                        wrapped_lines = [wrapped_lines[0]] + [f"{' ' * spaces}{line}" for line in wrapped_lines[1:]]
                        
                        # Join the lines with newline characters
                        return '\n'.join(wrapped_lines)

                    # Example for Manim
                    def get_wrapped_text_for_manim(text, width):
                        return wrap_text(text, width)
                    
                    # Get audio durations (replace with your actual audio files)
                    audio_file = "audio.mp3"   
                    duration = librosa.get_duration(filename=audio_file)
                    
                    # Load background image
                    background = ImageMobject("generated_image.png")
                    # Force the background to cover the entire screen initially (without distortion)
                    background.set_height(config.frame_height)  # Scale to fit the height of the screen
                    background.set_width(config.frame_width)    # Scale to fit the width of the screen
                    self.add(background)
                    # Create the text (initially not visible)
                    wrapped_text = get_wrapped_text_for_manim(my_dict["Text"], 70)
                    text = Text(wrapped_text, font="Arial",color=BLACK, font_size=32, line_spacing=1 ).scale(0.8).move_to(ORIGIN)
                    
                    # Define a function that updates the background scale continuously
                    def update_scale(mob, dt):
                        # Calculate scale factor based on elapsed time
                        elapsed_time = self.renderer.time
                        # Scale from 1.0 to 1.3 over the total duration
                        scale_factor = 1 + 0.3 * (elapsed_time / duration)
                        # Apply the scaling relative to the original size
                        mob.set_height(config.frame_height * scale_factor)  # Maintain height
                        mob.set_width(config.frame_width * scale_factor)  # Maintain width
                    
                    # Start continuous update of background scale
                    background.add_updater(update_scale)
                    
                    # Now run the other animations independently
                    self.play(Write(text, run_time=max(duration - 2, 0.5)))
                    self.wait(0.5)
                    self.play(FadeOut(text, run_time=0.5))
                    self.wait(0.5)
                    
                    # Remove the updater at the end
                    background.remove_updater(update_scale)


            
            # Create and render the scene
            scene = AnimationSequence()
            scene.render()

        # Execute the function
        create_animation_sequence()

    def aud_vid_merger(self):
        if my_dict["Q"]=="Y" and my_dict["Language"]=="Arabic":
            os.remove("audio.mp3")
            os.rename("quran_arabic.mp3", "audio.mp3")
        if my_dict["Q"]=="Y" and my_dict["Language"]=="English":
            os.remove("audio.mp3")
            os.rename("quran_english.mp3", "audio.mp3")
        video = VideoFileClip("media/videos/1080p30/animation_sequence.mp4")
        # Load audio
        audio = AudioFileClip("audio.mp3")
        # Combine video with new audio
        video_with_audio = video.with_audio(audio)
        if os.path.exists("output_video.mp4"):
            # Save the new video
            video_with_audio.write_videofile("output_video_temp.mp4", codec="libx264", audio_codec="aac")
            video.close()
            audio.close()
            video_with_audio.close()
            # Paths to video files
            video1_path = "output_video.mp4"
            video2_path = "output_video_temp.mp4"
            final_output = "final_output_video.mp4"

            # Step 1: Create a file list for FFmpeg
            file_list = "file_list.txt"
            with open(file_list, "w") as f:
                f.write(f"file '{video1_path}'\n")
                f.write(f"file '{video2_path}'\n")

            ffmpeg_command = [
                "ffmpeg", 
                "-f", "concat", 
                "-safe", "0", 
                "-i", file_list, 
                "-c:v", "libx264", 
                "-c:a", "aac", 
                "-strict", "experimental", 
                final_output
            ]

            # Run the FFmpeg command
            subprocess.run(ffmpeg_command)
            os.remove(file_list)
            os.remove("output_video.mp4")
            os.rename("final_output_video.mp4", "output_video.mp4")
        else:
            # Save the new video
            video_with_audio.write_videofile("output_video.mp4", codec="libx264", audio_codec="aac")
            video.close()
            audio.close()
            video_with_audio.close()

    def file_hoster(self):
        # Generate a random bin ID (you can also use a fixed name if you prefer)
        def generate_random_bin_id(length=8):
            chars = string.ascii_lowercase + string.digits
            return ''.join(random.choice(chars) for _ in range(length))

        # File to upload
        file_path = 'output_video.mp4'
        file_name = os.path.basename(file_path)

        # Generate a random bin ID
        bin_id = generate_random_bin_id()

        # Construct the proper URL with the bin ID
        url = f'https://filebin.net/{bin_id}/{file_name}'

        # Set headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # Open the file in binary mode
        with open(file_path, 'rb') as file:
            # Send a POST request with the file
            response = requests.post(url, data=file, headers=headers)

        # Check the response status and output the result
        if response.status_code in [200, 201]:
            print("File uploaded successfully!")
            # Extract bin ID from response
            bin_id = response.json()["bin"]["id"]
            file_name = response.json()["file"]["filename"]
            # Construct the direct URL to the file
            download_url = f"https://filebin.net/{bin_id}/{file_name}"
            with open("url.txt", "a") as file:
                file.write(f"\n{download_url}")
            return download_url
            
            # Print the full response (contains metadata)
            #print("Response:", response.json())
        else:
            print(f"Failed to upload file. Status code: {response.status_code}")
            print("Response content:", response.text)  # Helps to debug the error

    def delete_files(self):
        directory = "media/texts/"
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
                
            # Check if it's a file and delete it
            if os.path.isfile(file_path):
                os.remove(file_path)
        directory = "media/videos/1080p30/partial_movie_files/AnimationSequence"
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
                
            # Check if it's a file and delete it
            if os.path.isfile(file_path):
                os.remove(file_path)
        directories = [#"media/videos/1080p30/animation_sequence.mp4",
                    "Arabic_Text.png",
                    "audio.mp3",
                    "generated_image.png",
                    "output_video_temp.mp4",
                    "quran_arabic.mp3",
                    "quran_english.mp3"]
        for directory in directories:
            if os.path.isfile(directory):
                os.remove(directory)

fnc = fn()




