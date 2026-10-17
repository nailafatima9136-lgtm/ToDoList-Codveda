"""
To-Do List Application (GUI)
------------------------------
Level 2 (Intermediate) Task 1 — GUI version

Built with tkinter (ships with standard Python, works out-of-the-box in VS Code).

Features:
- Add, view, delete, and mark tasks as done
- Persistent storage in a JSON file
- Clean, modern-looking UI/UX:
    - Color-coded task states
    - Hover effects on buttons
    - Keyboard shortcut (Enter to add task)
    - Confirmation dialog before delete
    - Status bar with live task count
    - Basic error handling with friendly message boxes
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DATA_FILE = "tasks.json"

# ---------- Color / style palette ----------
BG_COLOR = "#F4F6F8"
SIDEBAR_COLOR = "#2D3142"
ACCENT_COLOR = "#4F5D75"
DONE_COLOR = "#8BC34A"
PENDING_COLOR = "#EF6C00"
DANGER_COLOR = "#E53935"
FONT_MAIN = ("Segoe UI", 11)
FONT_HEADER = ("Segoe UI", 18, "bold")
FONT_SMALL = ("Segoe UI", 9)


class TodoStore:
    """Handles persistence — kept separate from the UI so logic stays testable."""

    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.tasks = []
        self.load()

    def load(self):
        if not os.path.exists(self.data_file):
            self.tasks = []
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                self.tasks = json.loads(content) if content else []
        except (json.JSONDecodeError, IOError):
            self.tasks = []

    def save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2)
        except IOError as e:
            messagebox.showerror("Save Error", f"Could not save tasks:\n{e}")

    def add(self, description: str):
        next_id = (max((t["id"] for t in self.tasks), default=0)) + 1
        self.tasks.append({
            "id": next_id,
            "description": description,
            "done": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.save()

    def delete(self, task_id: int):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    def toggle_done(self, task_id: int):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = not t["done"]
        self.save()


class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = TodoStore()

        self.title("To-Do List")
        self.geometry("640x520")
        self.minsize(520, 420)
        self.configure(bg=BG_COLOR)

        self._build_layout()
        self._refresh_task_list()

    # ---------- UI construction ----------

    def _build_layout(self):
        # Sidebar (branding / header area)
        sidebar = tk.Frame(self, bg=SIDEBAR_COLOR, width=160)
        sidebar.pack(side="left", fill="y")
        tk.Label(
            sidebar, text="📝", font=("Segoe UI", 40), bg=SIDEBAR_COLOR, fg="white"
        ).pack(pady=(30, 5))
        tk.Label(
            sidebar, text="My Tasks", font=FONT_HEADER, bg=SIDEBAR_COLOR, fg="white"
        ).pack()
        self.count_label = tk.Label(
            sidebar, text="", font=FONT_SMALL, bg=SIDEBAR_COLOR, fg="#B8BEC9"
        )
        self.count_label.pack(pady=(4, 0))

        # Main content area
        main = tk.Frame(self, bg=BG_COLOR)
        main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Input row
        input_row = tk.Frame(main, bg=BG_COLOR)
        input_row.pack(fill="x", pady=(0, 12))

        self.entry = tk.Entry(input_row, font=FONT_MAIN, relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.insert(0, "")
        self.entry.bind("<Return>", lambda e: self._on_add())
        self._add_entry_border(self.entry)

        add_btn = self._make_button(input_row, "+ Add", ACCENT_COLOR, self._on_add)
        add_btn.pack(side="left")

        # Scrollable task list (Canvas + Frame, since tkinter has no native scroll list of widgets)
        list_container = tk.Frame(main, bg=BG_COLOR)
        list_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_container, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.list_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=440)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Status bar
        self.status_label = tk.Label(
            main, text="", font=FONT_SMALL, bg=BG_COLOR, fg="#777", anchor="w"
        )
        self.status_label.pack(fill="x", pady=(8, 0))

    def _add_entry_border(self, entry_widget):
        entry_widget.configure(highlightbackground="#D0D5DC", highlightthickness=1)
        entry_widget.insert(0, "")
        entry_widget.config(fg="#222")

    def _make_button(self, parent, text, color, command):
        btn = tk.Button(
            parent, text=text, command=command, font=FONT_MAIN,
            bg=color, fg="white", relief="flat", padx=14, pady=6, cursor="hand2",
            activebackground=self._darken(color), activeforeground="white",
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=self._darken(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    @staticmethod
    def _darken(hex_color, factor=0.85):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = (int(c * factor) for c in (r, g, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Actions ----------

    def _on_add(self):
        description = self.entry.get().strip()
        if not description:
            messagebox.showwarning("Empty Task", "Please type a task before adding it.")
            return
        self.store.add(description)
        self.entry.delete(0, "end")
        self._refresh_task_list()

    def _on_delete(self, task_id: int, description: str):
        confirmed = messagebox.askyesno(
            "Delete Task", f"Delete this task?\n\n\"{description}\""
        )
        if confirmed:
            self.store.delete(task_id)
            self._refresh_task_list()

    def _on_toggle(self, task_id: int):
        self.store.toggle_done(task_id)
        self._refresh_task_list()

    # ---------- Rendering ----------

    def _refresh_task_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        tasks = self.store.tasks
        if not tasks:
            tk.Label(
                self.list_frame, text="No tasks yet — add one above!",
                font=FONT_MAIN, bg=BG_COLOR, fg="#999"
            ).pack(pady=30)
        else:
            for task in tasks:
                self._render_task_row(task)

        done_count = sum(1 for t in tasks if t["done"])
        total = len(tasks)
        self.count_label.config(text=f"{done_count}/{total} done" if total else "No tasks")
        self.status_label.config(
            text=f"{total} task(s) total — {done_count} completed, {total - done_count} pending"
        )

    def _render_task_row(self, task):
        row = tk.Frame(self.list_frame, bg="white", pady=8, padx=10)
        row.pack(fill="x", pady=4, padx=2)

        is_done = task["done"]
        check_symbol = "✓" if is_done else "○"
        check_color = DONE_COLOR if is_done else PENDING_COLOR

        check_btn = tk.Label(
            row, text=check_symbol, font=("Segoe UI", 14, "bold"),
            bg="white", fg=check_color, cursor="hand2", width=2
        )
        check_btn.pack(side="left")
        check_btn.bind("<Button-1>", lambda e, tid=task["id"]: self._on_toggle(tid))

        text_style = {"bg": "white", "anchor": "w", "justify": "left"}
        desc_font = FONT_MAIN if not is_done else (FONT_MAIN[0], FONT_MAIN[1], "overstrike")
        desc_color = "#999" if is_done else "#222"

        desc_frame = tk.Frame(row, bg="white")
        desc_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))

        tk.Label(
            desc_frame, text=task["description"], font=desc_font, fg=desc_color, **text_style
        ).pack(anchor="w")
        tk.Label(
            desc_frame, text=task.get("created_at", ""), font=FONT_SMALL, fg="#AAA", **text_style
        ).pack(anchor="w")

        del_btn = tk.Label(
            row, text="🗑", font=("Segoe UI", 13), bg="white", fg=DANGER_COLOR, cursor="hand2"
        )
        del_btn.pack(side="right", padx=(8, 0))
        del_btn.bind(
            "<Button-1>",
            lambda e, tid=task["id"], desc=task["description"]: self._on_delete(tid, desc)
        )


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
