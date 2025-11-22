"""
Windows AI - GUI Application
Simple, user-friendly graphical interface for Windows AI
"""

import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
import threading
from typing import Optional


class WindowsAIGUI:
    """Main GUI Application for Windows AI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows AI - Unified AI Platform")
        self.root.geometry("1000x700")

        # Set app icon (if available)
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        self.orchestrator = None
        self.loop = None
        self.init_thread = None

        self._setup_ui()
        self._start_background_loop()

    def _setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Capabilities", command=self._show_capabilities)

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Top frame with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Create tabs
        self._create_chat_tab()
        self._create_image_tab()
        self._create_audio_tab()
        self._create_tools_tab()
        self._create_status_tab()

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(status_frame, text="Initializing Windows AI...", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start()

    def _create_chat_tab(self):
        """Create the chat tab"""
        chat_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(chat_frame, text="💬 Chat")

        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        # Chat history
        self.chat_history = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20)
        self.chat_history.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.chat_history.config(state=tk.DISABLED)

        # Input frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)

        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.chat_input.bind("<Return>", lambda e: self._send_chat())

        self.send_button = ttk.Button(input_frame, text="Send", command=self._send_chat)
        self.send_button.grid(row=0, column=1)

        # Provider selection
        provider_frame = ttk.Frame(chat_frame)
        provider_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W,), pady=(10, 0))

        ttk.Label(provider_frame, text="Provider:").pack(side=tk.LEFT, padx=(0, 5))
        self.provider_var = tk.StringVar(value="openai")
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.provider_var,
                                       values=["openai", "anthropic", "google", "mistral", "cohere", "groq"],
                                       state="readonly", width=15)
        provider_combo.pack(side=tk.LEFT)

    def _create_image_tab(self):
        """Create the image generation tab"""
        image_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(image_frame, text="🎨 Images")

        # Prompt input
        ttk.Label(image_frame, text="Image Prompt:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.image_prompt = scrolledtext.ScrolledText(image_frame, wrap=tk.WORD, height=4)
        self.image_prompt.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Generate button
        self.generate_image_button = ttk.Button(image_frame, text="Generate Image", command=self._generate_image)
        self.generate_image_button.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        # Image display area
        self.image_label = ttk.Label(image_frame, text="Generated image will appear here", relief=tk.SUNKEN)
        self.image_label.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(3, weight=1)

    def _create_audio_tab(self):
        """Create the audio processing tab"""
        audio_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(audio_frame, text="🎤 Audio")

        # Text-to-Speech section
        tts_frame = ttk.LabelFrame(audio_frame, text="Text-to-Speech", padding="10")
        tts_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.tts_input = scrolledtext.ScrolledText(tts_frame, wrap=tk.WORD, height=4)
        self.tts_input.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.tts_button = ttk.Button(tts_frame, text="Generate Speech", command=self._generate_speech)
        self.tts_button.grid(row=1, column=0, sticky=tk.W)

        tts_frame.columnconfigure(0, weight=1)

        # Speech-to-Text section
        stt_frame = ttk.LabelFrame(audio_frame, text="Speech-to-Text", padding="10")
        stt_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.stt_file_label = ttk.Label(stt_frame, text="No file selected")
        self.stt_file_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        self.stt_select_button = ttk.Button(stt_frame, text="Select Audio File", command=self._select_audio_file)
        self.stt_select_button.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 10))

        self.stt_transcribe_button = ttk.Button(stt_frame, text="Transcribe", command=self._transcribe_audio)
        self.stt_transcribe_button.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))

        self.stt_result = scrolledtext.ScrolledText(stt_frame, wrap=tk.WORD, height=6)
        self.stt_result.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.stt_result.config(state=tk.DISABLED)

        stt_frame.columnconfigure(0, weight=1)

        audio_frame.columnconfigure(0, weight=1)

    def _create_tools_tab(self):
        """Create the tools tab"""
        tools_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tools_frame, text="🛠️ Tools")

        # Web Search
        search_frame = ttk.LabelFrame(tools_frame, text="Web Search", padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        search_input_frame.columnconfigure(0, weight=1)

        self.search_input = ttk.Entry(search_input_frame)
        self.search_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        self.search_button = ttk.Button(search_input_frame, text="Search", command=self._search_web)
        self.search_button.grid(row=0, column=1)

        self.search_results = scrolledtext.ScrolledText(search_frame, wrap=tk.WORD, height=8)
        self.search_results.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.search_results.config(state=tk.DISABLED)

        search_frame.columnconfigure(0, weight=1)

        # Task Automation
        automation_frame = ttk.LabelFrame(tools_frame, text="Task Automation", padding="10")
        automation_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(automation_frame, text="Describe the task:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.automation_input = scrolledtext.ScrolledText(automation_frame, wrap=tk.WORD, height=4)
        self.automation_input.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.automate_button = ttk.Button(automation_frame, text="Automate", command=self._automate_task)
        self.automate_button.grid(row=2, column=0, sticky=tk.W)

        automation_frame.columnconfigure(0, weight=1)

        tools_frame.columnconfigure(0, weight=1)

    def _create_status_tab(self):
        """Create the status tab"""
        status_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(status_frame, text="📊 Status")

        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.status_text.config(state=tk.DISABLED)

        refresh_button = ttk.Button(status_frame, text="Refresh Status", command=self._refresh_status)
        refresh_button.pack()

    def _start_background_loop(self):
        """Start asyncio event loop in background thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.init_thread = threading.Thread(target=run_loop, daemon=True)
        self.init_thread.start()

        # Initialize orchestrator
        self.root.after(100, self._initialize_orchestrator)

    def _initialize_orchestrator(self):
        """Initialize the orchestrator"""
        async def init():
            from windows_ai.core.orchestrator import quick_start
            self.orchestrator = await quick_start()

        future = asyncio.run_coroutine_threadsafe(init(), self.loop)

        def check_init():
            if future.done():
                try:
                    future.result()
                    self.progress.stop()
                    self.status_label.config(text="✅ Windows AI Ready - All systems operational")
                    self._refresh_status()
                except Exception as e:
                    self.progress.stop()
                    self.status_label.config(text=f"❌ Initialization failed: {e}")
            else:
                self.root.after(100, check_init)

        self.root.after(100, check_init)

    def _send_chat(self):
        """Send chat message"""
        message = self.chat_input.get().strip()
        if not message:
            return

        self.chat_input.delete(0, tk.END)
        self._append_chat(f"You: {message}\n")

        async def send():
            response = await self.orchestrator.chat(message, self.provider_var.get())
            return response

        future = asyncio.run_coroutine_threadsafe(send(), self.loop)

        def check_response():
            if future.done():
                try:
                    response = future.result()
                    self._append_chat(f"AI: {response}\n\n")
                except Exception as e:
                    self._append_chat(f"Error: {e}\n\n")
            else:
                self.root.after(100, check_response)

        self.root.after(100, check_response)

    def _append_chat(self, text: str):
        """Append text to chat history"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, text)
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def _generate_image(self):
        """Generate image from prompt"""
        prompt = self.image_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("No Prompt", "Please enter an image prompt")
            return

        self.status_label.config(text="Generating image...")

        async def generate():
            image_bytes = await self.orchestrator.generate_image(prompt)
            # Save and display
            output_path = Path.home() / ".windows_ai" / "temp" / "generated_image.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            return str(output_path)

        future = asyncio.run_coroutine_threadsafe(generate(), self.loop)

        def check_result():
            if future.done():
                try:
                    path = future.result()
                    self.status_label.config(text=f"✅ Image saved to {path}")
                    self.image_label.config(text=f"Image saved to:\n{path}")
                except Exception as e:
                    self.status_label.config(text=f"❌ Error: {e}")
            else:
                self.root.after(100, check_result)

        self.root.after(100, check_result)

    def _generate_speech(self):
        """Generate speech from text"""
        text = self.tts_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Text", "Please enter text to convert to speech")
            return

        self.status_label.config(text="Generating speech...")

        async def generate():
            audio_bytes = await self.orchestrator.speak(text)
            output_path = Path.home() / ".windows_ai" / "temp" / "output.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return str(output_path)

        future = asyncio.run_coroutine_threadsafe(generate(), self.loop)

        def check_result():
            if future.done():
                try:
                    path = future.result()
                    self.status_label.config(text=f"✅ Audio saved to {path}")
                    messagebox.showinfo("Success", f"Audio saved to:\n{path}")
                except Exception as e:
                    self.status_label.config(text=f"❌ Error: {e}")
            else:
                self.root.after(100, check_result)

        self.root.after(100, check_result)

    def _select_audio_file(self):
        """Select audio file for transcription"""
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.ogg"), ("All Files", "*.*")]
        )
        if filename:
            self.stt_file_path = filename
            self.stt_file_label.config(text=f"Selected: {Path(filename).name}")

    def _transcribe_audio(self):
        """Transcribe selected audio file"""
        if not hasattr(self, 'stt_file_path'):
            messagebox.showwarning("No File", "Please select an audio file first")
            return

        self.status_label.config(text="Transcribing audio...")

        async def transcribe():
            text = await self.orchestrator.transcribe(self.stt_file_path)
            return text

        future = asyncio.run_coroutine_threadsafe(transcribe(), self.loop)

        def check_result():
            if future.done():
                try:
                    text = future.result()
                    self.stt_result.config(state=tk.NORMAL)
                    self.stt_result.delete("1.0", tk.END)
                    self.stt_result.insert("1.0", text)
                    self.stt_result.config(state=tk.DISABLED)
                    self.status_label.config(text="✅ Transcription complete")
                except Exception as e:
                    self.status_label.config(text=f"❌ Error: {e}")
            else:
                self.root.after(100, check_result)

        self.root.after(100, check_result)

    def _search_web(self):
        """Search the web"""
        query = self.search_input.get().strip()
        if not query:
            return

        self.status_label.config(text="Searching...")

        async def search():
            results = await self.orchestrator.search_web(query)
            return results

        future = asyncio.run_coroutine_threadsafe(search(), self.loop)

        def check_result():
            if future.done():
                try:
                    results = future.result()
                    self.search_results.config(state=tk.NORMAL)
                    self.search_results.delete("1.0", tk.END)
                    for i, result in enumerate(results[:10], 1):
                        self.search_results.insert(tk.END, f"{i}. {result.get('title', 'No title')}\n")
                        self.search_results.insert(tk.END, f"   {result.get('url', '')}\n\n")
                    self.search_results.config(state=tk.DISABLED)
                    self.status_label.config(text="✅ Search complete")
                except Exception as e:
                    self.status_label.config(text=f"❌ Error: {e}")
            else:
                self.root.after(100, check_result)

        self.root.after(100, check_result)

    def _automate_task(self):
        """Automate a task"""
        task = self.automation_input.get("1.0", tk.END).strip()
        if not task:
            messagebox.showwarning("No Task", "Please describe the task to automate")
            return

        self.status_label.config(text="Automating task...")

        async def automate():
            result = await self.orchestrator.automate_task(task)
            return result

        future = asyncio.run_coroutine_threadsafe(automate(), self.loop)

        def check_result():
            if future.done():
                try:
                    result = future.result()
                    self.status_label.config(text="✅ Task complete")
                    messagebox.showinfo("Automation Result", str(result))
                except Exception as e:
                    self.status_label.config(text=f"❌ Error: {e}")
            else:
                self.root.after(100, check_result)

        self.root.after(100, check_result)

    def _refresh_status(self):
        """Refresh system status"""
        if not self.orchestrator:
            return

        status = self.orchestrator.status()

        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", "📊 Windows AI System Status\n")
        self.status_text.insert(tk.END, "="*50 + "\n\n")
        self.status_text.insert(tk.END, f"Initialized: {'✅' if status['initialized'] else '❌'}\n")
        self.status_text.insert(tk.END, f"Managers Loaded: {status['managers_loaded']}\n")
        self.status_text.insert(tk.END, f"Performance Mode: {status['config'].get('performance_mode', 'N/A')}\n")
        self.status_text.insert(tk.END, f"Privacy Mode: {status['config'].get('privacy_mode', 'N/A')}\n\n")

        capabilities = self.orchestrator.list_capabilities()
        total_caps = sum(len(caps) for caps in capabilities.values())
        self.status_text.insert(tk.END, f"Total Capabilities: {total_caps}\n\n")
        self.status_text.insert(tk.END, "Capability Categories:\n")
        for category, caps in capabilities.items():
            self.status_text.insert(tk.END, f"  • {category}: {len(caps)} features\n")

        self.status_text.config(state=tk.DISABLED)

    def _open_settings(self):
        """Open settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog coming soon!")

    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About Windows AI",
                           "Windows AI - Unified AI Platform\n\n"
                           "Version: 1.0.0\n"
                           "2500+ AI Capabilities\n"
                           "43 Integrated Managers\n\n"
                           "© 2024 Windows AI")

    def _show_capabilities(self):
        """Show capabilities list"""
        if not self.orchestrator:
            messagebox.showwarning("Not Ready", "Windows AI is still initializing")
            return

        capabilities = self.orchestrator.list_capabilities()
        total = sum(len(caps) for caps in capabilities.values())

        cap_text = f"Windows AI Capabilities ({total} total)\n\n"
        for category, caps in capabilities.items():
            cap_text += f"{category.upper()} ({len(caps)} features)\n"

        messagebox.showinfo("Capabilities", cap_text)

    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

        # Cleanup
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)


def main():
    """Main entry point for GUI"""
    app = WindowsAIGUI()
    app.run()


if __name__ == "__main__":
    main()
