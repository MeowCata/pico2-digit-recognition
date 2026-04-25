# pico2-digit-recognition

![Python](https://img.shields.io/badge/Python-3.10-blue)
![CircuitPython](https://img.shields.io/badge/CircuitPython-10.1.4-green)
![Platform](https://img.shields.io/badge/Board-Pico%202-orange)

A lightweight handwritten digit recognizer running **entirely on Pi Pico 2** using *CircuitPython* and a compact MLP model trained on MNIST.

## Features
- **Fully on-device handwritten digit recognition** on Raspberry Pi Pico 2
- Tiny MLP (32 hidden units) with ~97% MNIST test accuracy
- PCA fused into model weights for true MCU-side inference
- Quantized lightweight model optimized for CircuitPython
- PC drawing UI over serial
- ~1 second inference on Pico 2

## Screenshot
<img width="422" height="266" alt="image" src="https://github.com/user-attachments/assets/a9a90188-5dec-4783-95c2-507759cbebf1" />

<img width="521" height="630" alt="image" src="https://github.com/user-attachments/assets/ae8a04dc-a597-49aa-968e-3abfa961f8ef" />

<img width="735" height="112" alt="image" src="https://github.com/user-attachments/assets/860592d9-0cb4-461f-8adc-6f8b88215aac" />

## Setup

First, clone this repo:

```bash
git clone https://github.com/MeowCata/pico2-digit-recognition
cd pico2-digit-recognition
```

Install dependencies: 

```python
pip install numpy==1.26.4 scikit-learn==1.4.2 pyserial==3.5 Pillow==10.3.0
```

Now let's train the model:

```python
python train_model.py
```

After training, `pico_mnist_model.json` will be generated

> Want pre-trained model? Download it by clicking [here](https://github.com/MeowCata/pico2-digit-recognition/releases/download/MLP_hu32_1/pico_mnist_model.json)

Finally, upload the files to Pico. Please drag-and-drop `code.py`(**renamed from pico.py**) and `pico_mnist_model.json` to Pico's disk(displayed as `CIRCUITPY`)

Once the files are uploaded, run `ui.py` on your PC, select the serial port, and test the model.

## Releases

### v1.1 (Recommended)
- PCA is fused into the model during training — an integrated approach I really like.
- 32 hidden-unit compact model optimized for Pico 2.
- Special thanks to Gemini for the inspiration.

### Legacy
Contains two earlier experiments:

1. `mnistpico.zip`
- PCA computed on PC
- Deprecated because the goal was fully on-device inference

2. 64-hidden-unit model
- Higher accuracy
- Slower inference on Pico, therefore discontinued

## Acknowledgements
> Vibe coded using:
> - Gemini 3.1 Pro - template, model & UI refinement, plus cleaning up some early GPT-generated spaghetti
> - DeepSeek v4-flash - UI enhancement & port selector
> - ChatGPT - writing code for the initial version of using MNIST model (code in Legacy Release, `mnistpico.zip`) 
