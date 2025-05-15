PromptCraft AI is a sophisticated desktop application built with Python and PyQt6, designed to help users generate high-quality, detailed prompts for various AI models, including image and video generators. Powered by Google's Gemini AI, PromptCraft AI provides an intuitive interface for both basic and advanced prompt engineering, as well as the ability to generate prompts from uploaded images.



## Key Features

*   **🧠 Gemini AI Powered:** Leverages Google's advanced Gemini models (including multimodal vision capabilities) for intelligent prompt generation and analysis.
*   **📝 Multiple Generation Modes:**
    *   **Basic Mode:** For quick and straightforward prompt creation based on a core idea. Supports batch generation for multiple variations.
    *   **Image Prompt (Advanced):** Offers fine-grained control over image prompt creation with detailed parameters like primary & secondary styles, character details, scene, artistic influences, camera settings, lighting, color palettes, and negative prompts. Features preset options for many fields.
    *   **Video Prompt Mode:** A specialized toolkit to craft detailed prompts for AI video generation, including concept, style, scene, key actions, characters, camera work, pacing, and audio mood cues. Features preset options.
*   **🖼️ Image-to-Prompt:**
    *   Upload an image, and PromptCraft AI will use Gemini Vision to generate a descriptive prompt.
    *   Option to tailor the generated prompt for either an AI Image Generator or an AI Video Generator.
*   **📚 Prompt Library:** Save, organize, and quickly reuse your favorite or most effective prompts. Prompts are saved locally.
*   **🎨 Customizable UI Themes:** Switch between a futuristic dark theme (default) and a clean light theme.
*   **🔧 User-Friendly Interface:** Designed with PyQt6 for a responsive and good-looking experience, suitable for both beginners and experienced AI prompters.
*   **⚙️ Asynchronous Operations:** API calls to Gemini are handled in separate threads to keep the UI responsive.

## Prerequisites

*   Python 3.8 or newer.
*   A Google Gemini API Key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/PromptCraftAI.git # Replace with your actual repo URL
    cd PromptCraftAI
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Make sure you have `pip` installed and upgraded. Then, install the required packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your Gemini API Key:**
    PromptCraft AI uses the `python-dotenv` library to load your API key from a `.env` file.
    *   In the root directory of the project (where `promptcraft_ai_qt.py` is located), create a file named `.env`.
    *   Add your Gemini API key to this file:
        ```
        GEMINI_API_KEY="YOUR_ACTUAL_API_KEY_HERE"
        ```
    *   **Important:** Add the `.env` file to your `.gitignore` if you are using Git to prevent accidentally committing your API key.

    *(Optional)* You can also set environment variables `GEMINI_TEXT_MODEL` and `GEMINI_VISION_MODEL` in your `.env` file if you need to use specific model IDs different from the defaults (e.g., `"models/gemini-1.5-flash-latest"`). Example:
    ```
    GEMINI_TEXT_MODEL="models/your-specific-text-model-id"
    GEMINI_VISION_MODEL="models/your-specific-vision-model-id"
    ```

## Running the Application

Once the dependencies are installed and your API key is set up in the `.env` file:

1.  Ensure your virtual environment is activated.
2.  Navigate to the project directory in your terminal.
4.  Run the main application script:
    ```bash
    python promptcraft_ai_qt.py
    ```

The PromptCraft AI application window should now open.

## Usage

*   **Navigation:** Use the tabs at the top to switch between Basic, Image Prompt (Advanced), Video Prompt, Image-to-Prompt, and Library modes.
*   **Basic Mode:** Enter a core idea. Optionally, load an existing prompt and provide modification instructions. Set the number of variations for batch generation.
*   **Image Prompt (Advanced) / Video Prompt:** Fill in the detailed fields to craft precise prompts. Many fields offer presets in dropdowns but also allow custom typed input.
*   **Image-to-Prompt:** Upload an image, select whether you want a prompt for an image or video generator, then click "Generate".
*   **Prompt Library:** Save generated prompts using the "💾 Save to Library" button. Load, view, or delete saved prompts from the "📚 Library" tab.
*   **Themes:** Go to `Settings > Theme` in the menubar to switch between UI themes.
*   **Tooltips:** Hover over most input fields and buttons for brief explanations.
