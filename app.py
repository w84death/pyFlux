import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO

class App(tk.Frame):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.master.title("PyFlux")

        # Input frame
        input_frame = tk.Frame(self.master)
        input_frame.pack(pady=10)

        self.prompt_label = tk.Label(input_frame, text="Enter prompt:")
        self.prompt_label.pack(side=tk.LEFT)

        self.prompt_entry = tk.Entry(input_frame, width=50)
        self.prompt_entry.pack(side=tk.LEFT, padx=5)

        self.generate_button = tk.Button(input_frame, text="Generate", command=self.generate_image)
        self.generate_button.pack(side=tk.LEFT, padx=5)

        self.download_button = tk.Button(input_frame, text="Download Image", command=self.download_image)
        self.download_button.pack(side=tk.LEFT, padx=5)

        # Creative Generation checkbox
        self.creative_var = tk.BooleanVar()
        self.creative_checkbutton = tk.Checkbutton(
            input_frame, text="Creative Generation", variable=self.creative_var
        )
        self.creative_checkbutton.pack(side=tk.LEFT, padx=5)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(self.master)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Vertical scrollbar
        self.v_scrollbar = tk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        # Horizontal scrollbar
        self.h_scrollbar = tk.Scrollbar(self.master, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)

        self.image = None  # PIL image reference
        self.photo = None  # PhotoImage reference

        # Frame inside the canvas
        self.image_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_frame, anchor='nw')

        self.image_frame.bind("<Configure>", self.on_frame_configure)

        # Image label
        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack()

        self.image = None  # To store the PIL image

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def generate_image(self):
        prompt = self.prompt_entry.get()
        if not prompt:
            return

        # Build the payload
        payload = {
            'prompt': prompt,
            'width': 1440,
            'height': 1080,
        }
        if self.creative_var.get():
            payload['prompt_upsampling'] = True

        response = requests.post(
            'https://api.bfl.ml/v1/flux-pro-1.1',
            headers={
                'accept': 'application/json',
                'x-key': os.environ.get("BFL_API_KEY"),
                'Content-Type': 'application/json',
            },
            json=payload,
        ).json()

        request_id = response['id']

        # Polling for the result
        while True:
            result = requests.get(
                'https://api.bfl.ml/v1/get_result',
                headers={
                    'accept': 'application/json',
                    'x-key': os.environ.get("BFL_API_KEY"),
                },
                params={
                    'id': request_id,
                },
            ).json()
            if result["status"] == "Ready":
                image_url = result['result']['sample']
                self.display_image(image_url)
                break
            else:
                self.master.update()
                self.master.after(1000)

    def display_image(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = response.content
            self.image = Image.open(BytesIO(image_data))

            # Convert the PIL image to a PhotoImage
            self.photo = ImageTk.PhotoImage(self.image)

            # Clear the canvas
            self.canvas.delete("all")

            # Display the image on the canvas
            self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

            # Update the scroll region
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response Content: {response.text}")

    def download_image(self):
        if self.image:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            )
            if save_path:
                self.image.save(save_path)
        else:
            print("No image to save.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()