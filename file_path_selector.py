#!/usr/bin/env python3
"""
Simple GUI application to request a file path from the user.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
from outcome import process_pdf


class FilePathSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Form Processor")
        self.root.geometry("800x600")
        self.selected_file_path = None

        # Create and configure the main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Label
        label = tk.Label(main_frame, text="Select a PDF file:", font=("Arial", 12))
        label.pack(pady=(0, 10))

        # Entry field to display selected path
        self.path_entry = tk.Entry(main_frame, width=70, font=("Arial", 10))
        self.path_entry.pack(pady=(0, 10))

        # Button frame for Browse and Submit buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(0, 10))

        # Browse button
        browse_btn = tk.Button(
            button_frame,
            text="Browse",
            command=self.browse_file,
            width=12,
            font=("Arial", 10)
        )
        browse_btn.pack(side=tk.LEFT, padx=5)

        # Process button
        process_btn = tk.Button(
            button_frame,
            text="Process PDF",
            command=self.submit_path,
            width=12,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white"
        )
        process_btn.pack(side=tk.LEFT, padx=5)

        # Results label
        results_label = tk.Label(main_frame, text="Results:", font=("Arial", 12, "bold"))
        results_label.pack(pady=(10, 5), anchor=tk.W)

        # Text widget to display JSON results
        self.results_text = scrolledtext.ScrolledText(
            main_frame,
            width=90,
            height=25,
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        """Open file dialog to select a file."""
        file_path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def submit_path(self):
        """Handle the submitted file path and process the PDF."""
        file_path = self.path_entry.get()

        if not file_path:
            messagebox.showwarning("No File", "Please select a file first.")
            return

        # Store the selected path
        self.selected_file_path = file_path

        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Processing PDF, please wait...\n")
        self.root.update()

        try:
            # Process the PDF
            output_file, results = process_pdf(file_path)

            # Display results in the text widget
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Processing complete!\n")
            self.results_text.insert(tk.END, f"Output saved to: {output_file}\n\n")
            self.results_text.insert(tk.END, "="*80 + "\n")
            self.results_text.insert(tk.END, "JSON Results:\n")
            self.results_text.insert(tk.END, "="*80 + "\n\n")

            # Format and display JSON
            json_output = json.dumps(results, indent=2, ensure_ascii=False)
            self.results_text.insert(tk.END, json_output)

            messagebox.showinfo("Success", f"PDF processed successfully!\nResults saved to: {output_file}")

        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error processing PDF:\n{str(e)}")
            messagebox.showerror("Error", f"Failed to process PDF:\n{str(e)}")


def main():
    root = tk.Tk()
    app = FilePathSelector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
