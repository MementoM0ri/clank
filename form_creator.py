#!/usr/bin/env python3
"""
Form Creator - Create forms with name and questions, save as JSON
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os


class FormCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Form Creator")
        self.root.geometry("700x600")
        self.questions = []

        # Create main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Form name section
        name_frame = tk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(name_frame, text="Form Name:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.form_name_entry = tk.Entry(name_frame, width=50, font=("Arial", 11))
        self.form_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Question input section
        question_frame = tk.Frame(main_frame)
        question_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(question_frame, text="Add Question:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.question_entry = tk.Entry(question_frame, width=60, font=("Arial", 10))
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.question_entry.bind('<Return>', lambda e: self.add_question())

        add_btn = tk.Button(
            question_frame,
            text="Add",
            command=self.add_question,
            width=10,
            font=("Arial", 10),
            bg="#2196F3",
            fg="white"
        )
        add_btn.pack(side=tk.LEFT)

        # Questions list section
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(list_frame, text="Questions List:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))

        # Scrolled text to display questions
        self.questions_display = scrolledtext.ScrolledText(
            list_frame,
            width=70,
            height=15,
            font=("Arial", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.questions_display.pack(fill=tk.BOTH, expand=True)

        # Button frame for list operations
        list_btn_frame = tk.Frame(list_frame)
        list_btn_frame.pack(pady=(5, 0))

        remove_btn = tk.Button(
            list_btn_frame,
            text="Remove Last",
            command=self.remove_last_question,
            width=12,
            font=("Arial", 10)
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            list_btn_frame,
            text="Clear All",
            command=self.clear_questions,
            width=12,
            font=("Arial", 10)
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Action buttons frame
        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=(10, 0))

        save_btn = tk.Button(
            action_frame,
            text="Save Form",
            command=self.save_form,
            width=15,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = tk.Button(
            action_frame,
            text="Load Form",
            command=self.load_form,
            width=15,
            font=("Arial", 11),
            bg="#FF9800",
            fg="white"
        )
        load_btn.pack(side=tk.LEFT, padx=5)

    def add_question(self):
        """Add a question to the list."""
        question = self.question_entry.get().strip()

        if not question:
            messagebox.showwarning("Empty Question", "Please enter a question.")
            return

        self.questions.append(question)
        self.question_entry.delete(0, tk.END)
        self.update_questions_display()

    def remove_last_question(self):
        """Remove the last question from the list."""
        if not self.questions:
            messagebox.showinfo("No Questions", "There are no questions to remove.")
            return

        self.questions.pop()
        self.update_questions_display()

    def clear_questions(self):
        """Clear all questions."""
        if not self.questions:
            return

        if messagebox.askyesno("Clear All", "Are you sure you want to clear all questions?"):
            self.questions = []
            self.update_questions_display()

    def update_questions_display(self):
        """Update the questions display."""
        self.questions_display.config(state=tk.NORMAL)
        self.questions_display.delete(1.0, tk.END)

        if not self.questions:
            self.questions_display.insert(tk.END, "No questions added yet.")
        else:
            for i, question in enumerate(self.questions, 1):
                self.questions_display.insert(tk.END, f"{i}. {question}\n")

        self.questions_display.config(state=tk.DISABLED)

    def save_form(self):
        """Save the form to a JSON file."""
        form_name = self.form_name_entry.get().strip()

        if not form_name:
            messagebox.showwarning("No Form Name", "Please enter a form name.")
            return

        if not self.questions:
            messagebox.showwarning("No Questions", "Please add at least one question.")
            return

        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            title="Save Form As",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialfile=f"{form_name.replace(' ', '_')}.json"
        )

        if not file_path:
            return

        # Create form data structure
        form_data = {
            "form": form_name,
            "questions": self.questions
        }

        try:
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(form_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Success", f"Form saved successfully to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save form:\n{str(e)}")

    def load_form(self):
        """Load a form from a JSON file."""
        file_path = filedialog.askopenfilename(
            title="Load Form",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                form_data = json.load(f)

            # Validate form data
            if "form" not in form_data or "questions" not in form_data:
                messagebox.showerror("Invalid File", "The selected file is not a valid form file.")
                return

            # Load form name
            self.form_name_entry.delete(0, tk.END)
            self.form_name_entry.insert(0, form_data["form"])

            # Load questions
            self.questions = form_data["questions"]
            self.update_questions_display()

            messagebox.showinfo("Success", f"Form loaded successfully from:\n{file_path}")

        except json.JSONDecodeError:
            messagebox.showerror("Error", "The selected file is not a valid JSON file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load form:\n{str(e)}")


def main():
    root = tk.Tk()
    app = FormCreator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
