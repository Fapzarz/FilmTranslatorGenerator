import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES # Import DND_FILES
from gui.components import create_progress_frame, create_notebook # Added create_notebook
from config import (
    SUBTITLE_FONTS, SUBTITLE_COLORS, SUBTITLE_SIZES, SUBTITLE_POSITIONS,
    SUBTITLE_OUTLINE_COLORS, SUBTITLE_OUTLINE_WIDTHS, SUBTITLE_BG_COLORS, SUBTITLE_BG_OPACITY,
    TRANSLATION_PROVIDERS, LANGUAGES, OUTPUT_FORMATS, # Added for right pane
    WHISPER_MODELS, DEVICES, GEMINI_MODELS, OPENAI_MODELS, ANTHROPIC_MODELS, DEEPSEEK_MODEL # Added for right pane
)
from gui import queue_manager # Import queue_manager
from gui import video_processor # Import video_processor
from gui import subtitle_styler # Import subtitle_styler
from gui import editor_manager # Import editor_manager

def create_left_pane(app, parent_container):
    """Creates the left pane of the application, containing queue management and subtitle styling."""
    left_pane_container = ttk.Frame(parent_container, padding="5")
    left_pane_container.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

    # --- Queue control panel ---
    queue_control_panel = ttk.LabelFrame(left_pane_container, text="File Queue & Processing", padding="10")
    queue_control_panel.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    # Queue management frame
    queue_management_frame = ttk.Frame(queue_control_panel)
    queue_management_frame.pack(fill=tk.X, padx=5, pady=5)

    # Listbox for video queue
    app.video_listbox = tk.Listbox(queue_management_frame, height=8, selectmode=tk.SINGLE)
    app.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5), pady=5)
    app.video_listbox.bind('<<ListboxSelect>>', lambda event: queue_manager.on_video_select_in_queue(app, event))

    # --- Drag and Drop Setup ---
    # The DND_FILES constant indicates that the widget should accept dropped files.
    app.video_listbox.drop_target_register(DND_FILES)
    # Bind the <<Drop>> event to the handler method in AppGUI
    app.video_listbox.dnd_bind('<<Drop>>', lambda e: app._handle_drop_files(e))
    # --- End Drag and Drop Setup ---

    # Scrollbar for listbox
    listbox_scrollbar = ttk.Scrollbar(queue_management_frame, orient=tk.VERTICAL, command=app.video_listbox.yview)
    listbox_scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=5)
    app.video_listbox.config(yscrollcommand=listbox_scrollbar.set)

    # Queue buttons
    queue_buttons_frame = ttk.Frame(queue_management_frame)
    queue_buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5,0), pady=5)

    add_button = ttk.Button(queue_buttons_frame, text="Add Video(s)", command=lambda: queue_manager.add_videos_to_queue(app))
    add_button.pack(fill=tk.X, pady=2)
    remove_button = ttk.Button(queue_buttons_frame, text="Remove Selected", command=lambda: queue_manager.remove_selected_video_from_queue(app))
    remove_button.pack(fill=tk.X, pady=2)
    clear_button = ttk.Button(queue_buttons_frame, text="Clear Queue", command=lambda: queue_manager.clear_video_queue(app))
    clear_button.pack(fill=tk.X, pady=2)

    # Progress and action frame (using create_progress_frame from components)
    # It returns the frame, progress_bar, progress_status, and generate_button
    progress_action_frame, app.progress_bar, app.progress_status, app.generate_button = create_progress_frame(
        queue_control_panel, lambda: video_processor.start_processing(app)
    )

    # --- Queue Statistics Frame ---
    stats_frame = ttk.LabelFrame(queue_control_panel, text="Queue Statistics", padding="5")
    stats_frame.pack(fill=tk.X, padx=5, pady=(5,0))

    ttk.Label(stats_frame, textvariable=app.stat_total_files).pack(anchor='w', padx=5)
    ttk.Label(stats_frame, textvariable=app.stat_processed_files).pack(anchor='w', padx=5)
    ttk.Label(stats_frame, textvariable=app.stat_pending_files).pack(anchor='w', padx=5)
    ttk.Label(stats_frame, textvariable=app.stat_failed_files).pack(anchor='w', padx=5)

    # Pack progress_action_frame below stats_frame
    progress_action_frame.pack(fill=tk.X, padx=5, pady=(5,5))
    
    # --- Subtitle Style Editor Panel ---
    subtitle_style_panel = ttk.LabelFrame(left_pane_container, text="Subtitle Style Editor", padding="10")
    subtitle_style_panel.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)

    style_settings_frame = ttk.Frame(subtitle_style_panel)
    style_settings_frame.pack(fill=tk.X, padx=5, pady=5)

    # Font settings
    font_frame = ttk.Frame(style_settings_frame)
    font_frame.pack(fill=tk.X, pady=5)
    ttk.Label(font_frame, text="Font:", width=10).pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.font_combobox = ttk.Combobox(font_frame, textvariable=app.subtitle_font_var, 
                                      values=SUBTITLE_FONTS, state="readonly", width=18)
    app.font_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    app.font_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    # Font size and color in same row
    size_color_frame = ttk.Frame(style_settings_frame)
    size_color_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(size_color_frame, text="Size:", width=10).pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.size_combobox = ttk.Combobox(size_color_frame, textvariable=app.subtitle_size_var, 
                                     values=SUBTITLE_SIZES, state="readonly", width=6)
    app.size_combobox.pack(side=tk.LEFT, padx=5)
    app.size_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    ttk.Label(size_color_frame, text="Color:", width=6).pack(side=tk.LEFT, padx=(10,5), anchor='w')
    app.color_combobox = ttk.Combobox(size_color_frame, textvariable=app.subtitle_color_var, 
                                      values=SUBTITLE_COLORS, state="readonly", width=10)
    app.color_combobox.pack(side=tk.LEFT, padx=5)
    app.color_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    # Position
    position_frame = ttk.Frame(style_settings_frame)
    position_frame.pack(fill=tk.X, pady=5)
    ttk.Label(position_frame, text="Position:", width=10).pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.position_combobox = ttk.Combobox(position_frame, textvariable=app.subtitle_position_var, 
                                         values=SUBTITLE_POSITIONS, state="readonly", width=10)
    app.position_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    app.position_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    # Outline settings
    outline_frame = ttk.Frame(style_settings_frame)
    outline_frame.pack(fill=tk.X, pady=5)
    ttk.Label(outline_frame, text="Outline:", width=10).pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.outline_width_combobox = ttk.Combobox(outline_frame, textvariable=app.subtitle_outline_width_var, 
                                              values=SUBTITLE_OUTLINE_WIDTHS, state="readonly", width=6)
    app.outline_width_combobox.pack(side=tk.LEFT, padx=5)
    app.outline_width_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    ttk.Label(outline_frame, text="Color:", width=6).pack(side=tk.LEFT, padx=(10,5), anchor='w')
    app.outline_color_combobox = ttk.Combobox(outline_frame, textvariable=app.subtitle_outline_color_var, 
                                              values=SUBTITLE_OUTLINE_COLORS, state="readonly", width=10)
    app.outline_color_combobox.pack(side=tk.LEFT, padx=5)
    app.outline_color_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    # Background settings
    bg_frame = ttk.Frame(style_settings_frame)
    bg_frame.pack(fill=tk.X, pady=5)
    ttk.Label(bg_frame, text="Background:", width=10).pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.bg_color_combobox = ttk.Combobox(bg_frame, textvariable=app.subtitle_bg_color_var, 
                                         values=SUBTITLE_BG_COLORS, state="readonly", width=12)
    app.bg_color_combobox.pack(side=tk.LEFT, padx=5)
    app.bg_color_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    ttk.Label(bg_frame, text="Opacity:", width=8).pack(side=tk.LEFT, padx=(10,5), anchor='w')
    app.bg_opacity_combobox = ttk.Combobox(bg_frame, textvariable=app.subtitle_bg_opacity_var, 
                                           values=SUBTITLE_BG_OPACITY, state="readonly", width=6)
    app.bg_opacity_combobox.pack(side=tk.LEFT, padx=5)
    app.bg_opacity_combobox.bind("<<ComboboxSelected>>", lambda event: (subtitle_styler.refresh_subtitle_style_preview(app, event), app._restore_video_preview_if_selected()))
    
    # Subtitle preview frame
    preview_style_frame = ttk.LabelFrame(subtitle_style_panel, text="Style Preview", padding="10") # Renamed for clarity
    preview_style_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    app.preview_canvas = tk.Canvas(preview_style_frame, bg="black", height=100, width=300)
    app.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    app.preview_canvas.create_text(
        150, 50, text="Sample Subtitle Text", fill="white", font=("Arial", 14), anchor="center"
    )
    app.preview_canvas.bind("<Configure>", lambda event: subtitle_styler.refresh_subtitle_style_preview(app, event))

    # Apply Style button
    apply_style_frame = ttk.Frame(subtitle_style_panel)
    apply_style_frame.pack(fill=tk.X, padx=5, pady=5)
    
    app.apply_style_button = ttk.Button(apply_style_frame, text="Apply Style", 
                                       command=lambda: subtitle_styler.apply_and_save_subtitle_style(app), style="Accent.TButton")
    app.apply_style_button.pack(side=tk.RIGHT, padx=5)

    return left_pane_container 

def create_right_pane(app, parent_container):
    """Creates the right pane of the application, containing settings, preview, and the main notebook."""
    right_pane_container = ttk.Frame(parent_container, padding="5")
    right_pane_container.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

    # --- RIGHT PANE COMPONENTS ---
    top_right_settings_area = ttk.Frame(right_pane_container)
    top_right_settings_area.pack(fill=tk.X, pady=(0,5))

    # Panel: Selected Item Preview & Global Settings
    settings_preview_panel = ttk.LabelFrame(top_right_settings_area, text="Preview & Translation Setup", padding="10")
    settings_preview_panel.pack(fill=tk.X, padx=2, pady=2)
    
    preview_sub_panel = ttk.LabelFrame(settings_preview_panel, text="Selected Video Preview", padding="5")
    preview_sub_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, ipadx=5, ipady=5)
    
    app.thumbnail_label = ttk.Label(preview_sub_panel) 
    app.thumbnail_label.pack(pady=5, padx=5)
    app.thumbnail_placeholder = ttk.Label(preview_sub_panel, text="Select a video from queue") 
    app.thumbnail_placeholder.pack(pady=5, padx=5)
    
    app.video_info_frame = ttk.Frame(preview_sub_panel) 
    app.video_info_frame.pack(fill=tk.X, padx=5, pady=5)
    app.video_duration_label = ttk.Label(app.video_info_frame, text="Duration: N/A")
    app.video_duration_label.pack(side=tk.LEFT, padx=5)
    app.video_size_label = ttk.Label(app.video_info_frame, text="Size: N/A")
    app.video_size_label.pack(side=tk.LEFT, padx=20)
    
    translation_settings_sub_panel = ttk.Frame(settings_preview_panel, padding="5")
    translation_settings_sub_panel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

    # --- Translation Provider Selection ---
    provider_selection_frame = ttk.Frame(translation_settings_sub_panel)
    provider_selection_frame.pack(fill=tk.X, padx=5, pady=3)
    ttk.Label(provider_selection_frame, text="Provider:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.provider_combobox = ttk.Combobox(
        provider_selection_frame, 
        textvariable=app.translation_provider_var, 
        values=TRANSLATION_PROVIDERS, 
        state="readonly", 
        width=15
    )
    app.provider_combobox.pack(side=tk.LEFT, padx=5)
    app.provider_combobox.bind("<<ComboboxSelected>>", app._update_translation_settings_ui)

    # --- Frame for Provider-Specific Settings (API Key, Model, etc.) ---
    app.provider_details_frame = ttk.Frame(translation_settings_sub_panel)
    app.provider_details_frame.pack(fill=tk.X, expand=True, padx=5, pady=(5,0))

    # --- Common Translation Settings (Language, Output Format) ---
    common_settings_frame = ttk.Frame(translation_settings_sub_panel)
    common_settings_frame.pack(fill=tk.X, padx=5, pady=3)
    
    lang_frame = ttk.Frame(common_settings_frame)
    lang_frame.pack(fill=tk.X, pady=(0,3))
    ttk.Label(lang_frame, text="Target Language:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.language_combobox = ttk.Combobox(lang_frame, textvariable=app.target_language, 
                                         values=LANGUAGES, state="readonly", width=18)
    app.language_combobox.pack(side=tk.LEFT, padx=5)
    
    format_frame = ttk.Frame(common_settings_frame)
    format_frame.pack(fill=tk.X)
    ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
    app.format_combobox = ttk.Combobox(format_frame, textvariable=app.output_format_var,
                                      values=OUTPUT_FORMATS, state="readonly", width=10)
    app.format_combobox.pack(side=tk.LEFT, padx=5)
    
    # Panel: Whisper Settings
    whisper_frame = ttk.LabelFrame(top_right_settings_area, text="Whisper Transcription Settings", padding="10")
    whisper_frame.pack(fill=tk.X, padx=2, pady=(5,2))
    
    settings_frame_whisper = ttk.Frame(whisper_frame) 
    settings_frame_whisper.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(settings_frame_whisper, text="Model:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
    app.model_combobox = ttk.Combobox(settings_frame_whisper, textvariable=app.whisper_model_name_var, 
                                     values=WHISPER_MODELS, state="readonly", width=12)
    app.model_combobox.grid(row=0, column=1, padx=5, pady=3, sticky="w")
    
    ttk.Label(settings_frame_whisper, text="Device:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
    app.device_combobox = ttk.Combobox(settings_frame_whisper, textvariable=app.device_var, 
                                      values=DEVICES, state="readonly", width=8)
    app.device_combobox.grid(row=0, column=3, padx=5, pady=3, sticky="w")
    app.device_combobox.bind("<<ComboboxSelected>>", app.update_compute_types)
    
    ttk.Label(settings_frame_whisper, text="Compute Type:").grid(row=0, column=4, padx=5, pady=3, sticky="w")
    app.compute_type_combobox = ttk.Combobox(settings_frame_whisper, textvariable=app.compute_type_var, 
                                            state="readonly", width=10)
    app.compute_type_combobox.grid(row=0, column=5, padx=5, pady=3, sticky="w")
    for i in range(6): settings_frame_whisper.columnconfigure(i, weight=1)
    
    # --- Main Work Area: Notebook (bottom part of right_pane_container) ---
    app.notebook, app.text_widgets = create_notebook(right_pane_container)
    app.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=(5,2))
    
    return right_pane_container 