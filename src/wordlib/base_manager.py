#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class WordLibManager:
    def __init__(self, bot, name):
        self.bot = bot
        self.name = name

    def load_wordlib(self):
        raise NotImplementedError

    def process_message(self, message: str) -> str:
        raise NotImplementedError