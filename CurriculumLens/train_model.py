#!/usr/bin/env python3
"""
train_model.py  –  CurriculumLens
Run this script to train and save the syllabus similarity classifier.

Usage:
    python train_model.py
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.model_trainer import train

if __name__ == "__main__":
    train()
