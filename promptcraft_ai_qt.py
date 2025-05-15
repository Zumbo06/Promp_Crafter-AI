import sys
import os
import json
import traceback
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFileDialog, QMessageBox, QStatusBar, QSpacerItem, QSizePolicy,
    QListWidget, QListWidgetItem, QInputDialog, QSpinBox, QMenuBar,
    QRadioButton, QButtonGroup, QComboBox, QTextBrowser # <--- Added QTextBrowser
)
from PyQt6.QtGui import QGuiApplication, QPixmap, QImage, QAction, QActionGroup,QIcon
from PyQt6.QtCore import Qt, QSize, QThread, QObject, pyqtSignal, QTimer

# --- Configuration & Gemini Setup ---

GEMINI_API_KEY_VALID = False
text_model = None
vision_model = None
ERROR_MSG = "Gemini AI not initialized." # Default message
TEXT_MODEL_NAME_TO_TRY = os.environ.get("GEMINI_TEXT_MODEL_OVERRIDE", "gemini-2.0-flash-thinking-exp-1219")
VISION_MODEL_NAME_TO_TRY = os.environ.get("GEMINI_VISION_MODEL_OVERRIDE", "gemini-2.0-flash-thinking-exp-1219")

try:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment or .env file.")
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API Key configured.")

    print("\nListing available models for your API key (for informational purposes):")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
             print(f"  - Name: {m.name}, Display: {m.display_name}, SupportedMethods: {m.supported_generation_methods}")
    print("-" * 20)

    model_initialization_errors = []
    try:
        print(f"Attempting to initialize text model with: '{TEXT_MODEL_NAME_TO_TRY}'")
        text_model = genai.GenerativeModel(TEXT_MODEL_NAME_TO_TRY)
        print(f"Successfully initialized text model: {TEXT_MODEL_NAME_TO_TRY}")
    except Exception as e:
        err_msg = f"Failed to initialize text model '{TEXT_MODEL_NAME_TO_TRY}': {e}"
        print(err_msg)
        model_initialization_errors.append(err_msg)
        text_model = None

    try:
        print(f"Attempting to initialize vision model with: '{VISION_MODEL_NAME_TO_TRY}'")
        vision_model = genai.GenerativeModel(VISION_MODEL_NAME_TO_TRY)
        print(f"Successfully initialized vision model: {VISION_MODEL_NAME_TO_TRY}")
    except Exception as e:
        err_msg = f"Failed to initialize vision model '{VISION_MODEL_NAME_TO_TRY}': {e}"
        print(err_msg)
        model_initialization_errors.append(err_msg)
        vision_model = None

    if text_model or vision_model:
        GEMINI_API_KEY_VALID = True
        if model_initialization_errors:
            ERROR_MSG = "Gemini API Key configured. However, there were issues initializing specific models:\n" + "\n".join(model_initialization_errors)
        else: ERROR_MSG = ""
    else:
        if "GEMINI_API_KEY not found" not in ERROR_MSG:
            ERROR_MSG = "Gemini API key configured, but failed to initialize any usable models. Check model ID(s) and API access.\nDetails:\n{}".format("\n".join(model_initialization_errors))
        GEMINI_API_KEY_VALID = False
except ValueError as e: ERROR_MSG = str(e); GEMINI_API_KEY_VALID = False
except Exception as e: ERROR_MSG = f"Critical error during Gemini configuration: {e}\n{traceback.format_exc()}"; GEMINI_API_KEY_VALID = False


# --- Constants ---
APP_NAME = "PromptCrafter AI"
APP_VERSION = "1.3.0" # Updated version
LIBRARY_FILE = "prompt_library.json"
num_variations_for_worker = 1

# --- Stylesheets ---

DARK_CYBORG_STYLESHEET = """
    /* ... (previous styles including QComboBox) ... */
    QTextBrowser { /* Similar to QTextEdit */
        background-color: #1e2228; color: #d0d0d0; border: 1px solid #3e4451;
        border-radius: 4px; padding: 5px;
    }
    QMainWindow, QDialog { background-color: #282c34; color: #abb2bf; }
    QTabWidget::pane { border-top: 2px solid #61afef; background-color: #21252b; }
    QTabBar::tab {
        background: #2c313a; color: #abb2bf; border: 1px solid #1c1e24;
        border-bottom: none; border-top-left-radius: 5px; border-top-right-radius: 5px;
        min-width: 100px; padding: 8px 12px; margin-right: 1px; font-weight: bold;
    }
    QTabBar::tab:selected, QTabBar::tab:hover { background: #61afef; color: #21252b; }
    QWidget { background-color: #282c34; color: #abb2bf; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }
    QLabel { color: #c8c8c8; padding-top: 2px; padding-bottom: 2px; }
    QLabel[isHeader="true"] {
        font-size: 13pt; font-weight: bold; color: #61afef; margin-bottom: 8px;
        border-bottom: 1px solid #3e4451; padding-bottom: 4px;
    }
    QLineEdit, QTextEdit, QListWidget, QSpinBox, QComboBox {
        background-color: #1e2228; color: #d0d0d0; border: 1px solid #3e4451;
        border-radius: 4px; padding: 5px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
        border-left-width: 1px; border-left-color: #3e4451; border-left-style: solid;
        border-top-right-radius: 3px; border-bottom-right-radius: 3px; background-color: #3e4451;
    }
    QComboBox::down-arrow { image: url(none); }
    QComboBox QAbstractItemView {
        background-color: #1e2228; color: #d0d0d0; border: 1px solid #61afef;
        selection-background-color: #61afef; selection-color: #1e2228;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        subcontrol-origin: border; subcontrol-position: top right; width: 16px;
        border-image: none; border-radius: 2px; background-color: #3e4451;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #4b5263; }
    QSpinBox::up-arrow, QSpinBox::down-arrow { image: url(none); }
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #61afef; background-color: #252930;
    }
    QListWidget::item { padding: 5px; }
    QListWidget::item:selected { background-color: #61afef; color: #21252b; }
    QListWidget::item:hover:!selected { background-color: #3e4451; }
    QPushButton {
        background-color: #61afef; color: #21252b; border: none; border-radius: 4px;
        padding: 8px 15px; min-width: 90px; font-weight: bold;
    }
    QPushButton:hover { background-color: #75c0ff; }
    QPushButton:pressed { background-color: #5297d6; }
    QPushButton[cssClass="secondary"] { background-color: #4b5263; color: #abb2bf; }
    QPushButton[cssClass="secondary"]:hover { background-color: #5f677a; }
    QPushButton[cssClass="info"] { background-color: #56b6c2; color: #21252b; }
    QPushButton[cssClass="info"]:hover { background-color: #60c4d0; }
    QPushButton[cssClass="success"] { background-color: #98c379; color: #21252b; }
    QPushButton[cssClass="success"]:hover { background-color: #a2d083; }
    QPushButton[cssClass="danger"] { background-color: #e06c75; color: #21252b; }
    QPushButton[cssClass="danger"]:hover { background-color: #ec7a83; }
    QPushButton[cssClass="counter"] { min-width: 30px; max-width: 30px; padding: 5px; font-size: 12pt; font-weight: bold;}
    QLineEdit[cssClass="counterDisplay"] { max-width: 40px; text-align: center; font-weight: bold; padding: 5px 2px;}
    QMenuBar { background-color: #21252b; color: #abb2bf; border-bottom: 1px solid #3e4451;}
    QMenuBar::item { background: transparent; padding: 4px 8px; }
    QMenuBar::item:selected { background: #3e4451; color: #61afef; }
    QMenu { background-color: #282c34; color: #abb2bf; border: 1px solid #3e4451; }
    QMenu::item:selected { background-color: #61afef; color: #21252b; }
    QStatusBar { background-color: #21252b; color: #9da5b4; }
    QStatusBar::item { border: none; }
    QScrollArea { border: none; background-color: transparent; }
    QScrollBar:vertical {
        border: none; background: #21252b; width: 10px; margin: 0px; border-radius: 5px;
    }
    QScrollBar::handle:vertical { background: #4b5263; min-height: 20px; border-radius: 5px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QInputDialog QLineEdit {
         background-color: #1e2228; color: #d0d0d0; border: 1px solid #61afef; padding: 5px;
    }
"""
LIGHT_FUSION_STYLESHEET = """
    /* ... (previous styles including QComboBox) ... */
    QTextBrowser {
        background-color: #ffffff; color: #222222; border: 1px solid #bababa;
        border-radius: 4px; padding: 5px;
    }
    QMainWindow, QDialog { background-color: #f0f0f0; color: #333333; }
    QTabWidget::pane { border-top: 2px solid #007acc; background-color: #ffffff; }
    QTabBar::tab {
        background: #e1e1e1; color: #333333; border: 1px solid #cccccc;
        border-bottom: none; border-top-left-radius: 5px; border-top-right-radius: 5px;
        min-width: 100px; padding: 8px 12px; margin-right: 1px; font-weight: bold;
    }
    QTabBar::tab:selected, QTabBar::tab:hover { background: #007acc; color: #ffffff; }
    QWidget { background-color: #f0f0f0; color: #333333; font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; }
    QLabel { color: #444444; padding-top: 2px; padding-bottom: 2px; }
    QLabel[isHeader="true"] {
        font-size: 13pt; font-weight: bold; color: #007acc; margin-bottom: 8px;
        border-bottom: 1px solid #cccccc; padding-bottom: 4px;
    }
    QLineEdit, QTextEdit, QListWidget, QSpinBox, QComboBox {
        background-color: #ffffff; color: #222222; border: 1px solid #bababa;
        border-radius: 4px; padding: 5px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
        border-left-width: 1px; border-left-color: #bababa; border-left-style: solid;
        border-top-right-radius: 3px; border-bottom-right-radius: 3px; background-color: #e0e0e0;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff; color: #222222; border: 1px solid #007acc;
        selection-background-color: #007acc; selection-color: #ffffff;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        subcontrol-origin: border; subcontrol-position: top right; width: 16px;
        border-image: none; border-radius: 2px; background-color: #e0e0e0;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #d0d0d0; }
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #007acc; background-color: #f8f8ff;
    }
    QListWidget::item { padding: 5px; }
    QListWidget::item:selected { background-color: #007acc; color: #ffffff; }
    QListWidget::item:hover:!selected { background-color: #e8f3ff; }
    QPushButton {
        background-color: #007acc; color: #ffffff; border: 1px solid #005fa3; border-radius: 4px;
        padding: 8px 15px; min-width: 90px; font-weight: bold;
    }
    QPushButton:hover { background-color: #0090f0; }
    QPushButton:pressed { background-color: #005fa3; }
    QPushButton[cssClass="secondary"] { background-color: #d0d0d0; color: #333333; border: 1px solid #b0b0b0; }
    QPushButton[cssClass="secondary"]:hover { background-color: #c0c0c0; }
    QPushButton[cssClass="info"] { background-color: #17a2b8; color: #ffffff; border: 1px solid #117a8b; }
    QPushButton[cssClass="info"]:hover { background-color: #1ab8cf; }
    QPushButton[cssClass="success"] { background-color: #28a745; color: #ffffff; border: 1px solid #1e7e34; }
    QPushButton[cssClass="success"]:hover { background-color: #2db94d; }
    QPushButton[cssClass="danger"] { background-color: #dc3545; color: #ffffff; border: 1px solid #bd2130; }
    QPushButton[cssClass="danger"]:hover { background-color: #e44d5a; }
    QPushButton[cssClass="counter"] { min-width: 30px; max-width: 30px; padding: 5px; font-size: 12pt; font-weight: bold; border: 1px solid #b0b0b0;}
    QLineEdit[cssClass="counterDisplay"] { max-width: 40px; text-align: center; font-weight: bold; padding: 5px 2px; border: 1px solid #bababa;}
    QMenuBar { background-color: #e8e8e8; color: #333333; border-bottom: 1px solid #cccccc;}
    QMenuBar::item { background: transparent; padding: 4px 8px; }
    QMenuBar::item:selected { background: #007acc; color: #ffffff; }
    QMenu { background-color: #ffffff; color: #333333; border: 1px solid #cccccc; }
    QMenu::item:selected { background-color: #007acc; color: #ffffff; }
    QStatusBar { background-color: #e8e8e8; color: #555555; }
    QStatusBar::item { border: none; }
    QScrollArea { border: none; background-color: transparent; }
    QScrollBar:vertical {
        border: 1px solid #cccccc; background: #f0f0f0; width: 10px; margin: 0px; border-radius: 5px;
    }
    QScrollBar::handle:vertical { background: #c0c0c0; min-height: 20px; border-radius: 5px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QInputDialog QLineEdit {
         background-color: #ffffff; color: #222222; border: 1px solid #007acc; padding: 5px;
    }
"""


class GeminiWorker(QObject):
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, query, context, num_variations, operation_type, pil_image=None):
        super().__init__()
        self.query = query
        self.context = context
        self.num_variations = num_variations
        self.operation_type = operation_type
        self.pil_image = pil_image
        self.quit_requested = False

    def _generate_single_prompt_core(self, user_query, context_instruction, variation_idx=0):
        global num_variations_for_worker
        if self.quit_requested: return "Operation cancelled by user."
        try:
            system_instruction = (
                "You are PromptCraft AI, an expert prompt engineering assistant. "
                "Your SOLE task is to generate a highly detailed, evocative, and comprehensive prompt suitable for an advanced AI image, video, or text generator, based on the user's request. "
                "The prompt should be rich in descriptive adjectives, specific nouns, and clearly articulate desired aesthetics, mood, and composition. "
                "Consider elements like subject details, environment, artistic style, lighting, camera view, color palette, and emotional tone. "
                "DO NOT include any conversational preambles, explanations, or any text other than the prompt itself. "
                "The output MUST be ONLY the generated prompt. "
                "If asked for variations, ensure each variation is distinct, creative, and also ONLY the prompt, maintaining a high level of detail."
            )
            if context_instruction:
                system_instruction += f"\nContext for this specific request: The user is trying to generate a '{context_instruction}'. Emphasize detail and richness for this type of prompt."
            variation_modifier = ""
            if num_variations_for_worker > 1 and variation_idx > 0:
                variation_prompts = [
                    "Provide another distinctly detailed variation based on the core request.",
                    "Offer a slightly different creative and highly descriptive take on the same core idea, delivering only the prompt.",
                    "Generate an alternative version of the prompt, exploring a different angle with rich detail, outputting only the prompt.",
                    "Give one more unique and detailed variant for this prompt idea, as only the prompt itself."
                ]
                variation_modifier = f"\n\nInstruction for this specific variation (out of several): {variation_prompts[variation_idx % len(variation_prompts)]} Ensure maximum detail and output only the prompt."
            gemini_prompt_payload = f"{system_instruction}\n\nUser's Request Details (aim for high detail):\n{user_query}{variation_modifier}"

            if not text_model:
                raise ConnectionError(f"Text model ('{TEXT_MODEL_NAME_TO_TRY}') is not initialized. Cannot generate text-based prompt.")
            response = text_model.generate_content(gemini_prompt_payload)
            generated_text = response.text.strip()
            unwanted_starts = [
                "Okay, here's the prompt:", "Okay, here is the prompt:", "Here's the prompt:", "Here is the prompt:",
                "Sure, here's a prompt:", "Sure, here is a prompt:", "Here's a prompt for you:", "Here is a prompt for you:",
                "Prompt:", "Generated Prompt:", "Okay, here's a variation:", "Here's another variation:"
            ]
            unwanted_ends = [
                "Let me know if you'd like another one!", "Hope this helps!", "Is there anything else I can help with?"
            ]
            for phrase in unwanted_starts:
                if generated_text.lower().startswith(phrase.lower()): generated_text = generated_text[len(phrase):].lstrip(); break
            for phrase in unwanted_ends:
                if generated_text.lower().endswith(phrase.lower()): generated_text = generated_text[:-len(phrase)].rstrip(); break
            return generated_text.strip()
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"WORKER Gemini Text Error (Var {variation_idx+1}): {e}\n{tb_str}")
            return f"API Error (Text Gen - Variation {variation_idx+1}): {e}"

    def run_text_generation(self):
        global num_variations_for_worker
        all_results = []
        for i in range(num_variations_for_worker):
            if self.quit_requested: all_results.append("Batch operation cancelled by user."); break
            result = self._generate_single_prompt_core(self.query, self.context, variation_idx=i)
            all_results.append(result)
        self.result_ready.emit(all_results)
        self.finished.emit()

    def run_vision_generation(self):
        if self.quit_requested: self.error_occurred.emit("Operation cancelled by user."); self.finished.emit(); return
        if not vision_model: self.error_occurred.emit(f"Vision model ('{VISION_MODEL_NAME_TO_TRY}') is not initialized."); self.finished.emit(); return
        if not self.pil_image: self.error_occurred.emit("No image provided to vision worker."); self.finished.emit(); return
        try:
            image_parts = [self.pil_image]
            target_prompt_type = self.context
            prompt_instruction_for_vision = ""
            if target_prompt_type == "video":
                prompt_instruction_for_vision = (
                    "You are PromptCraft AI. Analyze the provided static image with extreme detail. "
                    "Your task is to formulate ONLY a comprehensive and highly descriptive text prompt suitable for an AI VIDEO generator. "
                    "Infer a potential short narrative or sequence of events from the image. Describe potential character actions, motivations, and interactions. "
                    "Suggest dynamic camera movements (e.g., slow pan revealing a secret, rapid dolly zoom for tension, orbiting shot), "
                    "and consider scene transitions that could bring this static image to life as a compelling short video clip. "
                    "Elaborate on the visual style, lighting evolution, and atmospheric shifts that should occur. "
                    "DO NOT include any conversational text, preamble, or explanation. Output ONLY the video prompt string, rich with evocative language."
                )
            else:
                prompt_instruction_for_vision = (
                    "You are PromptCraft AI. Analyze the provided image with meticulous detail. "
                    "Your task is to formulate ONLY a comprehensive and highly descriptive text prompt suitable for an AI IMAGE generator. "
                    "Describe its primary subject(s) with specific attributes, the background elements in detail, the overall composition and framing, "
                    "the precise artistic style (e.g., hyperrealistic photograph, detailed oil painting, intricate watercolor, polished 3D render), "
                    "the nuances of lighting conditions (e.g., soft morning light with long shadows, dramatic chiaroscuro, vibrant neon reflections), the full color palette and its emotional impact, "
                    "and any significant textures, patterns, or emotional tone conveyed. "
                    "DO NOT include any conversational text, preamble, or explanation. Output ONLY the image prompt string, packed with descriptive keywords."
                )
            if self.quit_requested: self.error_occurred.emit("Operation cancelled by user."); self.finished.emit(); return
            response = vision_model.generate_content([prompt_instruction_for_vision] + image_parts)
            generated_text = response.text.strip()
            unwanted_starts = ["Prompt:", "Here's a prompt based on the image:", "Image Description Prompt:", "Video Prompt Idea:"]
            for phrase in unwanted_starts:
                if generated_text.lower().startswith(phrase.lower()): generated_text = generated_text[len(phrase):].lstrip(); break
            self.result_ready.emit([generated_text if generated_text else f"Gemini Vision returned an empty description for the {target_prompt_type} prompt."])
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"WORKER Vision Error ({target_prompt_type}): {e}\n{tb_str}")
            self.error_occurred.emit(f"Vision API Error ({target_prompt_type}): {e}")
        finally:
            self.finished.emit()

    def run(self):
        if not GEMINI_API_KEY_VALID: self.error_occurred.emit("Gemini API key is not configured or invalid."); self.finished.emit(); return
        if self.quit_requested: self.finished.emit(); return
        if self.operation_type == "text": self.run_text_generation()
        elif self.operation_type == "vision": self.run_vision_generation()
        else: self.error_occurred.emit(f"Unknown worker operation type: {self.operation_type}"); self.finished.emit()


# --- Main Application Class ---
class PromptCraftAI_Qt(QMainWindow):
    def __init__(self): 
        super().__init__()
        self.current_theme_name = "Dark Cyborg"
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.setGeometry(100, 100, 950, 800)
        self.setMinimumSize(800, 650)

        self.video_fields_qt = {}
        self.uploaded_image_pil = None
        self.prompt_library_data = self._load_library()

        self.gemini_thread = None
        self.gemini_worker = None

        self.basic_batch_count = 1
        self.MAX_VARIATIONS = 10

        self._create_menus()
        self._init_ui() 
        self.statusBar().showMessage("Ready", 3000)
        self._apply_theme(self.current_theme_name)

        if not GEMINI_API_KEY_VALID and "GEMINI_API_KEY not found" in ERROR_MSG:
            QMessageBox.critical(self, "API Key Error", ERROR_MSG + "\nPlease set the GEMINI_API_KEY in a .env file or your system environment and restart.")
        elif not GEMINI_API_KEY_VALID :
             QMessageBox.critical(self, "API Configuration Error", f"Failed to initialize Gemini AI models fully: {ERROR_MSG}\nSome AI features may be disabled or not work correctly. Check console for details.")
        elif GEMINI_API_KEY_VALID:
            if not text_model:
                 QMessageBox.warning(self, "Text Model Warning",
                                     f"Gemini Text Model ('{TEXT_MODEL_NAME_TO_TRY}') could not be initialized. "
                                     "Text-based generation features will be disabled.\n"
                                     f"Error details from setup (if any): {ERROR_MSG if 'Text model init failed' in ERROR_MSG else 'Unknown text model issue.'}")
            if not vision_model:
                 QMessageBox.warning(self, "Vision Model Warning",
                                     f"Gemini Vision Model ('{VISION_MODEL_NAME_TO_TRY}') could not be initialized. "
                                     "Image-to-Prompt feature will be disabled.\n"
                                     f"Error details from setup (if any): {ERROR_MSG if 'Vision model init failed' in ERROR_MSG else 'Unknown vision model issue.'}")

    def _create_menus(self): 
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("&Settings")
        theme_menu = settings_menu.addMenu("&Theme")
        dark_theme_action = QAction("Dark Cyborg (Default)", self)
        dark_theme_action.setCheckable(True); dark_theme_action.setChecked(self.current_theme_name == "Dark Cyborg")
        dark_theme_action.triggered.connect(lambda: self._apply_theme("Dark Cyborg")); theme_menu.addAction(dark_theme_action)
        light_theme_action = QAction("Light Fusion", self)
        light_theme_action.setCheckable(True); light_theme_action.setChecked(self.current_theme_name == "Light Fusion")
        light_theme_action.triggered.connect(lambda: self._apply_theme("Light Fusion")); theme_menu.addAction(light_theme_action)
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.addAction(dark_theme_action); self.theme_action_group.addAction(light_theme_action)
        self.theme_action_group.setExclusive(True)
        settings_menu.addSeparator()
        exit_action = QAction("&Exit", self); exit_action.setShortcut("Ctrl+Q"); exit_action.triggered.connect(self.close)
        settings_menu.addAction(exit_action)

    def _apply_theme(self, theme_name): 
        if theme_name == "Dark Cyborg": QApplication.instance().setStyleSheet(DARK_CYBORG_STYLESHEET)
        elif theme_name == "Light Fusion": QApplication.instance().setStyleSheet(LIGHT_FUSION_STYLESHEET)
        else: QApplication.instance().setStyleSheet(DARK_CYBORG_STYLESHEET); theme_name = "Dark Cyborg"
        self.current_theme_name = theme_name
        self.statusBar().showMessage(f"Theme changed to: {theme_name}", 3000)
        QTimer.singleShot(3000, lambda: self.statusBar().showMessage("Ready.", 2000))
        for action in self.theme_action_group.actions(): action.setChecked(action.text().startswith(theme_name))

    def _create_header_label(self, text):
        label = QLabel(text); label.setProperty("isHeader", True); return label

    def _init_ui(self): 
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.basic_tab_widget = self._create_basic_tab()
        self.advanced_img_tab_widget = self._create_advanced_image_tab()
        self.video_tab_widget = self._create_video_tab()
        self.image_prompt_tab_widget = self._create_image_prompt_tab()
        self.library_tab_widget = self._create_library_tab()
        self.help_tab_widget = self._create_help_tab() 

        self.tab_widget.addTab(self.basic_tab_widget, "✍️ Basic")
        self.tab_widget.addTab(self.advanced_img_tab_widget, "🖼️ Image Prompt (Advanced)")
        self.tab_widget.addTab(self.video_tab_widget, "🎬 Video Prompt")
        self.tab_widget.addTab(self.image_prompt_tab_widget, "🖼️ Image to Prompt")
        self.tab_widget.addTab(self.library_tab_widget, "📚 Library")
        self.tab_widget.addTab(self.help_tab_widget, "❓ Help / Guide") #Help Tab

      
        output_group = QWidget()
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(0,5,0,0)
        output_label = QLabel("Generated Prompt:")
        output_label.setStyleSheet("font-weight: bold; margin-bottom: 3px;")
        output_layout.addWidget(output_label)
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setMinimumHeight(150)
        self.output_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        output_layout.addWidget(self.output_text_edit)
        self.main_layout.setStretchFactor(self.tab_widget, 2)
        self.main_layout.setStretchFactor(output_group, 1)
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 5, 0, 0)
        buttons_layout.setSpacing(8)
        self.copy_button = QPushButton("📋 Copy")
        self.copy_button.setToolTip("Copy the generated prompt to clipboard")
        self.copy_button.clicked.connect(self._copy_prompt)
        buttons_layout.addWidget(self.copy_button)
        self.save_to_library_button = QPushButton("💾 Save to Library")
        self.save_to_library_button.setToolTip("Save the current generated prompt to your library")
        self.save_to_library_button.setProperty("cssClass", "success")
        self.save_to_library_button.clicked.connect(self._save_to_library_dialog)
        buttons_layout.addWidget(self.save_to_library_button)
        self.clear_output_button = QPushButton("🗑️ Clear Output")
        self.clear_output_button.setToolTip("Clear the output area")
        self.clear_output_button.setProperty("cssClass", "secondary")
        self.clear_output_button.clicked.connect(self._clear_output)
        buttons_layout.addWidget(self.clear_output_button)
        buttons_layout.addStretch(1)
        output_layout.addWidget(buttons_widget)
        self.main_layout.addWidget(output_group)
        self.setStatusBar(QStatusBar(self))



    def _create_basic_tab(self):
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        layout.addWidget(self._create_header_label("Basic Prompt Generation"))
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)
        self.basic_idea_text = QTextEdit()
        self.basic_idea_text.setPlaceholderText("e.g., a majestic dragon flying over a medieval castle")
        self.basic_idea_text.setToolTip("Describe the main concept or subject for your prompt.")
        self.basic_idea_text.setFixedHeight(80)
        form_layout.addRow(QLabel("Core Idea:"), self.basic_idea_text)
        self.basic_load_text = QTextEdit()
        self.basic_load_text.setPlaceholderText("(Optional) Paste an existing prompt here to modify it...")
        self.basic_load_text.setToolTip("Load a prompt you already have to refine or build upon.")
        self.basic_load_text.setFixedHeight(60)
        form_layout.addRow(QLabel("Load Existing Prompt:"), self.basic_load_text)
        self.basic_modify_instructions = QTextEdit()
        self.basic_modify_instructions.setPlaceholderText("(Optional) e.g., make it more cinematic, change to sunset")
        self.basic_modify_instructions.setToolTip("If loading a prompt, describe how you want AI to change it.")
        self.basic_modify_instructions.setFixedHeight(60)
        form_layout.addRow(QLabel("Modification Instructions:"), self.basic_modify_instructions)
        variation_counter_widget = QWidget()
        variation_counter_layout = QHBoxLayout(variation_counter_widget)
        variation_counter_layout.setContentsMargins(0,0,0,0)
        variation_counter_layout.setSpacing(5)
        self.basic_batch_decrease_btn = QPushButton("-")
        self.basic_batch_decrease_btn.setProperty("cssClass", "counter")
        self.basic_batch_decrease_btn.setToolTip("Decrease number of variations")
        self.basic_batch_decrease_btn.clicked.connect(self._decrease_basic_variations)
        variation_counter_layout.addWidget(self.basic_batch_decrease_btn)
        self.basic_batch_display = QLineEdit(str(self.basic_batch_count))
        self.basic_batch_display.setReadOnly(True)
        self.basic_batch_display.setProperty("cssClass", "counterDisplay")
        self.basic_batch_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.basic_batch_display.setToolTip("Current number of variations to generate")
        variation_counter_layout.addWidget(self.basic_batch_display)
        self.basic_batch_increase_btn = QPushButton("+")
        self.basic_batch_increase_btn.setProperty("cssClass", "counter")
        self.basic_batch_increase_btn.setToolTip("Increase number of variations")
        self.basic_batch_increase_btn.clicked.connect(self._increase_basic_variations)
        variation_counter_layout.addWidget(self.basic_batch_increase_btn)
        variation_counter_layout.addStretch()
        form_layout.addRow(QLabel("Number of Variations:"), variation_counter_widget)
        layout.addLayout(form_layout)
        generate_btn_container = QWidget()
        generate_btn_layout = QHBoxLayout(generate_btn_container)
        self.basic_generate_btn = QPushButton("✨ Generate Basic Prompt(s)")
        self.basic_generate_btn.setToolTip("Generate prompt(s) based on the inputs above.")
        self.basic_generate_btn.clicked.connect(self._trigger_gemini_basic_generation)
        self.basic_generate_btn.setMinimumHeight(35)
        generate_btn_layout.addStretch()
        generate_btn_layout.addWidget(self.basic_generate_btn)
        generate_btn_layout.addStretch()
        layout.addWidget(generate_btn_container)
        layout.addStretch(1)
        return tab_widget

    def _create_advanced_image_tab(self): # Renamed from _create_advanced_tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12) 
        layout.addWidget(self._create_header_label("Image Prompt Settings (Advanced)"))

        adv_form_layout = QFormLayout()
        adv_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        adv_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        adv_form_layout.setHorizontalSpacing(10)
        adv_form_layout.setVerticalSpacing(8) 

        self.adv_img_core_idea = QTextEdit() 
        self.adv_img_core_idea.setPlaceholderText("The central theme or subject of your image")
        self.adv_img_core_idea.setToolTip("Main subject of the image.")
        self.adv_img_core_idea.setFixedHeight(70)
        adv_form_layout.addRow(QLabel("Core Idea/Subject:"), self.adv_img_core_idea)

        # Primary Style ComboBox
        self.adv_img_style_combo = QComboBox()
        self.adv_img_style_combo.setEditable(True)
        self.adv_img_style_combo.setToolTip("Select a primary artistic style or type your own.")
        primary_style_presets = [ # Using the more extensive list from Phase 9a
            "", "Photorealistic", "Oil Painting", "Watercolor", "Sketch", "Pencil Drawing", "Charcoal Sketch",
            "Concept Art", "Digital Painting", "Matte Painting", "3D Render", "Voxel Art", "Pixel Art", "Anime Screenshot", "Manga Style",
            "Cartoon", "Impressionism", "Expressionism", "Surrealism", "Abstract", "Minimalist",
            "Steampunk", "Cyberpunk", "Dieselpunk", "Solarpunk", "Biopunk",
            "Fantasy Art", "Sci-Fi Art", "Horror Art", "Gothic Art", "Art Nouveau", "Art Deco", "Pop Art",
            "Vintage Photography", "Retro Futurism","Low Poly", "Claymation", "Stained Glass", "Mosaic", "Graffiti"
        ]
        self.adv_img_style_combo.addItems(primary_style_presets)
        self.adv_img_style_combo.lineEdit().setPlaceholderText("Select or type a primary style...")
        adv_form_layout.addRow(QLabel("Primary Artistic Style:"), self.adv_img_style_combo)

        # --- Secondary Style / Modifier ComboBox ---
        self.adv_img_secondary_style_combo = QComboBox()
        self.adv_img_secondary_style_combo.setEditable(True)
        self.adv_img_secondary_style_combo.setToolTip("Optional: Select or type a secondary style or modifier to combine.")
        secondary_style_modifier_presets = [
            "", # Empty for no secondary style
            # General Modifiers
            "Detailed", "Intricate", "Hyperdetailed", "Ornate", "Simplistic", "Clean lines",
            "Rough", "Gritty", "Smooth", "Polished", "Glossy", "Matte finish",
            "Grainy", "Film Grain", "VHS look", "Glitch Art", "Scanlines",
            "Low Contrast", "High Contrast", "Desaturated", "Vivid Colors", "Saturated Colors",
            "Lush", "Barren", "Ethereal", "Dreamlike", "Nightmarish", "Whimsical", "Atmospheric",
            # Specific Technique Modifiers
            "Sketchy outline", "Cel-shaded", "Toon shaded", "Chibi style", "Flat design",
            "Impasto", "Pointillism", "Cross-hatching", "Dithering", "Vintage illustration", "Blueprint style",
            # Lighting/Effect Modifiers (can overlap with main Lighting, but useful as quick adds)
            "Dramatic lighting", "Soft lighting", "Backlit", "Rim lit", "Glowing", "Volumetric fog",
            # Some primary styles that can also act as modifiers
            "Abstract elements", "Geometric patterns", "Surreal touches"
        ]
        self.adv_img_secondary_style_combo.addItems(secondary_style_modifier_presets)
        self.adv_img_secondary_style_combo.lineEdit().setPlaceholderText("Select or type a style modifier...")
        adv_form_layout.addRow(QLabel("Secondary Style/Modifier:"), self.adv_img_secondary_style_combo)
        

        self.adv_img_character_details = QTextEdit()
        self.adv_img_character_details.setPlaceholderText("Appearance, clothing, pose, species, expression...")
        self.adv_img_character_details.setToolTip("Detailed description of characters, if any.")
        self.adv_img_character_details.setFixedHeight(90)
        adv_form_layout.addRow(QLabel("Character Details:"), self.adv_img_character_details)

        self.adv_img_scene_environment = QTextEdit()
        self.adv_img_scene_environment.setPlaceholderText("Location, time of day, specific landmarks, atmosphere, weather...")
        self.adv_img_scene_environment.setToolTip("Describe the setting, background, and overall environment.")
        self.adv_img_scene_environment.setFixedHeight(90)
        adv_form_layout.addRow(QLabel("Scene & Environment:"), self.adv_img_scene_environment)

        self.adv_img_artistic_influence = QLineEdit()
        self.adv_img_artistic_influence.setPlaceholderText("e.g., by Van Gogh, Studio Ghibli, H.R. Giger")
        self.adv_img_artistic_influence.setToolTip("Specific artists, art movements, or studios to emulate.")
        adv_form_layout.addRow(QLabel("Artistic Influence:"), self.adv_img_artistic_influence)

        self.adv_img_camera_combo = QComboBox()
        self.adv_img_camera_combo.setEditable(True)
        self.adv_img_camera_combo.setToolTip("Select camera/composition elements or type your own.")
        camera_presets = [ # Using the extensive list from Phase 9a
            "", "Close-up Shot", "Medium Shot", "Full Shot", "Long Shot", "Extreme Wide Shot", "Establishing Shot",
            "Portrait Orientation", "Landscape Orientation", "Square Aspect Ratio", "Cinematic Aspect Ratio (16:9 or 2.35:1)",
            "Eye-Level Angle", "Low Angle Shot", "High Angle Shot", "Bird's-Eye View", "Worm's-Eye View", "Dutch Angle",
            "Rule of Thirds", "Golden Ratio", "Leading Lines", "Symmetry", "Asymmetrical Balance", "Framing",
            "Depth of Field (Bokeh)", "Shallow Depth of Field", "Deep Focus", "Motion Blur",
            "Wide-Angle Lens", "Telephoto Lens", "Fisheye Lens", "Macro Lens", "Tilt-Shift",
            "Panoramic", "Dynamic Composition", "Minimalist Composition"
        ]
        self.adv_img_camera_combo.addItems(camera_presets)
        self.adv_img_camera_combo.lineEdit().setPlaceholderText("Select or type camera/composition terms...")
        adv_form_layout.addRow(QLabel("Camera & Composition:"), self.adv_img_camera_combo)

        self.adv_img_lighting_combo = QComboBox()
        self.adv_img_lighting_combo.setEditable(True)
        self.adv_img_lighting_combo.setToolTip("Select lighting conditions or type your own.")
        lighting_presets = [ # Using the extensive list from Phase 9a
            "", "Natural Light", "Sunlight (Direct)", "Overcast (Diffused Light)", "Cloudy Sky",
            "Golden Hour (Sunrise/Sunset)", "Twilight", "Blue Hour", "Night Scene", "Moonlight", "Starlight",
            "Studio Lighting", "Softbox Lighting", "Ring Light", "Rembrandt Lighting", "Butterfly Lighting", "Split Lighting",
            "Backlighting", "Rim Lighting", "Edge Lighting", "Silhouette",
            "Cinematic Lighting", "Dramatic Lighting", "Chiaroscuro", "Film Noir Lighting", "High Key Lighting", "Low Key Lighting",
            "Volumetric Lighting", "God Rays", "Crepuscular Rays", "Lens Flare", "Anamorphic Lens Flare",
            "Candlelight", "Firelight", "Lantern Light", "Torchlight",
            "Neon Lights", "Cyberpunk Neon Glow", "Fluorescent Lighting", "Artificial Light", "Spotlight",
            "Warm Lighting", "Cool Lighting", "Ambient Occlusion", "Global Illumination", "Mystical Glow", "Ethereal Light"
        ]
        self.adv_img_lighting_combo.addItems(lighting_presets)
        self.adv_img_lighting_combo.lineEdit().setPlaceholderText("Select or type lighting terms...")
        adv_form_layout.addRow(QLabel("Lighting:"), self.adv_img_lighting_combo)

        self.adv_img_color_palette_combo = QComboBox()
        self.adv_img_color_palette_combo.setEditable(True)
        self.adv_img_color_palette_combo.setToolTip("Select a color scheme or describe your own.")
        color_palette_presets = [ # Using the extensive list from Phase 9a
            "", "Vibrant Colors", "Saturated Colors", "Muted Colors", "Desaturated Colors", "Pastel Colors", "Neon Colors", "Earthy Tones",
            "Monochromatic", "Monochromatic Blue", "Monochromatic Red", "Monochromatic Green",
            "Analogous Colors", "Complementary Colors", "Split-Complementary Colors", "Triadic Colors", "Tetradic Colors",
            "Warm Color Palette", "Cool Color Palette", "Neutral Colors",
            "Sepia Tone", "Grayscale", "Black and White", "High Contrast B&W",
            "Iridescent", "Opalescent", "Metallic Colors", "Gold Accents", "Silver Hues", "Bronze Tones",
            "Duotone", "Tritone", "Gradient Palette",
            "Dark and Moody Palette", "Bright and Cheerful Palette", "Dreamy Palette", "Synthwave Palette", "Vintage Palette"
        ]
        self.adv_img_color_palette_combo.addItems(color_palette_presets)
        self.adv_img_color_palette_combo.lineEdit().setPlaceholderText("Select or type color palette terms...")
        adv_form_layout.addRow(QLabel("Color Palette:"), self.adv_img_color_palette_combo)

        self.adv_img_negative_prompts = QTextEdit()
        self.adv_img_negative_prompts.setPlaceholderText("AVOID: blurry, ugly, text, watermark, deformed hands, extra limbs, bad anatomy, signature, low quality, jpeg artifacts")
        self.adv_img_negative_prompts.setToolTip("Elements or qualities to exclude (e.g., disfigured, tiling, out of frame).")
        self.adv_img_negative_prompts.setFixedHeight(70)
        adv_form_layout.addRow(QLabel("Negative Prompts:"), self.adv_img_negative_prompts)

        layout.addLayout(adv_form_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        layout.addWidget(QLabel("Modify Existing Image Prompt (Optional):"))
        load_mod_form_layout = QFormLayout()
        self.adv_img_load_text = QTextEdit()
        self.adv_img_load_text.setPlaceholderText("Paste an existing complex image prompt")
        self.adv_img_load_text.setToolTip("Load an image prompt to modify with fields above or instructions below.")
        self.adv_img_load_text.setFixedHeight(70)
        load_mod_form_layout.addRow(QLabel("Load Existing Prompt:"), self.adv_img_load_text)
        self.adv_img_modify_instructions = QTextEdit()
        self.adv_img_modify_instructions.setPlaceholderText("Describe changes to the loaded prompt")
        self.adv_img_modify_instructions.setToolTip("Instructions for AI on how to alter the loaded image prompt.")
        self.adv_img_modify_instructions.setFixedHeight(70)
        load_mod_form_layout.addRow(QLabel("Modification Instructions:"), self.adv_img_modify_instructions)
        layout.addLayout(load_mod_form_layout)
        generate_btn_container = QWidget()
        generate_btn_layout = QHBoxLayout(generate_btn_container)
        self.adv_img_generate_btn = QPushButton("✨ Generate Image Prompt")
        self.adv_img_generate_btn.setToolTip("Synthesize an advanced image prompt from all specified details.")
        self.adv_img_generate_btn.clicked.connect(self._trigger_gemini_advanced_image_generation)
        self.adv_img_generate_btn.setMinimumHeight(35)
        generate_btn_layout.addStretch(); generate_btn_layout.addWidget(self.adv_img_generate_btn); generate_btn_layout.addStretch()
        layout.addWidget(generate_btn_container)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_video_tab(self): 
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        content_widget = QWidget(); layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop); layout.setContentsMargins(15,15,15,15); layout.setSpacing(12)
        layout.addWidget(self._create_header_label("Video Prompt Settings"))
        video_form_layout = QFormLayout()
        video_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        video_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        video_form_layout.setHorizontalSpacing(10); video_form_layout.setVerticalSpacing(8)
        self.video_fields_qt = {}
        video_field_definitions = [
            ("Core Concept / Story:", "core_concept_story", "textedit", 80, "Main idea, narrative, or subject of the video", "The central theme or story of your video."),
            ("Video Style:", "video_style", "combo", 0,
             ["", "Cinematic Live-Action", "Anime", "2D Animation", "3D CGI Animation", "Stop-Motion", "Motion Graphics",
              "Documentary Style", "Found Footage", "Retro VHS", "Abstract Visuals", "Music Video Style", "Product Showcase", "Pixel Art Animation", "Claymation Video"],
             "Overall visual style of the video."),
            ("Scene & Setting:", "scene_setting", "textedit", 80, "Primary location(s), time period, environment details", "Describe where and when the video takes place."),
            ("Key Actions & Events:", "key_actions_events", "textedit", 100, "Sequence of main actions, plot points, or visual progression", "Outline the important events or visual changes that unfold."),
            ("Characters & Subjects:", "characters_subjects", "textedit", 80, "Descriptions of key characters, creatures, or main objects", "Details about people, creatures, or important subjects in the video."),
            ("Shot Types & Camera Movement:", "shot_types_camera_movement", "combo", 0,
             ["", "Establishing Shot", "Long Shot", "Medium Shot", "Close-up", "Extreme Close-up", "Cowboy Shot",
              "Tracking Shot", "Panning Shot", "Tilting Shot", "Dolly Shot (In/Out)", "Zoom (In/Out)", "Dolly Zoom (Vertigo Effect)",
              "Crane Shot", "Drone Shot / Aerial View", "Point-of-View (POV)", "Over-the-Shoulder Shot",
              "Slow Motion", "Time-Lapse", "Hyperlapse", "Bullet Time",
              "Static Shot", "Handheld Shaky Cam", "Whip Pan", "Match Cut", "J-Cut", "L-Cut", "Crash Zoom"],
             "Specify desired camera work like angles, shots, and movements."),
            ("Pacing & Duration:", "pacing_duration", "combo", 0,
             ["", "Fast-Paced", "Medium Paced", "Slow Paced", "Dynamic Pacing (Varied)",
              "Micro-short (e.g., <5 seconds)", "Short (e.g., 5-15 seconds)", "Medium (e.g., 15-60 seconds)", "Longer (e.g., >1 minute)",
              "Quick Cuts", "Long Takes", "Montage Sequence"],
             "Overall speed, rhythm, and approximate length of the video or sequences."),
            ("Lighting & Atmosphere:", "lighting_atmosphere", "combo", 0,
             ["", "Natural Light", "Sunlight", "Overcast", "Golden Hour", "Twilight", "Blue Hour", "Night Scene", "Moonlight",
              "Studio Lighting", "Cinematic Lighting", "Dramatic Lighting", "High-Key Lighting", "Low-Key Lighting", "Film Noir", "Volumetric Lighting",
              "Neon Glow", "Candlelight", "Firelight", "Warm Lighting", "Cool Lighting", "Eerie Atmosphere", "Mystical Atmosphere", "Joyful Atmosphere", "Tense Atmosphere", "Bright and Vibrant"],
             "Mood and lighting conditions (e.g., Bright, Dark, Mystical)."),
            ("Audio Cues (for Mood):", "audio_cues", "textedit", 70, "e.g., Epic orchestral score, Ambient nature sounds, Synthwave, Silence for tension", "Describe desired sound elements to guide visual mood (AI may not generate audio)."),
            ("Desired Output Format/Feeling:", "output_format_feeling", "combo", 0,
             ["", "Widescreen (16:9)", "Cinematic Widescreen (2.39:1)", "Vertical (9:16 for Social Media)", "Square (1:1)",
              "Grainy Film Look (8mm, 16mm, 35mm)", "Clean Digital Look (4K, 8K)", "Vintage TV Look (4:3, CRT scanlines)",
              "Dreamlike and Surreal", "Hyperrealistic", "Stylized and Artistic", "Gritty and Raw", "Polished and Sleek",
              "Looping Video", "Seamless Loop", "Boomerang Effect"],
             "Aspect ratio, specific visual feel, or other desired qualities.")
        ]
        for label_text, key, widget_type, height, presets_or_placeholder, tooltip_text in video_field_definitions:
            widget = None
            if widget_type == "textedit": widget = QTextEdit(); widget.setFixedHeight(height); widget.setPlaceholderText(presets_or_placeholder)
            elif widget_type == "combo":
                widget = QComboBox(); widget.setEditable(True)
                if isinstance(presets_or_placeholder, list): widget.addItems(presets_or_placeholder)
                widget.lineEdit().setPlaceholderText("Select or type...")
            elif widget_type == "lineedit": widget = QLineEdit(); widget.setPlaceholderText(presets_or_placeholder) # Unused for video currently
            if widget: widget.setToolTip(tooltip_text); video_form_layout.addRow(QLabel(label_text), widget); self.video_fields_qt[key] = widget
        layout.addLayout(video_form_layout)
        layout.addSpacerItem(QSpacerItem(20,20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        layout.addWidget(QLabel("Modify Existing Video Prompt (Optional):"))
        load_mod_form_layout = QFormLayout()
        self.video_load_text = QTextEdit(); self.video_load_text.setPlaceholderText("Paste an existing video prompt"); self.video_load_text.setToolTip("Load an existing video prompt to modify with fields above or instructions below."); self.video_load_text.setFixedHeight(70)
        load_mod_form_layout.addRow(QLabel("Load Existing Prompt:"), self.video_load_text)
        self.video_modify_instructions = QTextEdit(); self.video_modify_instructions.setPlaceholderText("Describe changes to the loaded prompt"); self.video_modify_instructions.setToolTip("Instructions for AI on how to alter the loaded video prompt."); self.video_modify_instructions.setFixedHeight(70)
        load_mod_form_layout.addRow(QLabel("Modification Instructions:"), self.video_modify_instructions)
        layout.addLayout(load_mod_form_layout)
        generate_btn_container = QWidget(); generate_btn_layout = QHBoxLayout(generate_btn_container)
        self.video_generate_btn = QPushButton("✨ Generate Video Prompt")
        self.video_generate_btn.setToolTip("Synthesize a detailed video prompt from the specified details.")
        self.video_generate_btn.clicked.connect(self._trigger_gemini_video_generation)
        self.video_generate_btn.setMinimumHeight(35)
        generate_btn_layout.addStretch(); generate_btn_layout.addWidget(self.video_generate_btn); generate_btn_layout.addStretch()
        layout.addWidget(generate_btn_container)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_image_prompt_tab(self): 
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self._create_header_label("Image-to-Prompt Generation"))
        self.img_upload_btn = QPushButton("📂 Upload Image")
        self.img_upload_btn.setToolTip("Select an image file (JPG, PNG, WEBP etc.) to generate a descriptive prompt from.")
        self.img_upload_btn.setProperty("cssClass", "info")
        self.img_upload_btn.setMinimumHeight(35)
        self.img_upload_btn.clicked.connect(self._upload_image_qt)
        upload_btn_container = QWidget(); upload_btn_layout = QHBoxLayout(upload_btn_container)
        upload_btn_layout.addStretch(); upload_btn_layout.addWidget(self.img_upload_btn); upload_btn_layout.addStretch()
        layout.addWidget(upload_btn_container)
        self.image_preview_label_qt = QLabel("No image uploaded.\nClick 'Upload Image' to select a file.")
        self.image_preview_label_qt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label_qt.setMinimumSize(300, 200)
        self.image_preview_label_qt.setStyleSheet(
            "border: 2px dashed #4b5263; background-color: #21252b; border-radius: 5px; padding: 10px;"
        )
        self.image_preview_label_qt.setToolTip("A preview of your uploaded image will appear here.")
        layout.addWidget(self.image_preview_label_qt)
        prompt_type_group_box_label = QLabel("Select Target Prompt Type:")
        prompt_type_group_box_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(prompt_type_group_box_label, 0, Qt.AlignmentFlag.AlignCenter)
        prompt_type_widget = QWidget()
        prompt_type_layout = QHBoxLayout(prompt_type_widget)
        prompt_type_layout.setContentsMargins(0,0,0,5)
        self.img_to_image_radio = QRadioButton("Image Prompt")
        self.img_to_image_radio.setToolTip("Generate a prompt suitable for AI Image Generators.")
        self.img_to_image_radio.setChecked(True)
        prompt_type_layout.addWidget(self.img_to_image_radio)
        self.img_to_video_radio = QRadioButton("Video Prompt")
        self.img_to_video_radio.setToolTip("Generate a prompt suggesting motion/narrative for AI Video Generators (experimental).")
        prompt_type_layout.addWidget(self.img_to_video_radio)
        self.img_prompt_type_group = QButtonGroup(self)
        self.img_prompt_type_group.addButton(self.img_to_image_radio, 1)
        self.img_prompt_type_group.addButton(self.img_to_video_radio, 2)
        centered_radio_widget = QWidget()
        centered_radio_layout = QHBoxLayout(centered_radio_widget)
        centered_radio_layout.addStretch()
        centered_radio_layout.addWidget(prompt_type_widget)
        centered_radio_layout.addStretch()
        layout.addWidget(centered_radio_widget)
        self.img_generate_btn = QPushButton("✨ Generate Prompt from Image")
        self.img_generate_btn.setToolTip("Analyze the uploaded image and generate a descriptive prompt based on the selected target type.")
        self.img_generate_btn.setMinimumHeight(35)
        self.img_generate_btn.clicked.connect(self._trigger_gemini_vision_generation)
        img_gen_btn_container = QWidget(); img_gen_btn_layout = QHBoxLayout(img_gen_btn_container)
        img_gen_btn_layout.addStretch(); img_gen_btn_layout.addWidget(self.img_generate_btn); img_gen_btn_layout.addStretch()
        layout.addWidget(img_gen_btn_container)
        layout.addStretch(1)
        return tab_widget

    def _create_library_tab(self): 
        tab_widget = QWidget(); main_layout = QVBoxLayout(tab_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop); main_layout.setContentsMargins(15,15,15,15); main_layout.setSpacing(10)
        main_layout.addWidget(self._create_header_label("Prompt Library"))
        self.library_list_widget_qt = QListWidget()
        self.library_list_widget_qt.setAlternatingRowColors(True)
        self.library_list_widget_qt.itemDoubleClicked.connect(self._load_from_library_on_double_click)
        self.library_list_widget_qt.setToolTip("Your saved prompts. Double-click to load.")
        main_layout.addWidget(self.library_list_widget_qt)
        self._refresh_library_list_widget()
        buttons_container = QWidget(); buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0,5,0,0); buttons_layout.setSpacing(10)
        load_btn = QPushButton("📂 Load Selected")
        load_btn.setToolTip("Load the selected prompt into the active generation tab's 'Load Existing' field.")
        load_btn.setProperty("cssClass", "info"); load_btn.clicked.connect(self._load_from_library)
        buttons_layout.addWidget(load_btn)
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setToolTip("Permanently delete the selected prompt from the library.")
        delete_btn.setProperty("cssClass", "danger"); delete_btn.clicked.connect(self._delete_from_library)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch(1)
        main_layout.addWidget(buttons_container)
        return tab_widget

    # +++ Help Tab +++
    def _create_help_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        help_widget = QWidget()
        layout = QVBoxLayout(help_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(self._create_header_label("❓ PromptCraft AI - User Guide"))

        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True) # If you add any URLs
        text_browser.setReadOnly(True)

        # --- Help Content (HTML Formatted) ---
        help_html = """
        <html>
        <head>
            <style>
                body { font-family: "Segoe UI", Arial, sans-serif; line-height: 1.6; }
                h2 { color: #61afef; border-bottom: 1px solid #4b5263; padding-bottom: 5px; margin-top: 20px;}
                h3 { color: #98c379; margin-top: 15px; }
                p { margin-bottom: 10px; }
                ul { margin-left: 20px; margin-bottom: 10px; }
                li { margin-bottom: 5px; }
                code { background-color: #1e2228; padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace; }
                strong { font-weight: bold; }
            </style>
        </head>
        <body>
            <h2>Welcome to PromptCraft AI!</h2>
            <p>This guide will help you get started with generating amazing prompts for your AI projects.</p>

            <h2>API Key Setup</h2>
            <p>PromptCraft AI requires a Google Gemini API Key to function.
            You need to set an environment variable named <code>GEMINI_API_KEY</code> with your key.
            Alternatively, you can create a <code>.env</code> file in the application's directory with the line:
            <code>GEMINI_API_KEY="YOUR_API_KEY_HERE"</code>.</p>
            <p>You can also try overriding default model names using <code>GEMINI_TEXT_MODEL_OVERRIDE</code> and <code>GEMINI_VISION_MODEL_OVERRIDE</code> environment variables if you have access to specific preview models.</p>

            <h2>Using the Tabs</h2>

            <h3>✍️ Basic Tab</h3>
            <ul>
                <li><strong>Core Idea:</strong> Enter a simple description of what you want.</li>
                <li><strong>Load Existing Prompt:</strong> Paste a prompt you already have to modify it.</li>
                <li><strong>Modification Instructions:</strong> If loading a prompt, tell the AI how to change it (e.g., "make it cyberpunk", "add a cat").</li>
                <li><strong>Number of Variations:</strong> Use the +/- buttons to choose how many different prompt variations you want (1-10).</li>
                <li>Click "Generate Basic Prompt(s)".</li>
            </ul>

            <h3>🖼️ Image Prompt (Advanced) Tab</h3>
            <p>Craft detailed prompts for AI image generators.</p>
            <ul>
                <li>Fill in the various fields like <strong>Artistic Style</strong>, <strong>Character Details</strong>, <strong>Scene & Environment</strong>, etc. Many fields have dropdowns with presets, but you can also type your own custom values.</li>
                <li><strong>Artistic Influence:</strong> Mention specific artists or art movements.</li>
                <li><strong>Camera & Composition:</strong> Define angles, shot types, lens effects.</li>
                <li><strong>Lighting & Color Palette:</strong> Specify mood and visual tones.</li>
                <li><strong>Negative Prompts:</strong> List things you want the AI to AVOID generating.</li>
                <li>Use "Load Existing Prompt" and "Modification Instructions" as in the Basic tab for further refinement.</li>
                <li>Click "Generate Image Prompt".</li>
            </ul>

            <h3>🎬 Video Prompt Tab</h3>
            <p>Design prompts for AI video generation.</p>
            <ul>
                <li>Similar to the Advanced Image tab, but with fields tailored for video concepts (e.g., <strong>Core Concept/Story</strong>, <strong>Video Style</strong>, <strong>Key Actions & Events</strong>, <strong>Shot Types & Camera Movement</strong>, <strong>Pacing & Duration</strong>).</li>
                <li>Many fields offer presets via dropdowns, and you can also type custom entries.</li>
                <li>Use "Load Existing Prompt" and "Modification Instructions" if needed.</li>
                <li>Click "Generate Video Prompt".</li>
            </ul>

            <h3>🖼️ Image to Prompt Tab</h3>
            <ul>
                <li>Click "Upload Image" to select an image file from your computer. A preview will be shown.</li>
                <li>Select the <strong>Target Prompt Type</strong>:
                    <ul>
                        <li><strong>Image Prompt:</strong> To get a descriptive prompt for generating a similar static image.</li>
                        <li><strong>Video Prompt:</strong> To get a prompt that suggests a short video concept based on the image (experimental).</li>
                    </ul>
                </li>
                <li>Click "Generate Prompt from Image". The AI will analyze the image and create a prompt based on your target.</li>
            </ul>

            <h3>📚 Library Tab</h3>
            <ul>
                <li>After generating a prompt you like in any tab, it will appear in the "Generated Prompt" area at the bottom.</li>
                <li>Click the "💾 Save to Library" button. You'll be asked to name the prompt.</li>
                <li>The Library tab lists all your saved prompts.</li>
                <li><strong>Load:</strong> Select a prompt in the list and click "📂 Load Selected" (or double-click the item). It will be loaded into the "Load Existing Prompt" field of the currently active generation tab (Basic, Image Advanced, or Video) or the main output area.</li>
                <li><strong>Delete:</strong> Select a prompt and click "🗑️ Delete Selected" to remove it (confirmation will be asked).</li>
                <li>Your library is saved automatically when you close the application.</li>
            </ul>

            <h2>General Prompting Tips</h2>
            <ul>
                <li><strong>Be Specific:</strong> The more detail you provide, the closer the AI can get to your vision.</li>
                <li><strong>Use Keywords:</strong> Think about important terms that define your desired output.
                <li><strong>Iterate:</strong> Don't expect perfection on the first try. Generate, review, refine, and generate again.</li>
                <li><strong>Experiment:</strong> Try different styles, combinations, and phrasing.
                <li><strong>Negative Prompts:</strong> Tell the AI what *not* to include can be very powerful.</li>
                <li><strong>Combine Ideas:</strong> Use an existing prompt as a base and add new elements or modification instructions.</li>
            </ul>

            <p>Happy Prompting!</p>
        </body>
        </html>
        """
        text_browser.setHtml(help_html)
        layout.addWidget(text_browser)

        scroll_area.setWidget(help_widget)
        return scroll_area



    def _display_output(self, prompt_text, is_batch_result=False):
        if is_batch_result:
            current_text = self.output_text_edit.toPlainText()
            if current_text: self.output_text_edit.append("\n\n" + "="*40 + "\n")
            self.output_text_edit.append(prompt_text)
        else: self.output_text_edit.setPlainText(prompt_text)

    def _clear_output(self):
        self.output_text_edit.clear()
        self.statusBar().showMessage("Output cleared.", 2000)
        QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Ready.", 2000))

    def _copy_prompt(self):
        prompt = self.output_text_edit.toPlainText().strip()
        if prompt:
            QGuiApplication.clipboard().setText(prompt)
            QMessageBox.information(self, "Copied", "Prompt copied to clipboard!")
            self.statusBar().showMessage("Prompt copied.", 2000)
            QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Ready.", 2000))
        else: QMessageBox.warning(self, "Empty Output", "Nothing to copy.")

    def _set_ui_for_generation(self, is_generating, message="Processing..."):
        buttons_to_toggle = [
            self.basic_generate_btn, self.adv_img_generate_btn,
            self.video_generate_btn, self.img_generate_btn,
            self.copy_button, self.save_to_library_button, self.clear_output_button
        ]
        if hasattr(self, 'library_list_widget_qt'): # Check if library UI is initialized
             buttons_to_toggle.extend(self.library_tab_widget.findChildren(QPushButton))

        for btn in buttons_to_toggle:
            if btn: # Check if button attribute exists
                btn.setEnabled(not is_generating)

        if is_generating:
            self.statusBar().showMessage(message)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
            # Status bar will be updated by _handle_gemini_results or _handle_gemini_error or QTimer

    def _upload_image_qt(self):
        image_file_types = "Image files (*.jpg *.jpeg *.png *.webp *.bmp *.gif);;All files (*.*)"
        filepath, _ = QFileDialog.getOpenFileName(self, "Select an Image", "", image_file_types)
        if filepath:
            try:
                self.uploaded_image_pil = Image.open(filepath)
                if self.uploaded_image_pil.mode == "RGBA": qimage = QImage(self.uploaded_image_pil.tobytes("raw", "RGBA"), self.uploaded_image_pil.width, self.uploaded_image_pil.height, QImage.Format.Format_RGBA8888)
                elif self.uploaded_image_pil.mode == "RGB": qimage = QImage(self.uploaded_image_pil.tobytes("raw", "RGB"), self.uploaded_image_pil.width, self.uploaded_image_pil.height, QImage.Format.Format_RGB888)
                else: converted_pil_img = self.uploaded_image_pil.convert("RGBA"); qimage = QImage(converted_pil_img.tobytes("raw", "RGBA"), converted_pil_img.width, converted_pil_img.height, QImage.Format.Format_RGBA8888)
                if qimage.isNull(): raise ValueError("Failed to convert PIL image to QImage.")
                pixmap = QPixmap.fromImage(qimage)
                self.image_preview_label_qt.setPixmap(pixmap.scaled(self.image_preview_label_qt.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.image_preview_label_qt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.statusBar().showMessage(f"Image loaded: {os.path.basename(filepath)}", 4000)
                QTimer.singleShot(4000, lambda: self.statusBar().showMessage("Ready.", 2000))
            except FileNotFoundError: QMessageBox.critical(self, "Image Error", f"File not found: {filepath}"); self._reset_image_preview()
            except UnidentifiedImageError: QMessageBox.critical(self, "Image Error", f"Cannot identify image file: {filepath}."); self._reset_image_preview()
            except Exception as e: QMessageBox.critical(self, "Image Error", f"Failed to load image: {e}"); self._reset_image_preview()
        else: self.statusBar().showMessage("Image selection cancelled.", 2000); QTimer.singleShot(2000, lambda: self.statusBar().showMessage("Ready.", 2000))

    def _reset_image_preview(self):
        self.uploaded_image_pil = None
        self.image_preview_label_qt.setText("No image uploaded.\nClick 'Upload Image' to select a file.")
        self.image_preview_label_qt.setPixmap(QPixmap())

    def _update_basic_variation_display(self):
        self.basic_batch_display.setText(str(self.basic_batch_count))
        self.basic_batch_decrease_btn.setEnabled(self.basic_batch_count > 1)
        self.basic_batch_increase_btn.setEnabled(self.basic_batch_count < self.MAX_VARIATIONS)

    def _decrease_basic_variations(self):
        if self.basic_batch_count > 1:
            self.basic_batch_count -= 1
            self._update_basic_variation_display()

    def _increase_basic_variations(self):
        if self.basic_batch_count < self.MAX_VARIATIONS:
            self.basic_batch_count += 1
            self._update_basic_variation_display()

    # Library Methods (_load_library to closeEvent )
    def _load_library(self):
        if os.path.exists(LIBRARY_FILE):
            try:
                with open(LIBRARY_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
                if isinstance(data, list) and all(isinstance(i, dict) and 'name' in i and 'prompt' in i for i in data): return data
                else: print(f"Warn: Lib file '{LIBRARY_FILE}' bad format."); return []
            except json.JSONDecodeError: print(f"Warn: Lib file '{LIBRARY_FILE}' corrupt JSON."); return []
            except Exception as e: print(f"Error loading lib: {e}."); return []
        return []

    def _save_library(self):
        try:
            with open(LIBRARY_FILE, 'w', encoding='utf-8') as f: json.dump(self.prompt_library_data, f, indent=2)
        except Exception as e: QMessageBox.critical(self, "Library Save Error", f"Could not save library: {e}"); print(f"Error saving lib: {e}")

    def _refresh_library_list_widget(self):
        if not hasattr(self, 'library_list_widget_qt'): return
        self.library_list_widget_qt.clear()
        sorted_library = sorted(self.prompt_library_data, key=lambda x: x['name'].lower())
        for item_data in sorted_library:
            list_item = QListWidgetItem(item_data['name']); list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.library_list_widget_qt.addItem(list_item)

    def _save_to_library_dialog(self):
        prompt_to_save = self.output_text_edit.toPlainText().strip()
        if not prompt_to_save: QMessageBox.warning(self, "Empty Prompt", "No prompt to save."); return
        default_name = " ".join(prompt_to_save.split()[:5]) + ("..." if len(prompt_to_save.split()) > 5 else "")
        name, ok = QInputDialog.getText(self, "Save to Library", "Prompt Name:", QLineEdit.EchoMode.Normal, default_name)
        if ok and name.strip():
            name = name.strip()
            if any(item['name'].lower() == name.lower() for item in self.prompt_library_data):
                if QMessageBox.question(self, "Duplicate Name", f"Overwrite '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return
                self.prompt_library_data = [i for i in self.prompt_library_data if i['name'].lower() != name.lower()]
            self.prompt_library_data.append({"name": name, "prompt": prompt_to_save})
            self._refresh_library_list_widget(); self._save_library()
            QMessageBox.information(self, "Saved", f"Prompt '{name}' saved."); self.statusBar().showMessage(f"Saved '{name}'.", 3000)
            QTimer.singleShot(3000, lambda: self.statusBar().showMessage("Ready.", 2000))
        elif ok: QMessageBox.warning(self, "Name Required", "Please enter a valid name.")


    def _load_from_library_on_double_click(self, item_widget: QListWidgetItem):
        self._load_from_library(selected_item_widget=item_widget)

    def _load_from_library(self, selected_item_widget=None):
        if not selected_item_widget:
            s_items = self.library_list_widget_qt.selectedItems()
            if not s_items: QMessageBox.warning(self, "No Selection", "Select a prompt to load."); return
            selected_item_widget = s_items[0]
        p_data = selected_item_widget.data(Qt.ItemDataRole.UserRole)
        if not p_data or not isinstance(p_data, dict) or 'name' not in p_data or 'prompt' not in p_data:
            QMessageBox.critical(self, "Library Error", "Invalid library item data."); return
        p_name, p_text = p_data['name'], p_data['prompt']
        curr_tab = self.tab_widget.currentWidget()
        msg = f"Prompt '{p_name}' loaded"; loaded_field = False
        if curr_tab == self.basic_tab_widget: self.basic_load_text.setPlainText(p_text); self.basic_idea_text.clear(); self.basic_modify_instructions.clear(); msg += " to Basic tab."; loaded_field=True
        elif curr_tab == self.advanced_img_tab_widget: self.adv_img_load_text.setPlainText(p_text); msg += " to Image Prompt tab."; loaded_field=True
        elif curr_tab == self.video_tab_widget: self.video_load_text.setPlainText(p_text); msg += " to Video tab."; loaded_field=True
        self._display_output(f"--- Loaded: {p_name} ---\n\n{p_text}")
        if loaded_field: QMessageBox.information(self, "Prompt Loaded", msg)
        else: QMessageBox.information(self, "Prompt Loaded", f"'{p_name}' loaded to output area.")
        self.statusBar().showMessage(f"Loaded '{p_name}'.", 4000)
        QTimer.singleShot(4000, lambda: self.statusBar().showMessage("Ready.", 2000))

    def _delete_from_library(self):
        s_items = self.library_list_widget_qt.selectedItems()
        if not s_items: QMessageBox.warning(self, "No Selection", "Select a prompt to delete."); return
        p_data_del = s_items[0].data(Qt.ItemDataRole.UserRole)
        p_name = p_data_del.get('name', 'selected prompt')
        if QMessageBox.question(self, "Confirm Delete", f"Delete '{p_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.prompt_library_data = [i for i in self.prompt_library_data if i != p_data_del]
            self._refresh_library_list_widget(); self._save_library()
            QMessageBox.information(self, "Deleted", f"'{p_name}' deleted."); self.statusBar().showMessage(f"Deleted '{p_name}'.", 3000)
            QTimer.singleShot(3000, lambda: self.statusBar().showMessage("Ready.", 2000))

    def closeEvent(self, event):
        self._save_library()
        if self.gemini_thread and self.gemini_thread.isRunning():
            print("Stopping worker thread...")
            if self.gemini_worker: self.gemini_worker.quit_requested = True
            self.gemini_thread.quit()
            if not self.gemini_thread.wait(2000):
                print("Worker timeout, terminating."); self.gemini_thread.terminate(); self.gemini_thread.wait()
            else: print("Worker finished gracefully.")
        self.gemini_thread = None
        self.gemini_worker = None
        super().closeEvent(event)

    # Generation Trigger & Handling Methods
    def _trigger_gemini_operation(self, query, context, num_vars, op_type, pil_image=None, clear_previous_output=True):
        global num_variations_for_worker
        num_variations_for_worker = num_vars
        if self.gemini_thread is not None:
             if self.gemini_thread.isRunning():
                 QMessageBox.information(self, "Busy", "Generation in progress. Please wait.")
                 return
             self.gemini_thread = None # Explicitly clear if it was not running but existed
             self.gemini_worker = None

        if clear_previous_output:
            if num_vars == 1 or getattr(self, 'is_new_batch_start', False):
                self.output_text_edit.clear()
                if hasattr(self, 'is_new_batch_start'): self.is_new_batch_start = False

        self._set_ui_for_generation(True, f"Starting {context} generation ({num_vars} var)...")
        self.gemini_thread = QThread(self)
        self.gemini_worker = GeminiWorker(query, context, num_vars, op_type, pil_image)
        self.gemini_worker.moveToThread(self.gemini_thread)
        self.gemini_worker.result_ready.connect(self._handle_gemini_results)
        self.gemini_worker.error_occurred.connect(self._handle_gemini_error)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        # Disconnect before reconnecting to avoid multiple calls if a trigger is rapid
        try: self.gemini_thread.finished.disconnect(self._on_thread_finished_cleanup)
        except TypeError: pass
        try: self.gemini_worker.finished.disconnect(self.gemini_worker.deleteLater)
        except TypeError: pass
        try: self.gemini_thread.finished.disconnect(self.gemini_thread.deleteLater)
        except TypeError: pass

        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        self.gemini_thread.finished.connect(self._on_thread_finished_cleanup)

        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_thread.start()

    def _on_thread_finished_cleanup(self):
        print("Worker thread process finished. UI re-enabled.")
        self.gemini_thread = None
        self.gemini_worker = None
        self._set_ui_for_generation(False)


    def _trigger_gemini_basic_generation(self):
        idea = self.basic_idea_text.toPlainText().strip()
        loaded_prompt = self.basic_load_text.toPlainText().strip()
        mod_instructions = self.basic_modify_instructions.toPlainText().strip()
        num_vars = self.basic_batch_count
        user_request_details = ""
        if loaded_prompt:
            user_request_details += f"Base existing prompt to work with:\n```\n{loaded_prompt}\n```\n"
            if mod_instructions: user_request_details += f"Refine or modify according to: {mod_instructions}\n"
            elif idea: user_request_details += f"Refine/combine with core idea: {idea}\n"
            else: user_request_details += "Refine or generate variations.\n"
        elif idea: user_request_details += f"Generate from core idea: {idea}\n"
        else: QMessageBox.warning(self, "Input Missing", "Provide 'Core Idea' or 'Load Existing Prompt'."); return
        user_request_details += "Ensure the output is ONLY the generated prompt string."
        self.is_new_batch_start = True
        self._trigger_gemini_operation(user_request_details, "Basic Prompt", num_vars, "text", clear_previous_output=True)

  
    def _trigger_gemini_advanced_image_generation(self):
        global num_variations_for_worker; num_variations_for_worker = 1
        components = {
            "Core Idea/Subject": self.adv_img_core_idea.toPlainText().strip(),
            "Primary Artistic Style": self.adv_img_style_combo.currentText().strip(),
            "Secondary Style/Modifier": self.adv_img_secondary_style_combo.currentText().strip(), 
            "Character Details": self.adv_img_character_details.toPlainText().strip(),
            "Scene & Environment": self.adv_img_scene_environment.toPlainText().strip(),
            "Artistic Influence": self.adv_img_artistic_influence.text().strip(),
            "Camera & Composition": self.adv_img_camera_combo.currentText().strip(),
            "Lighting": self.adv_img_lighting_combo.currentText().strip(),
            "Color Palette": self.adv_img_color_palette_combo.currentText().strip(),
            "Negative Prompts (Elements to AVOID)": self.adv_img_negative_prompts.toPlainText().strip(),
        }
        loaded_prompt = self.adv_img_load_text.toPlainText().strip()
        mod_instructions = self.adv_img_modify_instructions.toPlainText().strip()
        user_request_details_parts = []
        context = "Advanced Image Prompt"

        if loaded_prompt:
            user_request_details_parts.append(f"Base existing image prompt:\n```\n{loaded_prompt}\n```")
            if mod_instructions: user_request_details_parts.append(f"Modify with: {mod_instructions}")
            user_request_details_parts.append(
                "Integrate or override with the specific components listed below. "
                "If a 'Secondary Style/Modifier' is provided, blend it with the 'Primary Artistic Style' or use it to further describe the overall aesthetic."
            ) # Added guidance for secondary style

        # Filter out empty components BEFORE creating the list for Gemini
        # Note: The key "Secondary Style/Modifier" will only be included if it has a value.
        active_components = {k: v for k, v in components.items() if v}

        if active_components:
            if not loaded_prompt:
                user_request_details_parts.append("Synthesize a detailed image prompt from the following components:")
            else: # If loaded_prompt exists, these are additions/overrides
                user_request_details_parts.append("\nSpecific Image Components (to integrate or override):")

            for key, value in active_components.items():
                user_request_details_parts.append(f"  - {key}: {value}")

        if not user_request_details_parts:
            if loaded_prompt and not mod_instructions and not active_components:
                user_request_details_parts.append(f"Refine or enhance this loaded image prompt:\n```\n{loaded_prompt}\n```")
            else:
                QMessageBox.warning(self, "Input Missing", "Please provide image prompt details or load a prompt with modification instructions."); return

        user_request_details_parts.append("\nOutput ONLY the image prompt string, ensuring all provided elements are considered.")
        full_user_request = "\n\n".join(user_request_details_parts)

        self._trigger_gemini_operation(full_user_request, context, 1, "text")

    def _trigger_gemini_video_generation(self):
        global num_variations_for_worker; num_variations_for_worker = 1
        components = {}
        for field_key, widget_ref in self.video_fields_qt.items():
            value = ""
            if isinstance(widget_ref, QTextEdit): value = widget_ref.toPlainText().strip()
            elif isinstance(widget_ref, QLineEdit): value = widget_ref.text().strip()
            elif isinstance(widget_ref, QComboBox): value = widget_ref.currentText().strip()
            if value: components[field_key.replace('_', ' ').title()] = value
        loaded_prompt = self.video_load_text.toPlainText().strip()
        mod_instructions = self.video_modify_instructions.toPlainText().strip()
        user_request_details_parts = []
        context = "Detailed Video Prompt"
        if loaded_prompt:
            user_request_details_parts.append(f"Base existing video prompt:\n```\n{loaded_prompt}\n```")
            if mod_instructions: user_request_details_parts.append(f"Modify with: {mod_instructions}")
            user_request_details_parts.append("Integrate/override with specific video components below if provided.")
        if components:
            user_request_details_parts.append("Synthesize a video prompt from these components:" if not loaded_prompt else "\nSpecific Video Components:")
            for label, value in components.items(): user_request_details_parts.append(f"  - {label}: {value}")
        if not user_request_details_parts:
            if loaded_prompt and not mod_instructions and not components:
                user_request_details_parts.append(f"Refine/enhance this loaded video prompt:\n```\n{loaded_prompt}\n```")
            else: QMessageBox.warning(self, "Input Missing", "Provide video prompt details or load prompt with instructions."); return
        user_request_details_parts.append("\nOutput ONLY the video prompt string.")
        full_user_request = "\n\n".join(user_request_details_parts)
        self._trigger_gemini_operation(full_user_request, context, 1, "text")

    def _trigger_gemini_vision_generation(self):
        if not vision_model: QMessageBox.critical(self, "API Error", "Gemini Vision model unavailable."); return
        if not self.uploaded_image_pil: QMessageBox.warning(self, "No Image", "Upload an image first."); return
        target_prompt_type = "image"
        if self.img_to_video_radio.isChecked(): target_prompt_type = "video"
        query_for_worker = f"Generate a {target_prompt_type} prompt from the provided image."
        self._trigger_gemini_operation(
            query=query_for_worker, context=target_prompt_type,
            num_vars=1, op_type="vision", pil_image=self.uploaded_image_pil
        )

    def _handle_gemini_results(self, results: list):
        global num_variations_for_worker
        if not results:
            self._display_output("Worker returned no results.")
            self.statusBar().showMessage("Generation finished: No results.", 4000)
            QTimer.singleShot(4000, lambda: self.statusBar().showMessage("Ready.", 2000))
            return
        current_op_message_base = "Generation"

        if num_variations_for_worker > 1:
            output_parts = []; has_errors_in_batch = False
            for i, text in enumerate(results):
                if "API Error" in text or "Operation cancelled" in text:
                    output_parts.append(f"--- Variation {i+1} FAILED ---\n{text}\n"); has_errors_in_batch = True
                else: output_parts.append(f"--- Prompt Variation {i+1} ---\n{text}\n")
            final_output = "\n\n".join(output_parts).strip()
            self.output_text_edit.setPlainText(final_output)
            if has_errors_in_batch:
                QMessageBox.warning(self, "Batch Generation Issues", "One or more prompt variations may have failed or were cancelled.")
                self.statusBar().showMessage("Batch complete with issues.", 5000)
            else: self.statusBar().showMessage(f"Batch of {num_variations_for_worker} prompts generated successfully.", 5000)
        else:
            result_text = results[0]
            if "API Error" in result_text or "Operation cancelled" in result_text:
                 self.output_text_edit.setPlainText(result_text)
                 self.statusBar().showMessage("Generation failed or cancelled. Check output.", 5000)
            else: self._display_output(result_text); self.statusBar().showMessage("Prompt generation successful.", 5000)
        QTimer.singleShot(5000, lambda: self.statusBar().showMessage("Ready.", 2000))

    def _handle_gemini_error(self, error_message: str):
        self._display_output(f"An error occurred:\n{error_message}")
        QMessageBox.critical(self, "Generation Error", f"An error occurred during generation:\n{error_message}")
        self.statusBar().showMessage(f"Error: {error_message[:60]}...", 7000)
        QTimer.singleShot(7000, lambda: self.statusBar().showMessage("Ready.", 2000))

# --- Run the Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)


    # Define the path to your icon file
    icon_path = "icons/promptcraft_logo.png" # Assuming it's in the same directory as the script
                                      # Or use a relative path like "icons/promptcraft_logo.png"
                                      # Or an absolute path if necessary

    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        print(f"Application icon set from: {icon_path}")
    else:
        print(f"Warning: Application icon file not found at '{icon_path}'. Using default system icon.")
 




    main_window = PromptCraftAI_Qt()
    main_window.show()

    sys.exit(app.exec())
