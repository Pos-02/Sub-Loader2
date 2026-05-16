import os
import time
import json
import shutil
import tempfile
import threading
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
import patoolib
import re

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
WEBSITE_URL = "https://www.nexusmods.com/subnautica2" 

IGNORED_MODS = [
    "shared", 
    "modref", 
    "linetracemod", 
    "bpml_genericfunctions", 
    "bpmodloadermod", 
    "cheatmanagerenablermod", 
    "consolecommandsmod", 
    "consoleenablermod", 
    "keybinds", 
    "splitscreenmod"
]

class SubLoader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sub Loader v1.0 (UE4SS)")
        self.geometry("1100x750")

        self.config = self.load_config()
        self.exe_path = ctk.StringVar(value=self.config.get("last_exe_path", ""))
        self.selected_archives = []
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_view()
        self.create_mod_manager_view()
        
        self.show_installer()
        self.log("-------------", "")
        self.log("Subnautica 2 Edition", "")
        self.log("-------------\n", "")
        self.log("Sub loader loaded", "INFO")
        self.log("Welcome to Sub Loader 2", "INFO")

        if not self.exe_path.get():
            self.auto_detect_exe(silent=True)

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SUB LOADER 2", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_nav_install = ctk.CTkButton(self.sidebar_frame, text="Installer", command=self.show_installer)
        self.btn_nav_install.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="Add Mod Files", command=self.select_files)
        self.btn_add.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_nav_mods = ctk.CTkButton(self.sidebar_frame, text="Manage Mods", command=self.show_mod_manager)
        self.btn_nav_mods.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_web = ctk.CTkButton(self.sidebar_frame, text="Visit Nexus", command=self.open_website)
        self.btn_web.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_auto_detect = ctk.CTkButton(self.sidebar_frame, text="Auto Detect EXE", command=lambda: self.auto_detect_exe(silent=False))
        self.btn_auto_detect.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.btn_path = ctk.CTkButton(self.sidebar_frame, text="Select Game EXE Manually", fg_color="transparent", border_width=1, command=self.select_game_exe)
        self.btn_path.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light"], command=ctk.set_appearance_mode)
        self.appearance_mode_menu.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

    def open_website(self):
        webbrowser.open(WEBSITE_URL)

    def create_main_view(self):
        self.installer_view = ctk.CTkFrame(self, fg_color="transparent")
        self.installer_view.grid_columnconfigure(0, weight=1)
        self.installer_view.grid_rowconfigure(1, weight=1)

        self.path_card = ctk.CTkFrame(self.installer_view, height=50)
        self.path_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.path_display = ctk.CTkLabel(self.path_card, textvariable=self.exe_path, font=("Segoe UI", 11), text_color="#3b8ed0")
        self.path_display.pack(padx=20, pady=10, side="left", fill="x")

        self.console = ctk.CTkTextbox(self.installer_view, font=("Consolas", 13), fg_color="#0a0a0a", text_color="#d1d1d1", border_width=2, border_color="#2d2d2d")
        self.console.grid(row=1, column=0, sticky="nsew")
        
        self.bottom_frame = ctk.CTkFrame(self.installer_view, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 20))
        self.progress_bar.set(0)

        self.install_button = ctk.CTkButton(self.bottom_frame, text="RUN INSTALLER", height=45, width=200, font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", command=self.start_installation)
        self.install_button.grid(row=0, column=1)

    def create_mod_manager_view(self):
        self.manager_view = ctk.CTkFrame(self, fg_color="transparent")
        self.manager_view.grid_columnconfigure(0, weight=1)
        self.manager_view.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self.manager_view, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(0, 20), sticky="ew")

        self.manager_header = ctk.CTkLabel(self.header_frame, text="Installed UE4SS Mod Folders", font=ctk.CTkFont(size=20, weight="bold"))
        self.manager_header.pack(side="left")

        self.refresh_button = ctk.CTkButton(self.header_frame, text="⟳ Refresh", width=90, height=26, font=ctk.CTkFont(size=12, weight="bold"), command=self.refresh_mod_list)
        self.refresh_button.pack(side="right", padx=5)

        self.mods_scroll_frame = ctk.CTkScrollableFrame(self.manager_view, fg_color="#1a1a1a", border_width=2, border_color="#2d2d2d")
        self.mods_scroll_frame.grid(row=1, column=0, sticky="nsew")

    def show_installer(self):
        self.manager_view.grid_forget()
        self.installer_view.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")

    def show_mod_manager(self):
        self.installer_view.grid_forget()
        self.manager_view.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        self.refresh_mod_list()

    def auto_detect_exe(self, silent=False):
        """Przeszukuje standardowe lokalizacje Steam w celu znalezienia Subnautica2.exe"""
        drives = ["C", "D", "E", "F", "G"]
        common_paths = [
            os.path.join("SteamLibrary", "steamapps", "common", "Subnautica2", "Subnautica2.exe"),
            os.path.join("Program Files (x86)", "Steam", "steamapps", "common", "Subnautica2", "Subnautica2.exe"),
            os.path.join("Steam", "steamapps", "common", "Subnautica2", "Subnautica2.exe")
        ]

        found_path = None
        for drive in drives:
            for rel_path in common_paths:
                full_path = f"{drive}:\\{rel_path}"
                if os.path.exists(full_path):
                    found_path = full_path
                    break
            if found_path:
                break

        if found_path:
            self.exe_path.set(found_path)
            self.save_config(found_path)
            self.log(f"Auto-detected game location: {found_path}", "SUCCESS")
            if not silent:
                self.log("Game EXE automatically detected and set.", "INFO")
        else:
            if not silent:
                self.log("Automatic game detection failed. Please select EXE manually.", "WARNING")


    def clean_mod_name(self, name):
        name = re.sub(r'\d+(\.\d+)+', '', name)
        name = re.sub(r'\b\d{5,}\b', '', name)
        name = re.sub(r'[-_.]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        words = name.strip().split()
        clean_words = [w for w in words if not any(char.isdigit() for char in w)]
        if not clean_words: 
            return name.strip().title()
        return " ".join(clean_words).title()

    def get_mods_directory(self):
        exe_file = self.exe_path.get()
        if not exe_file:
            return None
        game_root_folder = os.path.dirname(exe_file)
        return os.path.join(game_root_folder, "Subnautica2", "Binaries", "Win64", "ue4ss", "Mods")

    def refresh_mod_list(self):
        for widget in self.mods_scroll_frame.winfo_children():
            widget.destroy()

        if not self.exe_path.get():
            ctk.CTkLabel(self.mods_scroll_frame, text="Select game EXE first.").pack(pady=20)
            return

        mods_dir = self.get_mods_directory()
        if not os.path.exists(mods_dir):
            ctk.CTkLabel(self.mods_scroll_frame, text=f"UE4SS 'Mods' folder not found.\nExpected path: {mods_dir}").pack(pady=20)
            return

        found_folders = False
        for folder_name in os.listdir(mods_dir):
            folder_path = os.path.join(mods_dir, folder_name)
            
            if os.path.isdir(folder_path) and folder_name.lower() not in IGNORED_MODS:
                found_folders = True
                
                enabled_txt = os.path.join(folder_path, "enabled.txt")
                disabled_txt = os.path.join(folder_path, "disabled.txt")
                
                if not os.path.exists(enabled_txt) and not os.path.exists(disabled_txt):
                    with open(enabled_txt, "w") as f:
                        f.write("enabled")
                
                is_disabled = os.path.exists(disabled_txt)
                display_name = self.clean_mod_name(folder_name)
                
                self.create_mod_entry(display_name, folder_path, is_disabled)
        
        if not found_folders:
            ctk.CTkLabel(self.mods_scroll_frame, text="No custom mod folders found.").pack(pady=20)

    def create_mod_entry(self, display_name, folder_path, is_disabled):
        container_frame = ctk.CTkFrame(self.mods_scroll_frame, fg_color="#2d2d2d" if not is_disabled else "#242424")
        container_frame.pack(fill="x", pady=5, padx=5)

        top_bar = ctk.CTkFrame(container_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=5)

        lbl = ctk.CTkLabel(top_bar, text=display_name, font=("Segoe UI", 12, "bold"), text_color="white" if not is_disabled else "#777777")
        lbl.pack(side="left", padx=5, pady=5)

        switch_var = ctk.StringVar(value="off" if is_disabled else "on")
        
        def toggle():
            enabled_file = os.path.join(folder_path, "enabled.txt")
            disabled_file = os.path.join(folder_path, "disabled.txt")
            if switch_var.get() == "on":
                if os.path.exists(disabled_file):
                    os.rename(disabled_file, enabled_file)
            else:
                if os.path.exists(enabled_file):
                    os.rename(enabled_file, disabled_file)
            self.refresh_mod_list()

        switch = ctk.CTkSwitch(top_bar, text="Enabled" if not is_disabled else "Disabled", 
                               variable=switch_var, onvalue="on", offvalue="off", command=toggle)
        switch.pack(side="right", padx=5)

        config_panel = ctk.CTkFrame(container_frame, fg_color="#1e1e1e", height=0)
        config_is_open = [False]

        def toggle_config_view():
            if not config_is_open[0]:
                config_panel.pack(fill="x", padx=10, pady=(0, 10))
                btn_config.configure(fg_color="#1f538d", text="Close Config")
                config_is_open[0] = True
                load_config_content()
            else:
                config_panel.pack_forget()
                btn_config.configure(fg_color="transparent", text="Edit Config")
                config_is_open[0] = False

        btn_config = ctk.CTkButton(top_bar, text="Edit Config", width=100, height=24, fg_color="transparent", border_width=1, command=toggle_config_view)
        btn_config.pack(side="right", padx=15)

        config_text_area = ctk.CTkTextbox(config_panel, font=("Consolas", 12), height=150, fg_color="#121212")
        config_text_area.pack(fill="x", padx=10, pady=10)

        config_path = os.path.join(folder_path, "scripts", "config.lua")

        def load_config_content():
            config_text_area.delete("1.0", "end")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_text_area.insert("1.0", f.read())
                except Exception as e:
                    config_text_area.insert("1.0", f"-- Error loading file: {str(e)}")
            else:
                config_text_area.insert("1.0", "-- config.lua not found in scripts/. Click Save to create it.")

        def save_config_content():
            scripts_dir = os.path.dirname(config_path)
            try:
                if not os.path.exists(scripts_dir):
                    os.makedirs(scripts_dir)
                content = config_text_area.get("1.0", "end-1c")
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Success", "config.lua saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

        btn_save = ctk.CTkButton(config_panel, text="Save Config", fg_color="#28a745", hover_color="#218838", height=28, command=save_config_content)
        btn_save.pack(anchor="e", padx=10, pady=(0, 10))

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}] "
        self.console.insert("end", prefix + message + "\n")
        self.console.see("end")
        self.update_idletasks()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def save_config(self, path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_exe_path": path}, f, indent=4)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Archives", "*.zip *.rar *.7z")])
        if files:
            self.selected_archives = list(files)
            self.log(f"Queued {len(files)} archive(s).", "INFO")

    def select_game_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.exe_path.set(path)
            self.save_config(path)
            self.log(f"Target EXE set: {os.path.basename(path)}", "SUCCESS")

    def start_installation(self):
        if not self.selected_archives or not self.exe_path.get():
            self.log("Error: Select mod files or game .exe.", "ERROR")
            return
        self.progress_bar.set(0)
        self.install_button.configure(state="disabled", text="PROCESSING...")
        threading.Thread(target=self.run_install_logic, daemon=True).start()

    def run_install_logic(self):
        mods_dir = self.get_mods_directory()
        if not mods_dir:
            self.log("Error: Target folder could not be determined.", "ERROR")
            self.install_button.configure(state="normal", text="RUN INSTALLER")
            return

        total = len(self.selected_archives)
        success_count = 0
        for i, archive in enumerate(self.selected_archives):
            mod_name = os.path.splitext(os.path.basename(archive))[0]
            self.log(f"Installing: {mod_name}...", "INFO")
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    self.log(f"Extracting archive: {mod_name}...", "INFO")
                    patoolib.extract_archive(archive, outdir=temp_dir, verbosity=-1)
                    
                    extracted_items = os.listdir(temp_dir)
                    if "scripts" not in extracted_items and len(extracted_items) == 1:
                        nested_folder_name = extracted_items[0]
                        nested_folder_path = os.path.join(temp_dir, nested_folder_name)
                        
                        if os.path.isdir(nested_folder_path):
                            self.log(f"Nested folder '{nested_folder_name}' detected. Restructuring...", "INFO")
                            for item in os.listdir(nested_folder_path):
                                shutil.move(os.path.join(nested_folder_path, item), temp_dir)
                            os.rmdir(nested_folder_path)
                    
                    mods_target = os.path.join(mods_dir, mod_name)
                    if os.path.exists(mods_target):
                        shutil.rmtree(mods_target)
                        
                    shutil.copytree(temp_dir, mods_target) 
                    
                    with open(os.path.join(mods_target, "enabled.txt"), "w") as f:
                        f.write("enabled")
                        
                self.log(f"Installed: {mod_name}", "SUCCESS")
                success_count += 1
            except Exception as e:
                self.log(f"Error {mod_name}: {str(e)}\nMake sure you have patool and winrar/7zip installed.", "ERROR")
            self.progress_bar.set((i + 1) / total)
        self.log(f"Finished. {success_count}/{total} successful.", "SUCCESS")
        self.install_button.configure(state="normal", text="RUN INSTALLER")
        self.selected_archives = [] 
        self.after(2300, lambda: self.progress_bar.set(0))

if __name__ == "__main__":
    app = SubLoader()
    app.mainloop()