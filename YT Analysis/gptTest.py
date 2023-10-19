# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="skeskinen/llama-lite-134m")

print(pipe("What is CNC?"))