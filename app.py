import io
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import requests
import os

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

        # Aspect Ratio dropdown
        self.aspect_ratio_var = tk.StringVar(value="4:3")
        self.aspect_ratio_label = tk.Label(input_frame, text="Aspect Ratio:")
        self.aspect_ratio_label.pack(side=tk.LEFT, padx=5)
        self.aspect_ratio_menu = ttk.OptionMenu(
            input_frame, self.aspect_ratio_var, "4:3", "1:1", "4:3", "16:9", "21:9"
        )
        self.aspect_ratio_menu.pack(side=tk.LEFT, padx=5)

        # Canvas for displaying the image
        self.canvas = tk.Canvas(self.master)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(self.canvas)
        self.image_label.pack()

        self.image = None  # To store the PIL image
        self.photo_image = None  # To store the PhotoImage

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.image_frame.bbox("all"))

    def generate_image(self):
        prompt = self.prompt_entry.get()
        if not prompt:
            return

        aspect_ratio = self.aspect_ratio_var.get()

        # Build the payload
        payload = {
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
            'output_format': 'png',
            'width': '2368',
            'height': '1792',
        }
        response = requests.post(
            'https://api.bfl.ml/v1/flux-pro-1.1-ultra',
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
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))

        # Resize the image to fit the window while maintaining aspect ratio
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        image.thumbnail((window_width, window_height), Image.LANCZOS)

        self.image = image  # Store the original PIL image
        self.photo_image = ImageTk.PhotoImage(image)
        self.image_label.config(image=self.photo_image)
        self.image_label.image = self.photo_image

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
    app = App(master=root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()