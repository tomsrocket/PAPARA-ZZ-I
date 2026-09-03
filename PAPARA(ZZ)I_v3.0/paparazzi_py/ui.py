"""Tk desktop interface for the PAPARA(ZZ)I Python edition."""

from __future__ import annotations

from dataclasses import replace
from math import hypot
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageDraw, ImageEnhance, ImageTk

from .analysis import export_results
from .keywords import KeywordList, color_hex
from .model import Annotation, Point, ScaleBar, Segment, UsableArea, backup_path
from .project import Project


class MainWindow:
    MIN_ZOOM = 0.05
    MAX_ZOOM = 20.0

    def __init__(self, root: tk.Tk, project: Project) -> None:
        self.root = root
        self.project = project
        self.image_paths = project.images()
        if not self.image_paths:
            raise ValueError("Im gewählten Ordner wurden keine Bilder gefunden")

        self.index = 0
        self.image: Image.Image | None = None
        self.display_image: Image.Image | None = None
        self.tk_image: ImageTk.PhotoImage | None = None
        self.annotations: list[Annotation] = []
        self.scale_bar: ScaleBar | None = None
        self.usable_area: UsableArea | None = None
        self.keywords = KeywordList(())
        self.keyword_path: Path | None = None
        self.selected_annotation: int | None = None
        self.mode = "annotate"
        self.mode_points: list[Point] = []
        self.pending_scale_metres = 0.0
        self.zoom = 1.0

        self.show_annotations = tk.BooleanVar(value=True)
        self.only_selected_keyword = tk.BooleanVar(value=False)
        self.ignore_current = tk.BooleanVar(value=False)
        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.gamma = tk.DoubleVar(value=1.0)
        self.keyword_search = tk.StringVar()
        self.status = tk.StringVar()
        self.image_counter = tk.StringVar()

        self._build_window()
        self._load_image(0)

    @property
    def image_path(self) -> Path:
        return self.image_paths[self.index]

    def _build_window(self) -> None:
        self.root.title(f"PAPARA(ZZ)I Python - {self.project.user}")
        self.root.geometry("1280x820")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self._build_menu()
        toolbar = ttk.Frame(self.root, padding=(6, 5))
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="◀ Vorheriges", command=self.previous_image).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Nächstes ▶", command=self.next_image).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(toolbar, textvariable=self.image_counter).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="100 %", command=self.actual_size).pack(side=tk.LEFT, padx=(16, 4))
        ttk.Button(toolbar, text="Einpassen", command=self.fit_image).pack(side=tk.LEFT)
        ttk.Checkbutton(
            toolbar,
            text="Annotationen anzeigen",
            variable=self.show_annotations,
            command=self.redraw,
        ).pack(side=tk.LEFT, padx=12)
        ttk.Button(toolbar, text="PNG exportieren", command=lambda: self.export_view("PNG")).pack(
            side=tk.RIGHT
        )
        ttk.Button(toolbar, text="JPG exportieren", command=lambda: self.export_view("JPG")).pack(
            side=tk.RIGHT, padx=4
        )

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(body, padding=8, width=270)
        viewer = ttk.Frame(body)
        body.add(left, weight=0)
        body.add(viewer, weight=1)
        self._build_sidebar(left)
        self._build_viewer(viewer)

        status_bar = ttk.Label(self.root, textvariable=self.status, anchor=tk.W, padding=(7, 4))
        status_bar.pack(fill=tk.X)

        self.root.bind("<Left>", lambda _event: self.previous_image())
        self.root.bind("<Right>", lambda _event: self.next_image())
        self.root.bind("<Delete>", lambda _event: self.delete_selected())
        self.root.bind("<Escape>", lambda _event: self.cancel_mode())

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Keyword-Datei laden…", command=self.load_keywords)
        file_menu.add_command(label="Ergebnisse exportieren", command=self.export_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.destroy)
        menu.add_cascade(label="Datei", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Keyword in allen Bildern ersetzen…", command=self.batch_replace_keyword)
        menu.add_cascade(label="Bearbeiten", menu=edit_menu)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Kurzhilfe", command=self.show_help)
        help_menu.add_command(label="Über", command=self.show_about)
        menu.add_cascade(label="Hilfe", menu=help_menu)
        self.root.configure(menu=menu)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        ttk.Button(parent, text="Keyword-Datei laden…", command=self.load_keywords).pack(fill=tk.X)
        ttk.Entry(parent, textvariable=self.keyword_search).pack(fill=tk.X, pady=(7, 3))
        self.keyword_search.trace_add("write", lambda *_args: self._refresh_keyword_list())
        self.keyword_listbox = tk.Listbox(parent, exportselection=False, activestyle="dotbox")
        self.keyword_listbox.pack(fill=tk.BOTH, expand=True)
        self.keyword_listbox.bind("<<ListboxSelect>>", lambda _event: self._keyword_changed())
        ttk.Checkbutton(
            parent,
            text="Nur gewähltes Keyword anzeigen",
            variable=self.only_selected_keyword,
            command=self.redraw,
        ).pack(anchor=tk.W, pady=(4, 10))

        actions = ttk.LabelFrame(parent, text="Werkzeuge", padding=6)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Annotieren", command=lambda: self.set_mode("annotate")).pack(fill=tk.X)
        ttk.Button(actions, text="Auswahl umbenennen", command=self.rename_selected).pack(
            fill=tk.X, pady=(3, 0)
        )
        ttk.Button(actions, text="Auswahl löschen", command=self.delete_selected).pack(
            fill=tk.X, pady=(3, 8)
        )
        ttk.Button(actions, text="Länge/Breite messen", command=self.start_measurement).pack(fill=tk.X)
        ttk.Button(actions, text="Maßstab zeichnen", command=self.start_scale).pack(fill=tk.X, pady=(3, 0))
        ttk.Button(actions, text="Nutzbares Rechteck", command=lambda: self.set_mode("rectangle")).pack(
            fill=tk.X, pady=(3, 0)
        )
        ttk.Button(actions, text="Nutzbares Polygon", command=self.start_polygon).pack(
            fill=tk.X, pady=(3, 0)
        )
        ttk.Button(actions, text="Nutzbare Fläche entfernen", command=self.remove_usable_area).pack(
            fill=tk.X, pady=(3, 8)
        )
        self.ignore_button = ttk.Checkbutton(
            actions,
            text="Bild als unbrauchbar markieren",
            variable=self.ignore_current,
            command=self.toggle_ignore,
        )
        self.ignore_button.pack(anchor=tk.W)
        ttk.Button(actions, text="Ergebnisse exportieren", command=self.export_analysis).pack(
            fill=tk.X, pady=(8, 0)
        )

        adjustments = ttk.LabelFrame(parent, text="Nur Anzeige", padding=6)
        adjustments.pack(fill=tk.X, pady=(8, 0))
        self._add_slider(adjustments, "Helligkeit", self.brightness, 0.3, 2.0)
        self._add_slider(adjustments, "Kontrast", self.contrast, 0.3, 2.0)
        self._add_slider(adjustments, "Gamma", self.gamma, 0.3, 3.0)
        ttk.Button(adjustments, text="Zurücksetzen", command=self.reset_adjustments).pack(fill=tk.X)

    def _add_slider(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.DoubleVar,
        minimum: float,
        maximum: float,
    ) -> None:
        ttk.Label(parent, text=label).pack(anchor=tk.W)
        ttk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            variable=variable,
            command=lambda _value: self._adjustment_changed(),
        ).pack(fill=tk.X)

    def _build_viewer(self, parent: ttk.Frame) -> None:
        self.canvas = tk.Canvas(parent, background="#303030", highlightthickness=0)
        vertical = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.canvas.yview)
        horizontal = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self._canvas_left_click)
        self.canvas.bind("<Shift-Button-1>", self._canvas_shift_click)
        self.canvas.bind("<Button-3>", self._canvas_right_click)
        self.canvas.bind("<MouseWheel>", self._mouse_wheel)
        self.canvas.bind("<Button-4>", lambda event: self._zoom_at(event.x, event.y, 1.15))
        self.canvas.bind("<Button-5>", lambda event: self._zoom_at(event.x, event.y, 1 / 1.15))
        self.canvas.bind("<ButtonPress-2>", lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind("<B2-Motion>", lambda event: self.canvas.scan_dragto(event.x, event.y, gain=1))
        self.canvas.bind("<Configure>", self._first_fit)

    def _load_image(self, index: int) -> None:
        self.index = index % len(self.image_paths)
        try:
            with Image.open(self.image_path) as source:
                self.image = source.convert("RGB")
        except Exception as error:
            messagebox.showerror("Bildfehler", f"{self.image_path.name} konnte nicht geladen werden:\n{error}")
            return
        try:
            self.annotations = self.project.load_annotations(self.image_path)
            self.scale_bar = self.project.load_scale(self.image_path)
            self.usable_area = self.project.load_usable_area(self.image_path)
        except ValueError as error:
            messagebox.showerror("Ungültige PAPARA-Datei", str(error))
            self.annotations = []
            self.scale_bar = None
            self.usable_area = None
        self.selected_annotation = None
        self.mode = "annotate"
        self.mode_points = []
        self.ignore_current.set(self.image_path.name in self.project.ignored_images())
        self.image_counter.set(f"Bild {self.index + 1} / {len(self.image_paths)}: {self.image_path.name}")
        self.reset_adjustments(redraw=False)
        self.zoom = 1.0
        self.root.after_idle(self.fit_image)
        self._set_status("Keyword wählen und ins Bild klicken. Rechtsklick löscht eine Markierung.")

    def previous_image(self) -> None:
        self._load_image(self.index - 1)

    def next_image(self) -> None:
        self._load_image(self.index + 1)

    def actual_size(self) -> None:
        self.zoom = 1.0
        self.redraw()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def fit_image(self) -> None:
        if self.image is None:
            return
        width = max(1, self.canvas.winfo_width() - 4)
        height = max(1, self.canvas.winfo_height() - 4)
        self.zoom = max(self.MIN_ZOOM, min(width / self.image.width, height / self.image.height, 1.0))
        self.redraw()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _first_fit(self, _event: tk.Event) -> None:
        if self.tk_image is None:
            self.fit_image()

    def redraw(self) -> None:
        if self.image is None:
            return
        self.canvas.delete("all")
        self.display_image = self._adjusted_image()
        size = (
            max(1, round(self.display_image.width * self.zoom)),
            max(1, round(self.display_image.height * self.zoom)),
        )
        resized = self.display_image.resize(size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW, tags=("base-image",))
        self.canvas.configure(scrollregion=(0, 0, size[0], size[1]))
        self._draw_overlays()

    def _adjusted_image(self) -> Image.Image:
        assert self.image is not None
        result = ImageEnhance.Brightness(self.image).enhance(self.brightness.get())
        result = ImageEnhance.Contrast(result).enhance(self.contrast.get())
        gamma = self.gamma.get()
        if abs(gamma - 1.0) > 0.01:
            lookup = [round(255 * ((value / 255) ** (1 / gamma))) for value in range(256)]
            result = result.point(lookup * 3)
        return result

    def _draw_overlays(self) -> None:
        if self.usable_area is not None:
            coordinates = [coordinate * self.zoom for p in self.usable_area.points for coordinate in (p.x, p.y)]
            self.canvas.create_polygon(*coordinates, outline="white", fill="", width=2, tags=("overlay",))
        if self.scale_bar is not None:
            self._canvas_segment(self.scale_bar.start, self.scale_bar.end, "#00e050", 2)
            self._canvas_circle(self.scale_bar.start, "#00e050", 4, fill="#00e050")
            self._canvas_circle(self.scale_bar.end, "#00e050", 4, fill="#00e050")
        if self.ignore_current.get() and self.image is not None:
            self.canvas.create_line(0, 0, self.image.width * self.zoom, self.image.height * self.zoom, fill="black", width=5)
            self.canvas.create_line(self.image.width * self.zoom, 0, 0, self.image.height * self.zoom, fill="black", width=5)
        if not self.show_annotations.get():
            return
        selected_keyword = self.current_keyword()
        for index, annotation in enumerate(self.annotations):
            if self.only_selected_keyword.get() and selected_keyword and annotation.keyword != selected_keyword:
                continue
            color = color_hex(self.keywords.color_for(annotation.keyword))
            if index == self.selected_annotation:
                color = "#ff3030"
            self._canvas_circle(annotation.point, color, 6, fill="")
            if annotation.length is not None:
                self._canvas_segment(annotation.length.start, annotation.length.end, "#00ffff", 2)
                self._canvas_circle(annotation.length.start, "#00ffff", 3, fill="#00ffff")
            if annotation.width is not None:
                self._canvas_segment(annotation.width.start, annotation.width.end, "#4080ff", 2)
        if self.mode_points:
            for point in self.mode_points:
                self._canvas_circle(point, "#ff4040", 4, fill="#ff4040")
            if self.mode == "polygon" and len(self.mode_points) > 1:
                coordinates = [coordinate * self.zoom for p in self.mode_points for coordinate in (p.x, p.y)]
                self.canvas.create_line(*coordinates, fill="#ff4040", width=2)

    def _canvas_circle(self, point: Point, color: str, radius: int, *, fill: str) -> None:
        x, y = point.x * self.zoom, point.y * self.zoom
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=color, fill=fill, width=2)

    def _canvas_segment(self, start: Point, end: Point, color: str, width: int) -> None:
        self.canvas.create_line(
            start.x * self.zoom,
            start.y * self.zoom,
            end.x * self.zoom,
            end.y * self.zoom,
            fill=color,
            width=width,
        )

    def _event_point(self, event: tk.Event) -> Point:
        return Point(self.canvas.canvasx(event.x) / self.zoom, self.canvas.canvasy(event.y) / self.zoom)

    def _inside_image(self, point: Point) -> bool:
        return self.image is not None and 0 <= point.x <= self.image.width and 0 <= point.y <= self.image.height

    def _nearest_annotation(self, point: Point) -> int | None:
        if not self.annotations:
            return None
        index, distance = min(
            enumerate(self.annotations),
            key=lambda item: hypot(item[1].point.x - point.x, item[1].point.y - point.y),
        )
        return index if distance <= 9 / self.zoom else None

    def _canvas_left_click(self, event: tk.Event) -> None:
        point = self._event_point(event)
        if not self._inside_image(point):
            return
        if self.mode == "annotate":
            nearby = self._nearest_annotation(point)
            if nearby is not None:
                self.selected_annotation = nearby
                self._set_status(f"Ausgewählt: {self.annotations[nearby].keyword}")
                self.redraw()
                return
            keyword = self.current_keyword()
            if not keyword:
                messagebox.showinfo("Keyword fehlt", "Bitte zuerst eine Keyword-Datei laden und ein Keyword wählen.")
                return
            self.annotations.append(Annotation(point, keyword))
            self.project.save_annotations(self.image_path, self.annotations)
            self.selected_annotation = len(self.annotations) - 1
            self._set_status(f"Gespeichert: {keyword}")
            self.redraw()
            return
        self._tool_click(point)

    def _canvas_shift_click(self, event: tk.Event) -> str:
        point = self._event_point(event)
        nearby = self._nearest_annotation(point)
        if nearby is not None:
            self.selected_annotation = nearby
            self.rename_selected()
        return "break"

    def _canvas_right_click(self, event: tk.Event) -> None:
        if self.mode == "polygon":
            self.finish_polygon()
            return
        point = self._event_point(event)
        nearby = self._nearest_annotation(point)
        if nearby is not None:
            self.selected_annotation = nearby
            self.delete_selected()

    def _tool_click(self, point: Point) -> None:
        self.mode_points.append(point)
        if self.mode == "scale" and len(self.mode_points) == 2:
            self.scale_bar = ScaleBar(self.mode_points[0], self.mode_points[1], self.pending_scale_metres)
            self.project.save_scale(self.image_path, self.scale_bar)
            self.cancel_mode("Maßstab gespeichert.")
        elif self.mode == "rectangle" and len(self.mode_points) == 2:
            self.usable_area = UsableArea.rectangle(*self.mode_points)
            self.project.save_usable_area(self.image_path, self.usable_area)
            self.cancel_mode("Nutzbares Rechteck gespeichert.")
        elif self.mode == "measure_length" and len(self.mode_points) == 2:
            assert self.selected_annotation is not None
            segment = Segment(*self.mode_points)
            self.annotations[self.selected_annotation] = replace(
                self.annotations[self.selected_annotation], length=segment, width=None
            )
            self.project.save_annotations(self.image_path, self.annotations)
            if messagebox.askyesno("Breite messen", "Soll zusätzlich eine Breite gemessen werden?"):
                self.mode = "measure_width"
                self.mode_points = []
                self._set_status("Breite: zwei Punkte anklicken. Esc bricht ab.")
            else:
                self.cancel_mode("Längenmessung gespeichert.")
        elif self.mode == "measure_width" and len(self.mode_points) == 2:
            assert self.selected_annotation is not None
            self.annotations[self.selected_annotation] = replace(
                self.annotations[self.selected_annotation], width=Segment(*self.mode_points)
            )
            self.project.save_annotations(self.image_path, self.annotations)
            self.cancel_mode("Längen- und Breitenmessung gespeichert.")
        self.redraw()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.mode_points = []
        messages = {
            "annotate": "Annotieren: Keyword wählen und ins Bild klicken.",
            "rectangle": "Nutzbares Rechteck: zwei gegenüberliegende Ecken anklicken.",
        }
        self._set_status(messages.get(mode, mode))
        self.redraw()

    def start_scale(self) -> None:
        value = simpledialog.askfloat(
            "Maßstab",
            "Reale Länge des Maßstabs in Metern:",
            parent=self.root,
            minvalue=0.000001,
        )
        if value is None:
            return
        self.pending_scale_metres = value
        self.set_mode("scale")
        self._set_status("Maßstab: Anfang und Ende der bekannten Strecke anklicken.")

    def start_measurement(self) -> None:
        if self.selected_annotation is None:
            messagebox.showinfo("Keine Auswahl", "Bitte zuerst einen Annotationskreis auswählen.")
            return
        self.set_mode("measure_length")
        self._set_status("Länge: zuerst Vorderseite, dann Rückseite anklicken.")

    def start_polygon(self) -> None:
        self.set_mode("polygon")
        self._set_status("Polygonpunkte anklicken; Rechtsklick schließt und speichert das Polygon.")

    def finish_polygon(self) -> None:
        if len(self.mode_points) < 3:
            messagebox.showinfo("Polygon", "Ein Polygon benötigt mindestens drei Punkte.")
            return
        self.usable_area = UsableArea("polygon", tuple(self.mode_points))
        self.project.save_usable_area(self.image_path, self.usable_area)
        self.cancel_mode("Nutzbares Polygon gespeichert.")

    def cancel_mode(self, status: str = "Werkzeug abgebrochen.") -> None:
        self.mode = "annotate"
        self.mode_points = []
        self._set_status(status)
        self.redraw()

    def remove_usable_area(self) -> None:
        if self.usable_area is None:
            return
        if not messagebox.askyesno("Nutzbare Fläche", "Nutzbare Fläche für dieses Bild entfernen?"):
            return
        path = self.project.usable_area_file(self.image_path)
        if path.exists():
            shutil.copy2(path, backup_path(path))
            path.unlink()
        self.usable_area = None
        self.redraw()

    def batch_replace_keyword(self) -> None:
        old = simpledialog.askstring(
            "Keyword ersetzen",
            "Bisheriges Keyword:",
            initialvalue=self.current_keyword() or "",
            parent=self.root,
        )
        if not old:
            return
        new = simpledialog.askstring(
            "Keyword ersetzen",
            "Neues Keyword:",
            parent=self.root,
        )
        if not new or new == old:
            return
        if not messagebox.askyesno(
            "Keyword ersetzen",
            f"„{old}“ in allen Annotationsdateien durch „{new}“ ersetzen?\n\n"
            "Vorherige Dateistände werden als .bak gesichert.",
        ):
            return
        try:
            annotations, files = self.project.replace_keyword(old, new)
            self.annotations = self.project.load_annotations(self.image_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Keyword ersetzen", str(error))
            return
        self.selected_annotation = None
        self.redraw()
        messagebox.showinfo(
            "Keyword ersetzt",
            f"{annotations} Annotation(en) in {files} Datei(en) wurden geändert.",
        )

    def delete_selected(self) -> None:
        if self.selected_annotation is None:
            return
        annotation = self.annotations[self.selected_annotation]
        if not messagebox.askyesno("Annotation löschen", f"Annotation „{annotation.keyword}“ löschen?"):
            return
        del self.annotations[self.selected_annotation]
        self.selected_annotation = None
        self.project.save_annotations(self.image_path, self.annotations)
        self._set_status("Annotation gelöscht.")
        self.redraw()

    def rename_selected(self) -> None:
        if self.selected_annotation is None:
            messagebox.showinfo("Keine Auswahl", "Bitte zuerst einen Annotationskreis auswählen.")
            return
        keyword = self.current_keyword()
        if not keyword:
            messagebox.showinfo("Keyword fehlt", "Bitte ein neues Keyword auswählen.")
            return
        current = self.annotations[self.selected_annotation]
        self.annotations[self.selected_annotation] = current.renamed(keyword)
        self.project.save_annotations(self.image_path, self.annotations)
        self._set_status(f"Annotation in „{keyword}“ umbenannt.")
        self.redraw()

    def toggle_ignore(self) -> None:
        self.project.set_ignored(self.image_path, self.ignore_current.get())
        self.redraw()

    def load_keywords(self) -> None:
        filename = filedialog.askopenfilename(
            title="Keyword-Datei öffnen",
            filetypes=(("Textdateien", "*.txt"), ("Alle Dateien", "*.*")),
        )
        if not filename:
            return
        try:
            self.keyword_path = Path(filename)
            self.keywords = KeywordList.load(self.keyword_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Keyword-Datei", str(error))
            return
        self._refresh_keyword_list()
        self._set_status(f"Keyword-Datei geladen: {self.keyword_path.name}")
        self.redraw()

    def _refresh_keyword_list(self) -> None:
        search = self.keyword_search.get().strip().casefold()
        self.keyword_listbox.delete(0, tk.END)
        self._visible_keywords = []
        for entry in self.keywords.entries:
            if search and search not in entry.name.casefold():
                continue
            self.keyword_listbox.insert(tk.END, entry.name)
            index = self.keyword_listbox.size() - 1
            self._visible_keywords.append(entry)
            if not entry.selectable:
                self.keyword_listbox.itemconfig(index, foreground="#777777")
            else:
                color = color_hex(self.keywords.color_for(entry.name))
                self.keyword_listbox.itemconfig(index, foreground=color)
        first = next((index for index, entry in enumerate(self._visible_keywords) if entry.selectable), None)
        if first is not None:
            self.keyword_listbox.selection_set(first)

    def _keyword_changed(self) -> None:
        selection = self.keyword_listbox.curselection()
        if selection and not self._visible_keywords[selection[0]].selectable:
            self.keyword_listbox.selection_clear(selection[0])
        self.redraw()

    def current_keyword(self) -> str | None:
        selection = self.keyword_listbox.curselection()
        if not selection or not hasattr(self, "_visible_keywords"):
            return None
        entry = self._visible_keywords[selection[0]]
        return entry.name if entry.selectable else None

    def _adjustment_changed(self) -> None:
        if hasattr(self, "canvas"):
            self.redraw()

    def reset_adjustments(self, *, redraw: bool = True) -> None:
        self.brightness.set(1.0)
        self.contrast.set(1.0)
        self.gamma.set(1.0)
        if redraw:
            self.redraw()

    def _mouse_wheel(self, event: tk.Event) -> None:
        self._zoom_at(event.x, event.y, 1.15 if event.delta > 0 else 1 / 1.15)

    def _zoom_at(self, x: int, y: int, factor: float) -> None:
        if self.image is None:
            return
        old_zoom = self.zoom
        memory_safe_zoom = 12000 / max(self.image.width, self.image.height)
        new_zoom = max(
            self.MIN_ZOOM,
            min(self.MAX_ZOOM, max(1.0, memory_safe_zoom), old_zoom * factor),
        )
        if new_zoom == old_zoom:
            return
        image_x = self.canvas.canvasx(x) / old_zoom
        image_y = self.canvas.canvasy(y) / old_zoom
        self.zoom = new_zoom
        self.redraw()
        total_width = self.image.width * new_zoom
        total_height = self.image.height * new_zoom
        if total_width > self.canvas.winfo_width():
            self.canvas.xview_moveto(max(0, (image_x * new_zoom - x) / total_width))
        if total_height > self.canvas.winfo_height():
            self.canvas.yview_moveto(max(0, (image_y * new_zoom - y) / total_height))

    def export_view(self, image_format: str) -> None:
        if self.display_image is None:
            return
        x0 = max(0, int(self.canvas.canvasx(0) / self.zoom))
        y0 = max(0, int(self.canvas.canvasy(0) / self.zoom))
        x1 = min(self.display_image.width, int(self.canvas.canvasx(self.canvas.winfo_width()) / self.zoom))
        y1 = min(self.display_image.height, int(self.canvas.canvasy(self.canvas.winfo_height()) / self.zoom))
        if x1 <= x0 or y1 <= y0:
            x0, y0, x1, y1 = 0, 0, self.display_image.width, self.display_image.height
        exported = self.display_image.crop((x0, y0, x1, y1))
        draw = ImageDraw.Draw(exported)
        offset = Point(x0, y0)
        if self.usable_area is not None:
            draw.polygon(
                [(p.x - offset.x, p.y - offset.y) for p in self.usable_area.points],
                outline="white",
                width=2,
            )
        if self.scale_bar is not None:
            draw.line(
                (
                    self.scale_bar.start.x - x0,
                    self.scale_bar.start.y - y0,
                    self.scale_bar.end.x - x0,
                    self.scale_bar.end.y - y0,
                ),
                fill="#00e050",
                width=2,
            )
        if self.show_annotations.get():
            selected_keyword = self.current_keyword()
            for annotation in self.annotations:
                if self.only_selected_keyword.get() and selected_keyword and annotation.keyword != selected_keyword:
                    continue
                color = color_hex(self.keywords.color_for(annotation.keyword))
                x, y, radius = annotation.point.x - x0, annotation.point.y - y0, 7
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=color, width=2)
                if annotation.length:
                    draw.line(
                        (
                            annotation.length.start.x - x0,
                            annotation.length.start.y - y0,
                            annotation.length.end.x - x0,
                            annotation.length.end.y - y0,
                        ),
                        fill="#00ffff",
                        width=2,
                    )
                if annotation.width:
                    draw.line(
                        (
                            annotation.width.start.x - x0,
                            annotation.width.start.y - y0,
                            annotation.width.end.x - x0,
                            annotation.width.end.y - y0,
                        ),
                        fill="#4080ff",
                        width=2,
                    )
        self.project.exported_images_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".png" if image_format == "PNG" else ".jpg"
        path = self.project.exported_images_dir / f"{self.image_path.stem}{suffix}"
        if image_format == "JPG":
            exported.save(path, "JPEG", quality=95)
        else:
            exported.save(path, "PNG")
        messagebox.showinfo("Export fertig", f"Bild gespeichert unter:\n{path}")

    def export_analysis(self) -> None:
        try:
            path = export_results(self.project)
        except Exception as error:
            messagebox.showerror("Exportfehler", str(error))
            return
        messagebox.showinfo("Export fertig", f"Ergebnisse gespeichert unter:\n{path}")

    def _set_status(self, text: str) -> None:
        self.status.set(f"{text}  |  Modus: {self.mode}")

    def show_help(self) -> None:
        messagebox.showinfo(
            "Kurzhilfe",
            "Linksklick ins Bild setzt eine Annotation. Ein Klick auf einen Kreis wählt ihn aus.\n\n"
            "Umschalt+Klick benennt einen Kreis mit dem aktuell gewählten Keyword um. "
            "Rechtsklick oder Entf löscht ihn.\n\n"
            "Das Mausrad zoomt, die mittlere Maustaste verschiebt das Bild. Esc beendet ein Werkzeug.\n\n"
            "Beim Polygon beendet ein Rechtsklick die Eingabe.",
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            "Über PAPARA(ZZ)I Python",
            "PAPARA(ZZ)I Python 0.1\n\n"
            "Kompatible, freie Python-Neuentwicklung auf Basis von PAPARA(ZZ)I 3.0.\n"
            "Lizenz: GNU GPL Version 3 oder später.",
        )


def launch(image_dir: Path | None = None, user: str | None = None) -> None:
    root = tk.Tk()
    root.withdraw()
    if not user:
        user = simpledialog.askstring("PAPARA(ZZ)I", "Name der annotierenden Person:", parent=root)
    if not user:
        root.destroy()
        return
    if image_dir is None:
        selected = filedialog.askdirectory(title="Bilderordner auswählen", parent=root)
        if not selected:
            root.destroy()
            return
        image_dir = Path(selected)
    try:
        project = Project(image_dir, user)
        root.deiconify()
        MainWindow(root, project)
    except (OSError, ValueError) as error:
        messagebox.showerror("PAPARA(ZZ)I", str(error), parent=root)
        root.destroy()
        return
    root.mainloop()
