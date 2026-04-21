# pico2-digit-recognition

> A handwritten digit recognizer running on Pi Pico 2, vibe-coded with `Gemini 3.1 Pro` (template) and `ChatGPT Thinking` (improvements)

> [!TIP]
> env:
> * PC: Python 3.10
> * Pico: CircuitPython 10
> * libs used will be informed as `requirements.txt` which will be added to this repo later

## Setup
First, clone this repo:
```bash
git clone https://github.com/MeowCata/pico2-digit-recognition
cd pico2-digit-recognition
```

Install necessary libs: 
```bash
pip install -r requirements.txt
```

Now let's train the model:
```bash
python train_model.py
```
After training, `pico_model.py` will be generated

Finally, upload the codes. Please drag-and-drop `code.py`(renamed from pico.py) and `pico_model.py` to Pico's disk(displayed as `CIRCUITPY`)

Once the codes uploaded, run `ui.py` on PC, and check out how this little model worked!

> [!IMPORTANT]
> Please replace [line10](https://github.com/MeowCata/pico2-digit-recognition/blob/main/ui_balanced.py#L10) in ui.py to your Pico's port before uploading. You can always check the port num in Device Manager
