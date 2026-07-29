"""German A1 vocabulary practice program.

Reads data/german_a1_vocabulary.md, lets the user pick one of the 21
vocabulary groups, then quizzes them: show the English meaning, the user
types the German word, and the program reports right/wrong plus the German
answer before moving to the next word. Ends with a summary of misses.
"""
from __future__ import annotations

import os
import random
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from vocab_parser import Group, Word, normalize_user_answer, parse_vocabulary

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "german_a1_vocabulary.md")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("German A1 Vocabulary Practice")
        self.geometry("640x480")
        self.minsize(520, 400)

        self.groups: list[Group] = parse_vocabulary(DATA_PATH)

        self.header_font = tkfont.Font(size=16, weight="bold")
        self.big_font = tkfont.Font(size=20)
        self.normal_font = tkfont.Font(size=12)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self.container = container

        self.frames: dict[type, tk.Frame] = {}
        for F in (MenuFrame, PracticeFrame, SummaryFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame(MenuFrame)

    def show_frame(self, frame_class: type) -> None:
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def start_practice(self, group: Group) -> None:
        self.frames[PracticeFrame].start(group)
        self.show_frame(PracticeFrame)

    def show_summary(self, group: Group, words: list[Word], results: list[bool], user_answers: list[str]) -> None:
        self.frames[SummaryFrame].set_results(group, words, results, user_answers)
        self.show_frame(SummaryFrame)


class MenuFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="German A1 Vocabulary Practice", font=app.header_font).pack(pady=(20, 10))
        ttk.Label(self, text="Choose a group to practice:").pack(pady=(0, 10))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(
            list_frame, font=app.normal_font, yscrollcommand=scrollbar.set, activestyle="dotbox"
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for group in app.groups:
            self.listbox.insert(
                "end", f"{group.number}. {group.title} ({len(group.words)} words)"
            )

        self.listbox.bind("<Double-Button-1>", lambda e: self.start_selected())
        self.listbox.bind("<Return>", lambda e: self.start_selected())
        self.listbox.selection_set(0)

        ttk.Button(self, text="Start Practice", command=self.start_selected).pack(pady=(0, 20))

    def on_show(self) -> None:
        self.listbox.focus_set()

    def start_selected(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        group = self.app.groups[selection[0]]
        if group.words:
            self.app.start_practice(group)


class PracticeFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent)
        self.app = app

        self.group: Group | None = None
        self.words: list[Word] = []
        self.index = 0
        self.results: list[bool] = []
        self.user_answers: list[str] = []
        self.state = "answering"  # or "feedback"

        top = ttk.Frame(self)
        top.pack(fill="x", padx=20, pady=(15, 5))
        self.group_label = ttk.Label(top, font=app.normal_font)
        self.group_label.pack(side="left")
        self.stats_label = ttk.Label(top, font=app.normal_font)
        self.stats_label.pack(side="right")

        self.progress_label = ttk.Label(self, font=app.normal_font)
        self.progress_label.pack(pady=(0, 10))

        ttk.Label(self, text="English meaning:", font=app.normal_font).pack(pady=(20, 5))
        self.english_label = ttk.Label(self, font=app.big_font, wraplength=560, justify="center")
        self.english_label.pack(pady=(0, 20))

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.entry_var, font=app.big_font, justify="center")
        self.entry.pack(pady=5, ipady=4, padx=40, fill="x")
        self.entry.bind("<Return>", lambda e: self.handle_primary_action())

        self.feedback_label = ttk.Label(self, font=app.big_font)
        self.feedback_label.pack(pady=(15, 5))
        self.answer_label = ttk.Label(self, font=app.normal_font, wraplength=560, justify="center")
        self.answer_label.pack(pady=(0, 10))

        self.action_button = ttk.Button(self, text="Submit", command=self.handle_primary_action)
        self.action_button.pack(pady=15)

        self.bind("<Return>", lambda e: self.handle_primary_action())

    def start(self, group: Group) -> None:
        self.group = group
        self.words = list(group.words)
        random.shuffle(self.words)
        self.index = 0
        self.results = []
        self.user_answers = []
        self.group_label.config(text=f"Group {group.number}: {group.title}")
        self.show_current_word()

    def on_show(self) -> None:
        self.entry.focus_set()

    def show_current_word(self) -> None:
        self.state = "answering"
        word = self.words[self.index]
        self.progress_label.config(text=f"Word {self.index + 1} of {len(self.words)}")
        self.update_stats()
        self.english_label.config(text=word.english)
        self.entry_var.set("")
        self.entry.config(state="normal")
        self.feedback_label.config(text="")
        self.answer_label.config(text="")
        self.action_button.config(text="Submit")
        self.entry.focus_set()

    def update_stats(self) -> None:
        correct = sum(1 for r in self.results if r)
        incorrect = sum(1 for r in self.results if not r)
        self.stats_label.config(text=f"Correct: {correct}   Incorrect: {incorrect}")

    def handle_primary_action(self) -> None:
        if self.state == "answering":
            self.submit_answer()
        else:
            self.next_word()

    def submit_answer(self) -> None:
        word = self.words[self.index]
        raw_answer = self.entry_var.get()
        normalized = normalize_user_answer(raw_answer)
        is_correct = normalized in word.accepted

        self.results.append(is_correct)
        self.user_answers.append(raw_answer)
        self.update_stats()

        self.entry.config(state="disabled")
        if is_correct:
            self.feedback_label.config(text="Correct!", foreground="green")
        else:
            self.feedback_label.config(text="Incorrect", foreground="red")
        self.answer_label.config(text=f"German: {word.german_display}")
        self.action_button.config(text="Next")
        self.state = "feedback"

    def next_word(self) -> None:
        self.index += 1
        if self.index >= len(self.words):
            self.app.show_summary(self.group, self.words, self.results, self.user_answers)
        else:
            self.show_current_word()


class SummaryFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Session Summary", font=app.header_font).pack(pady=(20, 10))
        self.stats_label = ttk.Label(self, font=app.normal_font)
        self.stats_label.pack(pady=(0, 15))

        ttk.Label(self, text="Missed words:", font=app.normal_font).pack()

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.text = tk.Listbox(list_frame, font=app.normal_font, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text.yview)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(self, text="Back to Menu", command=lambda: app.show_frame(MenuFrame)).pack(pady=20)

    def set_results(
        self, group: Group, words: list[Word], results: list[bool], user_answers: list[str]
    ) -> None:
        total = len(words)
        correct = sum(1 for r in results if r)
        incorrect = total - correct
        self.stats_label.config(
            text=f"Group {group.number}: {group.title}\nTotal: {total}   Correct: {correct}   Incorrect: {incorrect}"
        )

        self.text.delete(0, "end")
        missed = [(w, a) for w, r, a in zip(words, results, user_answers) if not r]
        if not missed:
            self.text.insert("end", "None — perfect score!")
        else:
            for word, user_answer in missed:
                shown = user_answer.strip() or "(no answer)"
                self.text.insert("end", f"{word.german_display}  —  {word.english}  (you: {shown})")


if __name__ == "__main__":
    app = App()
    app.mainloop()
