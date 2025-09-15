import tkinter as tk
from tkinter import scrolledtext
import time

def save_message(sender, message):
    with open("chat.txt", "a", encoding="utf-8") as f:
        f.write(f"{sender}|{message}\n")

def load_messages():
    messages = []
    try:
        with open("chat.txt", "r", encoding="utf-8") as f:
            for line in f:
                sender, msg = line.strip().split("|", 1)
                messages.append((sender, msg))
    except FileNotFoundError:
        pass
    return messages

def refresh_chat():
    chat_box.config(state=tk.NORMAL)
    chat_box.delete(1.0, tk.END)
    for sender, msg in load_messages():
        chat_box.insert(tk.END, f"{sender}: {msg}\n")
    chat_box.config(state=tk.DISABLED)

def send_message():
    msg = msg_entry.get()
    if msg.strip():
        save_message("Me", msg)
        msg_entry.delete(0, tk.END)
        refresh_chat()

root = tk.Tk()
root.title("Mini WhatsApp")

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20, state=tk.DISABLED)
chat_box.pack(padx=10, pady=10)

msg_entry = tk.Entry(root, width=40)
msg_entry.pack(side=tk.LEFT, padx=10, pady=10)

send_btn = tk.Button(root, text="Send", command=send_message)
send_btn.pack(side=tk.LEFT, padx=5)

refresh_btn = tk.Button(root, text="Refresh", command=refresh_chat)
refresh_btn.pack(side=tk.LEFT)

refresh_chat()
root.mainloop()
