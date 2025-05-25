import json
import random
import sqlite3
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import customtkinter as ctk
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import os
import webbrowser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Global variables
driver = None
is_stopped = False
is_paused = False
current_user = ""  # User whose followers are being processed
login_user_id = "" # User ID used for login
followed_count_total = 0  # Track total followed accounts
current_theme = "spotify"  # Default theme
current_language = "English"  # Default language
lang = {}  # Will hold language strings

# ---------------- Database Functions ----------------
def create_db():
    conn = sqlite3.connect("followed_users.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS followed_users (
                        user_url TEXT PRIMARY KEY)""")
    conn.commit()
    conn.close()

def load_followed_users():
    conn = sqlite3.connect("followed_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_url FROM followed_users")
    followed_users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return followed_users

def save_followed_user(user_url):
    conn = sqlite3.connect("followed_users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO followed_users (user_url) VALUES (?)", (user_url,))
    conn.commit()
    conn.close()

def get_total_followed_count():
    conn = sqlite3.connect("followed_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM followed_users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ---------------- Language Functions ----------------
import os

def load_language(language_name):
    global lang, current_language
    current_language = language_name
    
    lang_path = os.path.join("lang", f"{language_name}.json")
    
    try:
        with open(lang_path, "r", encoding="utf-8") as f:
            lang = json.load(f)
        
        save_language_preference(language_name)
        
        if "text_log" in globals():
            log_yaz(f"🌐 Language changed to: {language_name}")
        
        # Update UI with new language
        update_ui_language()
        
        return True
    except Exception as e:
        print(f"Error loading language file: {e}")
        
        # Fallback to English
        if language_name != "English":
            fallback_path = os.path.join("lang", "English.json")
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    lang = json.load(f)
                current_language = "English"
                update_ui_language()  # Update UI with fallback language
                return True
            except:
                return False
        return False


def get_text(key_path, **kwargs):
    """Get text from language file using dot notation path"""
    keys = key_path.split(".")
    value = lang
    
    try:
        for key in keys:
            value = value[key]
        
        # Replace placeholders if any kwargs provided
        if kwargs and isinstance(value, str):
            return value.format(**kwargs)
        return value
    except (KeyError, TypeError):
        # Return the key path if the text is not found
        print(f"Warning: Language key not found: {key_path}")
        return key_path

def save_language_preference(language_name):
    try:
        with open("language_preference.json", "w") as f:
            json.dump({"language": language_name}, f)
    except Exception as e:
        print(f"Error saving language preference: {e}")

def load_language_preference():
    try:
        with open("language_preference.json", "r") as f:
            data = json.load(f)
            return data.get("language", "English")
    except (FileNotFoundError, json.JSONDecodeError):
        return "English"  # Default language

def get_available_languages():
    """Get list of available language files"""
    languages = []
    # Changed to scan the lang directory instead of the root directory
    if os.path.exists("lang"):
        for file in os.listdir("lang"):
            if file.endswith(".json"):
                languages.append(file.replace(".json", ""))
    return languages

# ---------------- Theme Functions ----------------
def load_themes():
    """Load themes from themes.json file"""
    try:
        with open("themes.json", "r") as f:
            return json.load(f)["themes"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading themes: {e}")
        # Return default themes if file not found or invalid
        return {
            "spotify": {
                "name": "Spotify Green (Dark)",
                "appearance_mode": "dark",
                "color_theme": "green",
                "colors": {
                    "primary": "#1DB954",
                    "secondary": "#1ED760",
                    "bg": "#121212",
                    "text": "#FFFFFF",
                    "accent": "#1DB954"
                }
            },
            "night_purple": {
                "name": "Night Purple (Dark)",
                "appearance_mode": "dark",
                "color_theme": "dark-blue",
                "colors": {
                    "primary": "#9370DB",
                    "secondary": "#B19CD9",
                    "bg": "#1E1E2E",
                    "text": "#FFFFFF",
                    "accent": "#DA70D6"
                }
            },
            "system": {
                "name": "System Mode",
                "appearance_mode": "system",
                "color_theme": "blue",
                "colors": {
                    "primary": "#3B8ED0",
                    "secondary": "#36719F",
                    "bg": None,
                    "text": None,
                    "accent": "#3B8ED0"
                }
            }
        }

def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    
    # Load themes from file
    themes = load_themes()
    
    if theme_name in themes:
        theme_data = themes[theme_name]
        ctk.set_appearance_mode(theme_data["appearance_mode"])
        
        # Map custom color themes to valid built-in themes
        color_theme_map = {
            "pink": "blue",      # Map Rose Gold's pink to blue
            "orange": "blue",    # Map Sunset Orange's orange to blue
        }
        
        # Use the mapped theme if the original is not a valid built-in theme
        color_theme = theme_data["color_theme"]
        if color_theme in color_theme_map:
            color_theme = color_theme_map[color_theme]
            
        ctk.set_default_color_theme(color_theme)
        theme_colors = theme_data["colors"]
    else:
        # Fallback to spotify theme if requested theme not found
        theme_data = themes["spotify"]
        ctk.set_appearance_mode(theme_data["appearance_mode"])
        ctk.set_default_color_theme(theme_data["color_theme"])
        theme_colors = theme_data["colors"]
        current_theme = "spotify"
    
    # Update UI elements with new theme
    update_ui_with_theme(theme_colors)
    
    # Save theme preference
    save_theme_preference(theme_name)
    
    return theme_colors

def update_ui_with_theme(theme_colors):
    # This function will be called after UI elements are created
    if not "tabview" in globals():
        return  # UI not created yet
        
    # Update tab view colors
    tabview.configure(
        segmented_button_fg_color=theme_colors["primary"],
        segmented_button_selected_color=theme_colors["secondary"],
        segmented_button_selected_hover_color=theme_colors["secondary"]
    )
    
    # Update buttons
    if "start_button" in globals() and start_button.winfo_exists():
        if start_button.cget("text") == get_text("status.control_buttons.start"):
            start_button.configure(fg_color="green", hover_color=theme_colors["secondary"])
        # Don't change if it's in STOP state (red)
    
    if "toggle_button" in globals() and toggle_button.winfo_exists():
        if toggle_button.cget("text") == get_text("status.control_buttons.pause"):
            toggle_button.configure(fg_color="orange", hover_color="#ff7b00")
        elif toggle_button.cget("text") == get_text("status.control_buttons.resume"):
            toggle_button.configure(fg_color=theme_colors["primary"], hover_color=theme_colors["secondary"])
    
    if "btn_login" in globals() and btn_login.winfo_exists():
        btn_login.configure(hover_color=theme_colors["secondary"])
    
    if "save_button" in globals() and save_button.winfo_exists():
        save_button.configure(fg_color=theme_colors["primary"], hover_color=theme_colors["secondary"])
        
    if "zar_button" in globals() and zar_button.winfo_exists():
        zar_button.configure(hover_color=theme_colors["secondary"])
    
    # Update status display
    if "status_display_frame" in globals() and status_display_frame.winfo_exists():
        status_display_frame.configure(fg_color=theme_colors["primary"])
        
    # Update progress bars
    if "progress_bar" in globals() and progress_bar.winfo_exists():
        progress_bar.configure(progress_color=theme_colors["primary"])
        
    # Update Option Menus
    if "theme_option_menu" in globals() and theme_option_menu.winfo_exists():
        theme_option_menu.configure(button_color=theme_colors["primary"], 
                                   button_hover_color=theme_colors["secondary"])
                                   
    if "language_option_menu" in globals() and language_option_menu.winfo_exists():
        language_option_menu.configure(button_color=theme_colors["primary"], 
                                      button_hover_color=theme_colors["secondary"])
    
    # Update GitHub link button if it exists
    if "github_button" in globals() and github_button.winfo_exists():
        github_button.configure(fg_color=theme_colors["primary"], 
                               hover_color=theme_colors["secondary"])
    
    # Log message about theme change
    themes = load_themes()
    theme_display_name = get_text(f"themes.{current_theme}")
    log_yaz(get_text("status.log.theme_changed").format(theme=theme_display_name))

def save_theme_preference(theme_name):
    try:
        with open("theme_preference.json", "w") as f:
            json.dump({"theme": theme_name}, f)
    except Exception as e:
        print(f"Error saving theme preference: {e}")

def load_theme_preference():
    try:
        with open("theme_preference.json", "r") as f:
            data = json.load(f)
            return data.get("theme", "spotify")
    except (FileNotFoundError, json.JSONDecodeError):
        return "spotify"  # Default theme

# ---------------- Settings Save/Load ----------------
def save_settings():
    # Make sure entry widgets exist before trying to access them
    if not all(widget in globals() for widget in [
        "entry_user_id", "entry_follow_limit", "entry_min_break", 
        "entry_max_break", "entry_min_follow_time", 
        "entry_max_follow_time", "entry_login_user_id", "entry_password"
    ]):
        print("Cannot save settings: Entry widgets not created yet")
        return
        
    settings = {
        "start_user": entry_user_id.get(),
        "follow_limit": entry_follow_limit.get(),
        "min_break": entry_min_break.get(),
        "max_break": entry_max_break.get(),
        "min_follow_time": entry_min_follow_time.get(),
        "max_follow_time": entry_max_follow_time.get(),
        "login_user_id": entry_login_user_id.get(),
        "password": entry_password.get(),
        "theme": current_theme,
        "language": current_language
    }
    print(f"Saved settings: {settings}")
    with open("settings.json", "w") as f:
        json.dump(settings, f)
    
    # Show confirmation message
    log_yaz(get_text("status.log.settings_saved"))
        
def load_settings():
    # Make sure entry widgets exist before trying to access them
    if not all(widget in globals() for widget in [
        "entry_user_id", "entry_follow_limit", "entry_min_break", 
        "entry_max_break", "entry_min_follow_time", 
        "entry_max_follow_time", "entry_login_user_id", "entry_password"
    ]):
        print("Cannot load settings into widgets: Entry widgets not created yet")
        # Just load theme and language settings
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
            # Set global theme and language variables
            global current_theme, current_language
            current_theme = settings.get("theme", load_theme_preference())
            current_language = settings.get("language", load_language_preference())
            load_language(current_language)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading settings: {e}")
        return
        
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
        print(f"Loaded settings: {settings}")
        entry_user_id.delete(0, "end")
        entry_follow_limit.delete(0, "end")
        entry_min_break.delete(0, "end")
        entry_max_break.delete(0, "end")
        entry_min_follow_time.delete(0, "end")
        entry_max_follow_time.delete(0, "end")
        entry_login_user_id.delete(0, "end")
        entry_password.delete(0, "end")
        
        entry_user_id.insert(0, settings.get("start_user", ""))
        entry_follow_limit.insert(0, settings.get("follow_limit", ""))
        entry_min_break.insert(0, settings.get("min_break", ""))
        entry_max_break.insert(0, settings.get("max_break", ""))
        entry_min_follow_time.insert(0, settings.get("min_follow_time", ""))
        entry_max_follow_time.insert(0, settings.get("max_follow_time", ""))
        entry_login_user_id.insert(0, settings.get("login_user_id", ""))
        entry_password.insert(0, settings.get("password", ""))
        
    except FileNotFoundError:
        print("settings.json file not found.")
    except json.JSONDecodeError:
        print("Could not parse settings.json file.")

# ---------------- Helper Functions ----------------
def log_yaz(mesaj):
    # Use after method to update GUI from a non-main thread
    if "root" in globals() and root.winfo_exists():
        root.after(0, lambda: _update_log(mesaj))
    
def _update_log(mesaj):
    if "text_log" in globals() and text_log.winfo_exists():
        text_log.configure(state="normal")
        text_log.insert("end", mesaj + "\n")
        text_log.see("end")
        text_log.configure(state="disabled")

def save_start_user(start_user):
    with open("start_user.txt", "w") as file:
        file.write(start_user)

def load_start_user():
    try:
        with open("start_user.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def rastgele_kullanici_getir():
    users = load_followed_users()
    if not users:
        messagebox.showinfo(get_text("status.messages.no_users"), 
                           get_text("status.messages.no_users_message"))
        return None
    rastgele_url = random.choice(users)
    try:
        kullanici_id = rastgele_url.split("/user/")[1].split("?")[0]
        # Update entry in settings tab
        entry_user_id.delete(0, "end")
        entry_user_id.insert(0, kullanici_id)
        log_yaz(get_text("status.log.random_user").format(user=kullanici_id))
        return kullanici_id
    except IndexError:
        messagebox.showerror(get_text("status.messages.user_id_error"), 
                            get_text("status.messages.user_id_error_message"))
        return None

def open_github_link():
    """Open the GitHub profile link in the default web browser"""
    github_url = get_text("producer.github_url")
    webbrowser.open(github_url)
    log_yaz(f"Opening GitHub profile: {github_url}")

def update_ui_language():
    """Update all UI elements with current language"""
    if not "root" in globals() or not root.winfo_exists():
        return  # UI not created yet or destroyed
    
    # Update window title
    root.title(get_text("app.title"))
    
    # Update tab names - FIXED to ensure navigation remains functional
    if "tabview" in globals() and tabview.winfo_exists():
        # Get current tab
        current_tab = tabview._segmented_button.get()
        
        # Get the list of current tab names directly from the button *before* changing them
        original_tab_names = tabview._segmented_button.cget("values")
        try:
            # Find index based on current text
            current_tab_index = original_tab_names.index(current_tab)
        except ValueError:
            # If text somehow doesn't match, default to first tab
            current_tab_index = 0

        # Get new translated names
        new_tab_names = [
            get_text("app.tabs.status"),
            get_text("app.tabs.settings"),
            get_text("app.tabs.producer")
        ]
        
        # Create a mapping from old tab names to tab frames
        tab_frames = {}
        for old_name in original_tab_names:
            if old_name in tabview._tab_dict:
                tab_frames[old_name] = tabview._tab_dict[old_name]
        
        # Clear the tab dictionary and rebuild it with new names
        tabview._tab_dict = {}
        for i, (old_name, new_name) in enumerate(zip(original_tab_names, new_tab_names)):
            if old_name in tab_frames:
                tabview._tab_dict[new_name] = tab_frames[old_name]
        
        # Update the button values
        tabview._segmented_button.configure(values=new_tab_names)
        
        # Update the internal name list that CTkTabview uses for mapping clicks to tabs
        if hasattr(tabview, "_name_list"):
            tabview._name_list = new_tab_names
        
        # Set the button to the new name at the same index to visually select it
        new_selected_tab_name = new_tab_names[current_tab_index]
        tabview._segmented_button.set(new_selected_tab_name)
    # Update status tab elements
    if "status_title" in globals() and status_title.winfo_exists():
        status_title.configure(text=get_text("status.total_accounts_followed"))
    
    if "label_giris_durumu" in globals() and label_giris_durumu.winfo_exists():
        current_text = label_giris_durumu.cget("text")
        if current_text == "Logged In" or current_text == "Giriş Yapıldı":
            label_giris_durumu.configure(text=get_text("status.login_status.logged_in"))
        else:
            label_giris_durumu.configure(text=get_text("status.login_status.not_logged_in"))
    
    if "btn_login" in globals() and btn_login.winfo_exists():
        btn_login.configure(text=get_text("status.login_button"))
    
    if "label_current_user" in globals() and label_current_user.winfo_exists():
        current_text = label_current_user.cget("text")
        if current_text == get_text("status.current_user") or current_text.startswith("Current User: ") or current_text.startswith("Mevcut Kullanıcı: "):
            label_current_user.configure(text=get_text("status.current_user"))
        else:
            # Extract user info and update with new prefix
            user_info = current_text.split(": ", 1)[1] if ": " in current_text else ""
            label_current_user.configure(text=f"{get_text('status.current_user')}{user_info}")
    
    # Update control buttons
    if "start_button" in globals() and start_button.winfo_exists():
        current_text = start_button.cget("text")
        if current_text == "Start" or current_text == "Başlat":
            start_button.configure(text=get_text("status.control_buttons.start"))
        else:
            start_button.configure(text=get_text("status.control_buttons.stop"))
    
    if "toggle_button" in globals() and toggle_button.winfo_exists():
        current_text = toggle_button.cget("text")
        if current_text == "Pause" or current_text == "Duraklat":
            toggle_button.configure(text=get_text("status.control_buttons.pause"))
        else:
            toggle_button.configure(text=get_text("status.control_buttons.resume"))
    
    # Update progress labels
    if "label_takip" in globals() and label_takip.winfo_exists():
        current_text = label_takip.cget("text")
        if current_text.startswith("Followed: ") or current_text.startswith("Takip Edildi: "):
            count = current_text.split(": ")[1]
            label_takip.configure(text=get_text("status.progress.followed").format(count=count))
        else: # Initial state
            label_takip.configure(text=get_text("status.progress.followed").format(count="0"))
    
    if "label_süre" in globals() and label_süre.winfo_exists():
        current_text = label_süre.cget("text")
        if current_text.startswith("Running Time: ") or current_text.startswith("Çalışma Süresi: "):
            time_val = current_text.split(": ")[1]
            label_süre.configure(text=get_text("status.progress.running_time").format(time=time_val))
        else: # Initial state
            label_süre.configure(text=get_text("status.progress.running_time").format(time="0 min 0 sec"))
    
    if "break_label" in globals() and break_label.winfo_exists():
        current_text = break_label.cget("text")
        if current_text.startswith("Break: ") or current_text.startswith("Mola: "):
            parts = current_text.split(": ")[-1].split(" ")
            min_val = parts[0]
            sec_val = parts[2]
            break_label.configure(text=get_text("status.progress.break_time").format(min=min_val, sec=sec_val))
        else: # Initial state
            break_label.configure(text=get_text("status.progress.break_time").format(min="0", sec="0"))

    # Update log area
    if "log_label" in globals() and log_label.winfo_exists():
        log_label.configure(text=get_text("status.log.title"))
    
    # Update settings tab
    if "settings_title" in globals() and settings_title.winfo_exists():
        settings_title.configure(text=get_text("settings.title"))
    
    # Update appearance settings section
    if "appearance_title" in globals() and appearance_title.winfo_exists():
        appearance_title.configure(text=get_text("settings.appearance.title"))
    
    if "settings_theme_label" in globals() and settings_theme_label.winfo_exists():
        settings_theme_label.configure(text=get_text("settings.appearance.theme"))
    
    if "language_label" in globals() and language_label.winfo_exists():
        language_label.configure(text=get_text("settings.appearance.language"))
    
    # Update field labels
    if "field_labels" in globals():
        for idx, label_widget in enumerate(field_labels):
            if label_widget.winfo_exists():
                field_key = list(get_text("settings.fields").keys())[idx]
                label_widget.configure(text=get_text(f"settings.fields.{field_key}"))
    
    # Update random user button text (if it changes)
    if "zar_button" in globals() and zar_button.winfo_exists():
        zar_button.configure(text=get_text("settings.random_user_button"))
        
    # Update save button
    if "save_button" in globals() and save_button.winfo_exists():
        save_button.configure(text=get_text("settings.save_button"))
    
    # Update producer tab
    if "producer_title" in globals() and producer_title.winfo_exists():
        producer_title.configure(text=get_text("producer.title"))
    
    if "producer_description" in globals() and producer_description.winfo_exists():
        producer_description.configure(text=get_text("producer.description"))
    
    if "producer_name" in globals() and producer_name.winfo_exists():
        producer_name.configure(text=get_text("producer.name"))
    
    if "github_button" in globals() and github_button.winfo_exists():
        github_button.configure(text=get_text("producer.github_link"))
    
    # Update theme option menu values with translated theme names
    if "theme_option_menu" in globals() and theme_option_menu.winfo_exists() and "themes" in globals():
        # Get translated theme names
        translated_theme_names = []
        theme_keys = list(themes.keys())
        
        for theme_key in theme_keys:
            translated_name = get_text(f"themes.{theme_key}")
            translated_theme_names.append(translated_name)
        
        # Update option menu with translated names
        theme_option_menu.configure(values=translated_theme_names)
        
        # Set current theme with translated name
        current_translated_name = get_text(f"themes.{current_theme}")
        theme_option_menu.set(current_translated_name)
    
    # Log language change
    log_yaz(f"🌐 Language changed to: {current_language}")

# ---------------- Status Update Functions ----------------
def update_status_display():
    # Update the status display with current information
    global followed_count_total
    
    # Get total followed count from database
    followed_count_total = get_total_followed_count()
    
    # Update the status display
    if "total_followed_label" in globals() and total_followed_label.winfo_exists():
        total_followed_label.configure(text=f"{followed_count_total}")
    
    # Update current user display
    if driver is not None and current_user:
        # Try to get the current user's name
        try:
            driver.get(f"https://open.spotify.com/user/{current_user}")
            time.sleep(2)
            isim = kullanici_ismi_getir()
            if isim and isim.lower() != "your library":
                label_current_user.configure(text=f"{get_text('status.current_user')}{isim}({current_user})")
            else:
                # If name is "your library" or None, just show the ID
                label_current_user.configure(text=f"{get_text('status.current_user')}{current_user}")
        except:
            pass

def update_runtime_display():
    global start_time
    if "start_time" in globals() and not is_stopped and "root" in globals() and root.winfo_exists():
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)
        
        if hours > 0:
            time_str = f"{hours}h {mins}m {secs}s"
        else:
            time_str = f"{mins}m {secs}s"
            
        if "label_süre" in globals() and label_süre.winfo_exists():
            label_süre.configure(text=get_text("status.progress.running_time").format(time=time_str))
        
        # Schedule next update
        root.after(1000, update_runtime_display)

# ---------------- WebDriver and Login ----------------
def giriş_yapıldı():
    global driver, login_user_id
    try:
        # Get login user ID and password from settings tab
        login_user_id = entry_login_user_id.get().strip()
        password = entry_password.get()
        
        if not login_user_id:
            messagebox.showwarning(get_text("status.messages.missing_login_id"), 
                                  get_text("status.messages.missing_login_id_message"))
            return
            
        if not password:
            messagebox.showwarning(get_text("status.messages.missing_info"), 
                                  get_text("settings.fields.password"))
            return
        
        driver = webdriver.Chrome()
        driver.maximize_window()
        
        # Construct login URL using the provided login_user_id
        login_url = f"https://accounts.spotify.com/tr/login?login_hint={login_user_id}&allow_password=1&continue=https%3A%2F%2Faccounts.spotify.com%2Ftr%2Fstatus"
        driver.get(login_url)
     
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login-password"))).send_keys(password)

        messagebox.showinfo(get_text("status.messages.login_success"), 
                           get_text("status.messages.login_success_message"))
        if "root" in globals() and root.winfo_exists():
            root.after(0, lambda: label_giris_durumu.configure(
                text=get_text("status.login_status.logged_in"), text_color="green"))
            root.after(0, lambda: toggle_button.configure(state="normal"))
            root.after(0, lambda: btn_login.configure(state="disabled"))

        # Update followers after login
        güncelle_takip_edilenler()
        
        # Update status display
        update_status_display()

    except Exception as e:
        messagebox.showerror(get_text("status.messages.login_error"), 
                            get_text("status.messages.login_error_message").format(error=str(e)))

def güncelle_takip_edilenler():
    global login_user_id
    # Save followed users to database
    if not login_user_id:
        print("Cannot update followers: Login User ID is missing.")
        return
        
    driver.get(f"https://open.spotify.com/user/{login_user_id}/following")
    time.sleep(5)

    # Scroll to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get followed users
    raw_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/user/')]")
    user_links = []
    for elem in raw_elements:
        try:
            text = elem.text.strip()
            href = elem.get_attribute('href')
        except Exception:
            continue
        if text and href:
            user_links.append((text, href))

    # Update database
    followed_users = load_followed_users()
    for _, user_profile_url in user_links:
        if user_profile_url not in followed_users:
            save_followed_user(user_profile_url)
            log_yaz(get_text("status.log.new_followed_saved").format(url=user_profile_url))
    
    # Update status display
    update_status_display()

# ---------------- Bot Functions ----------------
def toggle_bot():
    global is_paused
    
    if toggle_button.cget("text") == get_text("status.control_buttons.pause"):
        is_paused = True
        toggle_button.configure(text=get_text("status.control_buttons.resume"), 
                               fg_color=apply_theme(current_theme)["primary"])
        log_yaz(get_text("status.log.bot_paused"))
    else:
        is_paused = False
        toggle_button.configure(text=get_text("status.control_buttons.pause"), fg_color="orange")
        log_yaz(get_text("status.log.bot_resumed"))

def start_bot():
    global is_stopped, is_paused, current_user, start_time

    # Check if logged in
    if label_giris_durumu.cget("text") != get_text("status.login_status.logged_in"):
        messagebox.showwarning(get_text("status.messages.login_required"), 
                              get_text("status.messages.login_required_message"))
        return

    if start_button.cget("text") == get_text("status.control_buttons.stop"):
        is_stopped = True
        start_button.configure(text=get_text("status.control_buttons.start"), fg_color="green")
        toggle_button.configure(state="disabled")
        log_yaz(get_text("status.log.bot_stopped"))
        progress_bar.set(0)
        label_süre.configure(text=get_text("status.progress.running_time").format(time="0 min 0 sec"))
        label_takip.configure(text=get_text("status.progress.followed").format(count="0"))
        label_current_user.configure(text=get_text("status.current_user"))
        return

    # Get values without switching tabs
    start_user = entry_user_id.get().strip()
    if not start_user:
        start_user = load_start_user()
        if not start_user:
            messagebox.showwarning(get_text("status.messages.missing_info"), 
                                  get_text("status.messages.missing_info_message"))
            return
        entry_user_id.insert(0, start_user)

    try:
        follow_limit = int(entry_follow_limit.get())
        min_break = int(entry_min_break.get())
        max_break = int(entry_max_break.get())
        min_follow_time = int(entry_min_follow_time.get())
        max_follow_time = int(entry_max_follow_time.get())
    except ValueError:
        messagebox.showwarning(get_text("status.messages.invalid_numbers"), 
                              get_text("status.messages.invalid_numbers_message"))
        return
    
    save_settings()
    save_start_user(start_user)
    is_stopped = False
    is_paused = False
    current_user = start_user
    start_time = time.time()

    progress_bar.set(0)

    threading.Thread(
        target=run_bot,
        args=(follow_limit, min_break, max_break, min_follow_time, max_follow_time),
        daemon=True
    ).start()

    start_button.configure(text=get_text("status.control_buttons.stop"), fg_color="red")
    toggle_button.configure(state="normal", text=get_text("status.control_buttons.pause"), fg_color="orange")
    
    # Get user name and update display with Name(ID) format
    driver.get(f"https://open.spotify.com/user/{current_user}")
    time.sleep(2)
    isim = kullanici_ismi_getir()
    if isim and isim.lower() != "your library":
        label_current_user.configure(text=f"{get_text('status.current_user')}{isim}({current_user})")
    else:
        label_current_user.configure(text=f"{get_text('status.current_user')}{current_user}")
    
    # Start runtime display update
    update_runtime_display()

def kullanici_ismi_getir():
    try:
        # Updated to match the specific HTML element described by the user
        h1_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[@data-encore-id='text']")
            )
        )
        name = h1_element.text.strip()
        # Check if the name is "Your Library" and return None in that case
        if name.lower() == "your library":
            return None
        return name
    except Exception:
        return None

def is_private_profile(user_profile_url):
    try:
        driver.get(user_profile_url)
        time.sleep(3)
        
        # Check if the follow button exists
        try:
            follow_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Takip Et')]"))
            )
            return False  # Not private if follow button exists
        except:
            return True  # Private if no follow button
    except:
        return True  # Assume private on any error
        
def mola_gerisayim(dakika):
    global is_stopped
    
    # Show break progress bar and label
    if "break_progress" in globals() and break_progress.winfo_exists():
        break_progress.pack(pady=5, padx=10)
    if "break_label" in globals() and break_label.winfo_exists():
        break_label.pack(pady=5, anchor="w", padx=10)
    
    toplam_saniye = dakika * 60
    for kalan_saniye in range(toplam_saniye, 0, -1):
        if is_stopped:
            break
            
        # Calculate remaining minutes and seconds
        kalan_dakika, kalan_sn = divmod(kalan_saniye, 60)
        
        # Update progress bar and label
        oran = kalan_saniye / toplam_saniye
        if "root" in globals() and root.winfo_exists():
            root.after(0, lambda o=oran: break_progress.set(o) if "break_progress" in globals() and break_progress.winfo_exists() else None)
            root.after(0, lambda m=kalan_dakika, s=kalan_sn: 
                      break_label.configure(text=get_text("status.progress.break_time").format(min=m, sec=s)) if "break_label" in globals() and break_label.winfo_exists() else None)
        
        time.sleep(1)
    
    # Hide break progress bar and label when done
    if "root" in globals() and root.winfo_exists():
        root.after(0, lambda: break_progress.pack_forget() if "break_progress" in globals() and break_progress.winfo_exists() else None)
        root.after(0, lambda: break_label.pack_forget() if "break_label" in globals() and break_label.winfo_exists() else None)

def run_bot(follow_limit, min_break, max_break, min_follow_time, max_follow_time):
    global is_stopped, is_paused, current_user, followed_count_total

    followed_count = 0
    followed_users = load_followed_users()

    gizli_profil_sayaci = 0  # Counter for private profiles
    
    # New variables for stuck detection
    last_user = None
    stuck_count = 0
    max_stuck_count = 2  # After this many repetitions, consider the bot stuck

    while not is_stopped:
        # Check if paused
        while is_paused and not is_stopped:
            time.sleep(1)
            
        if is_stopped:
            break
        
        # Check if we're stuck in a loop with the same user
        if current_user == last_user:
            stuck_count += 1
            if stuck_count >= max_stuck_count:
                log_yaz(f"🛑 Bot tamamen durduruldu. Yeni ayarlar için hazır!")
                log_yaz(f"🔵 '{current_user}' {len(followed_users)} kişiyi takip ediyor.")
                
                # Use random selection to break the loop
                yeni_kullanici = rastgele_kullanici_getir()
                if yeni_kullanici:
                    current_user = yeni_kullanici
                    save_start_user(current_user)
                    stuck_count = 0
                    continue
                else:
                    # If no random user available, stop the bot
                    is_stopped = True
                    if "root" in globals() and root.winfo_exists():
                        root.after(0, lambda: start_button.configure(text=get_text("status.control_buttons.start"), fg_color="green") if "start_button" in globals() and start_button.winfo_exists() else None)
                        root.after(0, lambda: toggle_button.configure(state="disabled") if "toggle_button" in globals() and toggle_button.winfo_exists() else None)
                    break
        else:
            stuck_count = 0
            last_user = current_user
        
        # 1) Go to user's profile
        driver.get(f"https://open.spotify.com/user/{current_user}")
        time.sleep(3)
        
        # 2) Get user's name
        isim = kullanici_ismi_getir()
        
        # 3) Go to user's following page
        driver.get(f"https://open.spotify.com/user/{current_user}/following")
        time.sleep(5)
        
        # 4) Scroll to the bottom of the page
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 5) Get followed users
        raw_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/user/')]")
        user_links = []
        for elem in raw_elements:
            try:
                text = elem.text.strip()
                href = elem.get_attribute('href')
            except Exception:
                continue
            if text and href:
                user_links.append((text, href))
        
        # Log how many users this person follows
        if isim:
            log_yaz(get_text("status.log.user_follows").format(user=f"{isim}({current_user})", count=len(user_links)))
        else:
            log_yaz(get_text("status.log.user_follows").format(user=current_user, count=len(user_links)))
        
        # If user doesn't follow anyone, pick a random user
        if not user_links:
            log_yaz(get_text("status.log.no_followers").format(user=current_user))
            yeni_kullanici = rastgele_kullanici_getir()
            if yeni_kullanici:
                current_user = yeni_kullanici
                save_start_user(current_user)
                continue
            else:
                log_yaz(get_text("status.log.no_random_user"))
                is_stopped = True
                if "root" in globals() and root.winfo_exists():
                    root.after(0, lambda: start_button.configure(text=get_text("status.control_buttons.start"), fg_color="green") if "start_button" in globals() and start_button.winfo_exists() else None)
                    root.after(0, lambda: toggle_button.configure(state="disabled") if "toggle_button" in globals() and toggle_button.winfo_exists() else None)
                break
        
        # Track if all users were already followed
        all_already_followed = True
        
        # Follow users
        for i, (user_name, user_profile_url) in enumerate(user_links):
            if is_stopped or is_paused:
                break
                
            # Update progress bar
            progress = (i + 1) / len(user_links)
            if "root" in globals() and root.winfo_exists():
                root.after(0, lambda p=progress: progress_bar.set(p) if "progress_bar" in globals() and progress_bar.winfo_exists() else None)
            
            # Skip if already followed
            if user_profile_url in followed_users:
                log_yaz(get_text("status.log.already_followed").format(user=user_name))
                continue
                
            all_already_followed = False
            
            # Check if private profile
            if is_private_profile(user_profile_url):
                log_yaz(get_text("status.log.private_profile").format(user=user_name))
                gizli_profil_sayaci += 1
                
                # If too many private profiles in a row, switch to a random user
                if gizli_profil_sayaci >= 5:
                    log_yaz(get_text("status.log.private_profiles_limit"))
                    gizli_profil_sayaci = 0
                    yeni_kullanici = rastgele_kullanici_getir()
                    if yeni_kullanici:
                        current_user = yeni_kullanici
                        save_start_user(current_user)
                        break
                continue
            
            # Reset private profile counter
            gizli_profil_sayaci = 0
            
            # Try to follow user
            try:
                # Find and click follow button
                follow_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Takip Et')]"))
                )
                follow_button.click()
                time.sleep(1)
                
                # Save to database
                save_followed_user(user_profile_url)
                followed_count += 1
                followed_count_total += 1
                
                # Update UI
                log_yaz(get_text("status.log.user_followed").format(user=user_name))
                if "root" in globals() and root.winfo_exists():
                    root.after(0, lambda count=followed_count: label_takip.configure(text=get_text("status.progress.followed").format(count=count)) if "label_takip" in globals() and label_takip.winfo_exists() else None)
                    root.after(0, lambda count=followed_count_total: total_followed_label.configure(text=f"{count}") if "total_followed_label" in globals() and total_followed_label.winfo_exists() else None)
            except Exception:
                log_yaz(get_text("status.log.follow_failed").format(user=user_name))

            if followed_count >= follow_limit:
                break

            sleep_time = random.randint(min_follow_time, max_follow_time)
            log_yaz(get_text("status.log.waiting").format(seconds=sleep_time))
            time.sleep(sleep_time)

        # If all users were already followed, pick a random user to break potential loop
        if all_already_followed:
            log_yaz("⚠️ All users are already followed. Selecting a random user to avoid loops.")
            yeni_kullanici = rastgele_kullanici_getir()
            if yeni_kullanici:
                current_user = yeni_kullanici
                save_start_user(current_user)
                continue
            
        # 6) Take a break when limit is reached
        if followed_count >= follow_limit:
            mola = random.randint(min_break, max_break)
            log_yaz(get_text("status.log.taking_break").format(minutes=mola))
            mola_gerisayim(mola)
            followed_count = 0
            if "root" in globals() and root.winfo_exists():
                root.after(0, lambda: progress_bar.set(0) if "progress_bar" in globals() and progress_bar.winfo_exists() else None)

        # 7) Move to the next user
        if user_links:
            try:
                next_user = user_links[-1][1].split("/user/")[1].split("?")[0]
                current_user = next_user
                save_start_user(current_user)
                
                # Get the user's name for the new user
                driver.get(f"https://open.spotify.com/user/{current_user}")
                time.sleep(2)
                isim = kullanici_ismi_getir()
                
                if "root" in globals() and root.winfo_exists():
                    if isim and isim.lower() != "your library":
                        log_yaz(get_text("status.log.moved_to_user").format(user=f"{isim}({current_user})"))
                        root.after(0, lambda: label_current_user.configure(
                            text=f"{get_text('status.current_user')}{isim}({current_user})") if "label_current_user" in globals() and label_current_user.winfo_exists() else None)
                    else:
                        log_yaz(get_text("status.log.moved_to_user").format(user=current_user))
                        root.after(0, lambda: label_current_user.configure(
                            text=f"{get_text('status.current_user')}{current_user}") if "label_current_user" in globals() and label_current_user.winfo_exists() else None)
            except Exception as e:
                log_yaz(get_text("status.log.error_moving").format(error=str(e)))
                yeni_kullanici = rastgele_kullanici_getir()
                if yeni_kullanici:
                    current_user = yeni_kullanici
                    save_start_user(current_user)

    # If stopped, reset UI
    if "root" in globals() and root.winfo_exists():
        root.after(0, lambda: start_button.configure(text=get_text("status.control_buttons.start"), fg_color="green") if "start_button" in globals() and start_button.winfo_exists() else None)
        root.after(0, lambda: toggle_button.configure(state="disabled") if "toggle_button" in globals() and toggle_button.winfo_exists() else None)
        root.after(0, lambda: progress_bar.set(0) if "progress_bar" in globals() and progress_bar.winfo_exists() else None)

# ---------------- Tray Icon ----------------
def create_image():
    # Create a simple green square icon
    width = 64
    height = 64
    color1 = "#1DB954"  # Spotify green
    
    image = Image.new("RGB", (width, height), color1)
    dc = ImageDraw.Draw(image)
    
    return image

def on_quit():
    global is_stopped
    is_stopped = True
    if driver:
        try:
            driver.quit()
        except:
            pass
    if "root" in globals() and root.winfo_exists():
        root.destroy()

def start_tray_icon():
    # Create tray icon
    icon = pystray.Icon("Spotify Bot", create_image(), menu=(
        item("Exit", on_quit),
    ))
    # Run the app
    icon.run()

# Main application
def run_gui():
    global root, text_log, entry_user_id, entry_follow_limit, entry_min_break, entry_max_break
    global entry_min_follow_time, entry_max_follow_time, entry_login_user_id, entry_password, label_giris_durumu
    global label_süre, label_takip, label_current_user, progress_bar, break_progress
    global break_label, start_button, toggle_button, btn_login, tabview
    global status_tab, settings_tab, producer_tab, status_frame, control_frame, progress_frame, log_frame
    global settings_frame, fields_frame, status_display_frame, total_followed_label
    global save_button, themes, field_labels, zar_button
    global appearance_title, settings_theme_label, language_label, language_option_menu, theme_option_menu
    global producer_title, producer_description, producer_name, github_button
    
    # Initialize database at startup
    create_db()
    
    # Load language preference
    language_name = load_language_preference()
    load_language(language_name)
    
    # Load theme preference
    theme_name = load_theme_preference()
    
    # Load themes
    themes = load_themes()
    
    # Load settings (just theme and language before GUI creation)
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
        # Set global theme and language variables
        global current_theme, current_language
        current_theme = settings.get("theme", theme_name)
        current_language = settings.get("language", language_name)
        load_language(current_language)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
    
    # GUI Setup - Apply initial theme
    theme_colors = apply_theme(current_theme)
    
    root = ctk.CTk()
    
    # Try to load Spotify icon
    try:
        root.iconbitmap("resimler/2.ico")
    except:
        pass  # Continue without icon if not found
    
    root.title(get_text("app.title"))
    root.geometry("500x750") # Adjusted height after removing theme buttons from status
    
    # Create tabview with improved styling
    tabview = ctk.CTkTabview(root, width=680, height=750, 
                            segmented_button_fg_color=theme_colors["primary"],
                            segmented_button_selected_color=theme_colors["secondary"],
                            segmented_button_selected_hover_color=theme_colors["secondary"])
    tabview.pack(padx=10, pady=10, fill="both", expand=True)
    

    
    # Create tabs
    status_tab = tabview.add(get_text("app.tabs.status"))
    settings_tab = tabview.add(get_text("app.tabs.settings"))
    producer_tab = tabview.add(get_text("app.tabs.producer"))
    
    # Store original tab names for reference during language changes
    tabview._original_tab_names = [
        get_text("app.tabs.status"),
        get_text("app.tabs.settings"),
        get_text("app.tabs.producer")
    ]
    
    # Store initial tab dictionary mapping for reference
    tabview._original_tab_dict = tabview._tab_dict.copy()
    
    # =============== STATUS TAB ===============
    # New prominent status display
    status_display_frame = ctk.CTkFrame(status_tab, corner_radius=15, 
                                       fg_color=theme_colors["primary"], 
                                       height=100)
    status_display_frame.pack(pady=10, padx=10, fill="x")
    
    # Total followed accounts display
    followed_count_total = get_total_followed_count()
    
    status_title = ctk.CTkLabel(status_display_frame, 
                               text=get_text("status.total_accounts_followed"), 
                               font=("Arial", 14, "bold"),
                               text_color="white")
    status_title.pack(pady=(10, 0))
    
    total_followed_label = ctk.CTkLabel(status_display_frame, 
                                       text=f"{followed_count_total}", 
                                       font=("Arial", 36, "bold"),
                                       text_color="white")
    total_followed_label.pack(pady=(0, 10))
    
    # Status information frame
    status_frame = ctk.CTkFrame(status_tab, corner_radius=10)
    status_frame.pack(pady=10, padx=10, fill="x")
    
    # Login status and button
    login_frame = ctk.CTkFrame(status_frame, corner_radius=10)
    login_frame.pack(pady=5, padx=10, fill="x")
    
    label_giris_durumu = ctk.CTkLabel(login_frame, text=get_text("status.login_status.not_logged_in"), 
                                     text_color="red", font=("Arial", 14, "bold"))
    label_giris_durumu.pack(side="left", padx=10)
    
    btn_login = ctk.CTkButton(login_frame, text=get_text("status.login_button"), 
                             command=giriş_yapıldı, width=150,
                             font=("Arial", 12, "bold"), hover_color=theme_colors["secondary"])
    btn_login.pack(side="right", padx=10)
    
    # Current user info
    label_current_user = ctk.CTkLabel(status_frame, text=get_text("status.current_user"), 
                                     anchor="w", font=("Arial", 14))
    label_current_user.pack(pady=5, padx=10, fill="x")
    
    # Control buttons frame
    control_frame = ctk.CTkFrame(status_tab, corner_radius=10)
    control_frame.pack(pady=10, padx=10, fill="x")
    
    # Control buttons
    button_frame = ctk.CTkFrame(control_frame)
    button_frame.pack(pady=10, padx=10, fill="x")
    
    start_button = ctk.CTkButton(button_frame, text=get_text("status.control_buttons.start"), 
                                command=start_bot, width=150, 
                                fg_color="green", hover_color=theme_colors["secondary"],
                                font=("Arial", 14, "bold"))
    start_button.pack(side="left", padx=10)
    
    toggle_button = ctk.CTkButton(button_frame, text=get_text("status.control_buttons.pause"), 
                                 command=toggle_bot, width=150, 
                                 fg_color="orange", hover_color="#ff7b00",
                                 font=("Arial", 14, "bold"), state="disabled")
    toggle_button.pack(side="right", padx=10)
    
    # Progress frame
    progress_frame = ctk.CTkFrame(status_tab, corner_radius=10)
    progress_frame.pack(pady=10, padx=10, fill="x")
    
    # Progress bar
    progress_bar = ctk.CTkProgressBar(progress_frame, progress_color=theme_colors["primary"])
    progress_bar.pack(pady=10, padx=10, fill="x")
    progress_bar.set(0)
    
    # Break progress bar (initially hidden)
    break_progress = ctk.CTkProgressBar(progress_frame, progress_color="orange")
    break_progress.set(0)
    
    # Progress labels
    label_takip = ctk.CTkLabel(progress_frame, text=get_text("status.progress.followed").format(count="0"), 
                              anchor="w", font=("Arial", 12))
    label_takip.pack(pady=5, anchor="w", padx=10)
    
    label_süre = ctk.CTkLabel(progress_frame, text=get_text("status.progress.running_time").format(time="0 min 0 sec"), 
                             anchor="w", font=("Arial", 12))
    label_süre.pack(pady=5, anchor="w", padx=10)
    
    # Break label (initially hidden)
    break_label = ctk.CTkLabel(progress_frame, text=get_text("status.progress.break_time").format(min="0", sec="0"), 
                              anchor="w", font=("Arial", 12))
    
    # Log frame
    log_frame = ctk.CTkFrame(status_tab, corner_radius=10)
    log_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    log_label = ctk.CTkLabel(log_frame, text=get_text("status.log.title"), 
                            font=("Arial", 14, "bold"))
    log_label.pack(pady=5)
    
    text_log = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, 
                                        font=("Consolas", 10))
    text_log.pack(pady=5, padx=10, fill="both", expand=True)
    text_log.configure(state="disabled")
    
    # =============== SETTINGS TAB ===============
    settings_frame = ctk.CTkFrame(settings_tab, corner_radius=10)
    settings_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    settings_title = ctk.CTkLabel(settings_frame, text=get_text("settings.title"), 
                                 font=("Arial", 18, "bold"))
    settings_title.pack(pady=10)
    
    # Appearance settings
    appearance_frame = ctk.CTkFrame(settings_frame, corner_radius=10)
    appearance_frame.pack(pady=10, padx=10, fill="x")
    
    appearance_title = ctk.CTkLabel(appearance_frame, text=get_text("settings.appearance.title"), 
                                   font=("Arial", 14, "bold"))
    appearance_title.pack(pady=5)
    
    # Theme selection
    theme_frame = ctk.CTkFrame(appearance_frame)
    theme_frame.pack(pady=5, padx=10, fill="x")
    
    settings_theme_label = ctk.CTkLabel(theme_frame, text=get_text("settings.appearance.theme"), 
                                       width=150, anchor="w")
    settings_theme_label.pack(side="left", padx=10)
    
    # Get translated theme names
    translated_theme_names = []
    theme_keys = list(themes.keys())
    
    for theme_key in theme_keys:
        translated_name = get_text(f"themes.{theme_key}")
        translated_theme_names.append(translated_name)
    
    def on_theme_change(choice):
        # Find the theme key from the translated display name
        for i, translated_name in enumerate(translated_theme_names):
            if translated_name == choice:
                theme_key = theme_keys[i]
                apply_theme(theme_key)
                break
    
    theme_option_menu = ctk.CTkOptionMenu(theme_frame, values=translated_theme_names, 
                                         command=on_theme_change,
                                         width=200,
                                         button_color=theme_colors["primary"],
                                         button_hover_color=theme_colors["secondary"])
    theme_option_menu.pack(side="right", padx=10)
    
    # Set initial theme selection with translated name
    current_translated_name = get_text(f"themes.{current_theme}")
    theme_option_menu.set(current_translated_name)
    
    # Language selection
    language_frame = ctk.CTkFrame(appearance_frame)
    language_frame.pack(pady=5, padx=10, fill="x")
    
    language_label = ctk.CTkLabel(language_frame, text=get_text("settings.appearance.language"), 
                                 width=150, anchor="w")
    language_label.pack(side="left", padx=10)
    
    available_languages = get_available_languages()
    
    def on_language_change(choice):
        load_language(choice)
    
    language_option_menu = ctk.CTkOptionMenu(language_frame, values=available_languages, 
                                            command=on_language_change,
                                            width=200,
                                            button_color=theme_colors["primary"],
                                            button_hover_color=theme_colors["secondary"])
    language_option_menu.pack(side="right", padx=10)
    
    # Set initial language selection
    language_option_menu.set(current_language)
    
    # Bot settings fields
    fields_frame = ctk.CTkFrame(settings_frame, corner_radius=10)
    fields_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Create fields dynamically
    field_keys = list(get_text("settings.fields").keys())
    field_labels = []
    
    # User ID field with random button - Modified for better visibility on small screens
    user_id_frame = ctk.CTkFrame(fields_frame)
    user_id_frame.pack(pady=5, padx=10, fill="x")
    
    user_id_label = ctk.CTkLabel(user_id_frame, 
                                text=get_text("settings.fields.user_id"), 
                                width=250, anchor="w")
    user_id_label.pack(side="left", padx=10)
    field_labels.append(user_id_label)
    
    # Create a container frame for entry and dice button
    entry_dice_frame = ctk.CTkFrame(user_id_frame, fg_color="transparent")
    entry_dice_frame.pack(side="right", padx=10, fill="x", expand=True)
    
    entry_user_id = ctk.CTkEntry(entry_dice_frame)
    entry_user_id.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    zar_button = ctk.CTkButton(entry_dice_frame, text=get_text("settings.random_user_button"), 
                              command=rastgele_kullanici_getir, width=40,
                              hover_color=theme_colors["secondary"])
    zar_button.pack(side="right")
         # Other fields
    for i, key in enumerate(field_keys[1:], 1):  # Skip user_id as it's already added
        frame = ctk.CTkFrame(fields_frame)
        frame.pack(pady=5, padx=10, fill="x")
        
        label = ctk.CTkLabel(frame, text=get_text(f"settings.fields.{key}"), 
                            width=250, anchor="w")
        label.pack(side="left", padx=10)
        field_labels.append(label)
        
        # Use password entry with show="*" for password field
        if key == "password":
            entry = ctk.CTkEntry(frame, width=200, show="*")
        else:
            entry = ctk.CTkEntry(frame, width=200)
        entry.pack(side="right", padx=10)
        
        # Store entry widget in global variable
        globals()[f"entry_{key}"] = entry
    
    # Save button
    save_button = ctk.CTkButton(settings_frame, text=get_text("settings.save_button"), 
                               command=save_settings, width=200,
                               fg_color=theme_colors["primary"],
                               hover_color=theme_colors["secondary"],
                               font=("Arial", 14, "bold"))
    save_button.pack(pady=20)
    
    # =============== PRODUCER TAB ===============
    producer_frame = ctk.CTkFrame(producer_tab, corner_radius=10)
    producer_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    producer_title = ctk.CTkLabel(producer_frame, text=get_text("producer.title"), 
                                 font=("Arial", 18, "bold"))
    producer_title.pack(pady=10)
    
    producer_description = ctk.CTkLabel(producer_frame, text=get_text("producer.description"), 
                                       font=("Arial", 14))
    producer_description.pack(pady=5)
    
    producer_name = ctk.CTkLabel(producer_frame, text=get_text("producer.name"), 
                                font=("Arial", 16, "bold"))
    producer_name.pack(pady=10)
    
    github_button = ctk.CTkButton(producer_frame, text=get_text("producer.github_link"), 
                                 command=open_github_link, width=200,
                                 font=("Arial", 14, "bold"),
                                 fg_color=theme_colors["primary"],
                                 hover_color=theme_colors["secondary"])
    github_button.pack(pady=20)
    
    # Initialize database
    create_db()
    
    # Now that all widgets are created, load settings values into entries
    load_settings()
    
    # Start tray icon in a separate thread
    threading.Thread(target=start_tray_icon, daemon=True).start()
    
    # Set initial tab
    tabview.set(get_text("app.tabs.status"))
    
    # Log welcome message
    log_yaz(get_text("status.log.welcome"))
    log_yaz(f"🎨 {get_text('status.log.theme_changed').format(theme=get_text(f'themes.{current_theme}'))}")
    log_yaz(f"🌐 Language: {current_language}")
    log_yaz(f"👥 {get_text('status.total_accounts_followed')}: {followed_count_total}")
    
    # Start the main loop
    root.mainloop()

# Main entry point
if __name__ == "__main__":
    run_gui()
