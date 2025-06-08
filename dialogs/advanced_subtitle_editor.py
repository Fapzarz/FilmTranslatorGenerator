"""
Advanced Subtitle Editor untuk Film Translator Generator - Qt Edition.

Dialog ini menyediakan tampilan video yang lebih besar dan kontrol detail
untuk mengedit subtitle, termasuk timing, styling, dan teks subtitle.
"""
import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QComboBox,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QWidget,
    QSplitter,
    QFrame,
    QMessageBox,
    QTimeEdit,
    QGraphicsScene,
    QGraphicsView,
)
from PySide6.QtCore import Qt, QTime, QUrl, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QColor,
    QKeySequence,
    QUndoStack,
    QUndoCommand,
    QFont,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem


class AdvancedSubtitleEditor(QDialog):
    """Advanced Subtitle Editor dengan tampilan video besar dan kontrol detail."""

    # Signal untuk memberitahu perubahan pada subtitle
    subtitle_updated = Signal(list)

    # Readability constants
    MAX_CPS_THRESHOLD = 20
    MAX_CPL_THRESHOLD = 42
    NORMAL_TEXT_COLOR = ""
    WARNING_TEXT_COLOR = "color: red;"

    def __init__(self, parent=None, segments=None, video_path=None):
        super().__init__(parent)
        self.app = parent
        self.segments = segments or []
        self.video_path = video_path
        self.current_segment_idx = -1

        self.undo_stack = QUndoStack(self)

        self.setWindowTitle("Advanced Subtitle Editor")
        self.resize(1200, 800)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.media_player.setAudioOutput(self.audio_output)

        self.graphics_scene = QGraphicsScene(self)
        self.video_item = QGraphicsVideoItem()
        self.subtitle_text_item = self.graphics_scene.addText("")

        self.graphics_scene.addItem(self.video_item)

        self.video_item.setAspectRatioMode(Qt.KeepAspectRatio)
        self.subtitle_text_item.setDefaultTextColor(Qt.white)
        self.subtitle_text_item.setZValue(1)

        self.media_player.setVideoOutput(self.video_item)

        self.setup_ui() # self.graphics_view is created here

        # Connections for video scaling
        self.video_item.nativeSizeChanged.connect(self._update_video_size)
        self.media_player.mediaStatusChanged.connect(self._on_media_status)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorViewCenter) # Scale from center

        if self.video_path and os.path.exists(self.video_path):
            self.load_video(self.video_path)

        # Jika ada segments, muat ke tabel
        if self.segments:
            self.load_segments()

        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)

        # Connect signals for readability indicators
        self.subtitle_text_edit.textChanged.connect(self._update_readability_indicators)
        self.start_time_edit.timeChanged.connect(self._update_readability_indicators)
        self.end_time_edit.timeChanged.connect(self._update_readability_indicators)

        # Connect signals for subtitle preview
        self.media_player.positionChanged.connect(self._show_current_subtitle_at_playback_position)
        self.subtitle_text_edit.textChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        self.start_time_edit.timeChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        self.end_time_edit.timeChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        # Style changes should also trigger preview update
        self.font_combo.currentTextChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        self.color_combo.currentTextChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        self.size_combo.currentTextChanged.connect(lambda: self._show_current_subtitle_at_playback_position())
        self.position_combo.currentTextChanged.connect(lambda: self._show_current_subtitle_at_playback_position())

        # Set initial state for readability indicators if a segment is loaded
        if self.current_segment_idx != -1:
            self._update_readability_indicators()
        else:
            self.cps_label.setText("CPS: N/A")
            self.cpl_label.setText("Max CPL: N/A")
            if self.NORMAL_TEXT_COLOR == "": # one time fetch of default color
                self.NORMAL_TEXT_COLOR = self.cps_label.styleSheet() # Assuming it's not styled initially
            self.cps_label.setStyleSheet(self.NORMAL_TEXT_COLOR)
            self.cpl_label.setStyleSheet(self.NORMAL_TEXT_COLOR)

        # Connect undo stack signals to update button states
        self.undo_stack.canUndoChanged.connect(self.undo_button.setEnabled)
        self.undo_stack.canRedoChanged.connect(self.redo_button.setEnabled)
        self.undo_stack.undoTextChanged.connect(self.undo_button.setText) # Show command text on button
        self.undo_stack.redoTextChanged.connect(self.redo_button.setText) # Show command text on button

        # Standard Shortcuts for Undo/Redo
        undo_shortcut = QAction(self)
        undo_shortcut.setShortcut(QKeySequence.Undo) # Ctrl+Z
        undo_shortcut.triggered.connect(self.undo_stack.undo)
        self.addAction(undo_shortcut)

        redo_shortcut = QAction(self)
        redo_shortcut.setShortcut(QKeySequence.Redo) # Ctrl+Y (Windows/Linux), Shift+Ctrl+Z (macOS)
        redo_shortcut.triggered.connect(self.undo_stack.redo)
        self.addAction(redo_shortcut)

    def setup_ui(self):
        """Setup UI untuk dialog editor."""
        layout = QVBoxLayout(self)

        # Splitter untuk membagi area video dan area editing
        splitter = QSplitter(Qt.Vertical)

        # === Video Player Section ===
        video_container = QFrame()
        video_container.setObjectName("VideoContainer") # Set object name for potential specific styling
        video_container.setFrameShape(QFrame.StyledPanel)
        # video_container.setStyleSheet("background-color: #1A1A1A;") # Style can be set here or in main stylesheet
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0,0,0,0) # Remove margins to use full container space
        video_layout.setSpacing(2) # Reduce spacing

        # QGraphicsView for video display
        self.graphics_view = QGraphicsView(self.graphics_scene, video_container) # Parent to container
        self.graphics_view.setMinimumHeight(350) # Increased min height slightly
        self.graphics_view.setFrameShape(QFrame.NoFrame) # No border for the view itself
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setAlignment(Qt.AlignCenter) # Center the scene content if smaller than view
        self.graphics_view.setStyleSheet("background-color: black;") # Background for the view

        video_layout.addWidget(self.graphics_view, 1) # Add with stretch factor

        # Controls area (media controls)
        controls_layout = QHBoxLayout()

        self.position_label = QLabel("00:00:00")
        controls_layout.addWidget(self.position_label)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)

        self.duration_label = QLabel("00:00:00")
        controls_layout.addWidget(self.duration_label)

        video_layout.addLayout(controls_layout)

        # Playback buttons
        playback_layout = QHBoxLayout()

        self.jump_prev_button = QPushButton("⏮ Prev")
        self.jump_prev_button.clicked.connect(self.jump_to_previous_segment)
        playback_layout.addWidget(self.jump_prev_button)

        self.rewind_button = QPushButton("⏪ -5s")
        self.rewind_button.clicked.connect(lambda: self.media_player.setPosition(max(0, self.media_player.position() - 5000)))
        playback_layout.addWidget(self.rewind_button)

        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_play)
        playback_layout.addWidget(self.play_button)

        self.forward_button = QPushButton("⏩ +5s")
        self.forward_button.clicked.connect(lambda: self.media_player.setPosition(min(self.media_player.duration(), self.media_player.position() + 5000)))
        playback_layout.addWidget(self.forward_button)

        self.jump_next_button = QPushButton("⏭ Next")
        self.jump_next_button.clicked.connect(self.jump_to_next_segment)
        playback_layout.addWidget(self.jump_next_button)

        playback_layout.addStretch()

        volume_label = QLabel("Volume:")
        playback_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        playback_layout.addWidget(self.volume_slider)

        video_layout.addLayout(playback_layout)

        # Add the video container to splitter
        splitter.addWidget(video_container)

        # === Subtitle Editing Section ===
        subtitle_container = QFrame()
        subtitle_container.setFrameShape(QFrame.StyledPanel)
        subtitle_layout = QVBoxLayout(subtitle_container)

        subtitle_tabs = QTabWidget()

        # Segment List tab
        segments_tab = QWidget()
        segments_layout = QVBoxLayout(segments_tab)

        self.segments_table = QTableWidget()
        self.segments_table.setColumnCount(5)
        self.segments_table.setHorizontalHeaderLabels(["#", "Start Time", "End Time", "Duration", "Text"])
        self.segments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.segments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.segments_table.selectionModel().selectionChanged.connect(self.on_segment_selection_changed)

        segments_layout.addWidget(self.segments_table)

        # Table action buttons
        table_buttons_layout = QHBoxLayout()

        add_segment_button = QPushButton("Add Segment")
        add_segment_button.clicked.connect(self.add_new_segment)
        table_buttons_layout.addWidget(add_segment_button)

        delete_segment_button = QPushButton("Delete Segment")
        delete_segment_button.clicked.connect(self.delete_selected_segment)
        table_buttons_layout.addWidget(delete_segment_button)

        table_buttons_layout.addStretch()

        sort_button = QPushButton("Sort by Time")
        sort_button.clicked.connect(self.sort_segments)
        table_buttons_layout.addWidget(sort_button)

        segments_layout.addLayout(table_buttons_layout)

        subtitle_tabs.addTab(segments_tab, "Segments List")

        # Segment Editor tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)

        # Time editing
        time_layout = QHBoxLayout()

        time_layout.addWidget(QLabel("Start Time:"))
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("hh:mm:ss.zzz")
        time_layout.addWidget(self.start_time_edit)

        set_current_start_button = QPushButton("Set to Current")
        set_current_start_button.clicked.connect(lambda: self.set_time_from_player('start'))
        time_layout.addWidget(set_current_start_button)

        time_layout.addSpacing(20)

        time_layout.addWidget(QLabel("End Time:"))
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("hh:mm:ss.zzz")
        time_layout.addWidget(self.end_time_edit)

        set_current_end_button = QPushButton("Set to Current")
        set_current_end_button.clicked.connect(lambda: self.set_time_from_player('end'))
        time_layout.addWidget(set_current_end_button)

        editor_layout.addLayout(time_layout)

        # Text editing
        editor_layout.addWidget(QLabel("Subtitle Text:"))
        self.subtitle_text_edit = QTextEdit()
        editor_layout.addWidget(self.subtitle_text_edit)

        # Readability Indicators
        readability_layout = QHBoxLayout()
        self.cps_label = QLabel("CPS: N/A")
        self.cpl_label = QLabel("Max CPL: N/A")
        readability_layout.addWidget(self.cps_label)
        readability_layout.addStretch()
        readability_layout.addWidget(self.cpl_label)
        editor_layout.addLayout(readability_layout)

        # Action buttons
        action_buttons_layout = QHBoxLayout()

        update_segment_button = QPushButton("Update Segment")
        update_segment_button.clicked.connect(self.update_current_segment)
        action_buttons_layout.addWidget(update_segment_button)

        action_buttons_layout.addStretch()

        save_all_button = QPushButton("Save All Changes")
        save_all_button.setStyleSheet("background-color: #4CAF50; color: white;")
        save_all_button.clicked.connect(self.save_all_changes)
        action_buttons_layout.addWidget(save_all_button)

        editor_layout.addLayout(action_buttons_layout)

        subtitle_tabs.addTab(editor_tab, "Segment Editor")

        # Style tab
        style_tab = QWidget()
        style_layout = QVBoxLayout(style_tab)

        # Font
        style_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana"])
        style_layout.addWidget(self.font_combo)

        # Font size
        style_layout.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large", "X-Large"])
        style_layout.addWidget(self.size_combo)

        # Color
        style_layout.addWidget(QLabel("Text Color:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Yellow", "Green", "Cyan", "Red"])
        style_layout.addWidget(self.color_combo)

        # Position
        style_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Bottom", "Top", "Middle"])
        style_layout.addWidget(self.position_combo)

        # Apply style button
        style_buttons_layout = QHBoxLayout()

        apply_to_current_button = QPushButton("Apply to Current")
        apply_to_current_button.clicked.connect(lambda: self.apply_style('current'))
        style_buttons_layout.addWidget(apply_to_current_button)

        apply_to_all_button = QPushButton("Apply to All")
        apply_to_all_button.clicked.connect(lambda: self.apply_style('all'))
        style_buttons_layout.addWidget(apply_to_all_button)

        style_layout.addLayout(style_buttons_layout)
        style_layout.addStretch()

        subtitle_tabs.addTab(style_tab, "Style")

        subtitle_layout.addWidget(subtitle_tabs)

        # Add the subtitle container to splitter
        splitter.addWidget(subtitle_container)

        # Set initial splitter sizes
        splitter.setSizes([300, 400])

        layout.addWidget(splitter)

        # Bottom action buttons
        button_layout = QHBoxLayout()

        self.undo_button = QPushButton("Undo")
        self.undo_button.setEnabled(False) # Initially disabled
        self.undo_button.clicked.connect(self.undo_stack.undo)
        button_layout.addWidget(self.undo_button)

        self.redo_button = QPushButton("Redo")
        self.redo_button.setEnabled(False) # Initially disabled
        self.redo_button.clicked.connect(self.undo_stack.redo)
        button_layout.addWidget(self.redo_button)

        button_layout.addStretch(1)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)

        self.save_button = QPushButton("Apply Changes and Close")
        self.save_button.setStyleSheet("background-color: #007BFF; color: white;")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def load_video(self, video_path):
        """Load video into media player."""
        if os.path.exists(video_path):
            self.video_path = video_path
            abs_path = os.path.abspath(video_path).replace('\\', '/')
            self.media_player.setSource(QUrl.fromLocalFile(abs_path))

    def load_segments(self):
        """Load subtitle segments into table."""
        self.segments_table.setRowCount(0)
        for i, segment in enumerate(self.segments):
            row_pos = self.segments_table.rowCount()
            self.segments_table.insertRow(row_pos)

            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            duration = end_time - start_time
            text = segment.get('text', "")

            # Format time values
            start_formatted = self.format_time(start_time)
            end_formatted = self.format_time(end_time)
            duration_formatted = self.format_duration(duration)

            self.segments_table.setItem(row_pos, 0, QTableWidgetItem(str(i+1)))
            self.segments_table.setItem(row_pos, 1, QTableWidgetItem(start_formatted))
            self.segments_table.setItem(row_pos, 2, QTableWidgetItem(end_formatted))
            self.segments_table.setItem(row_pos, 3, QTableWidgetItem(duration_formatted))
            self.segments_table.setItem(row_pos, 4, QTableWidgetItem(text))

    def format_time(self, seconds):
        """Format time in seconds to HH:MM:SS.ms format."""
        ms = int((seconds % 1) * 1000)
        s = int(seconds % 60)
        m = int((seconds / 60) % 60)
        h = int(seconds / 3600)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"

    def format_duration(self, seconds):
        """Format duration in seconds."""
        s = int(seconds % 60)
        m = int((seconds / 60) % 60)
        return f"{m:02}:{s:02}"

    def parse_time(self, time_str):
        """Parse time string to seconds."""
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            if '.' in s:
                s, ms = s.split('.')
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
            else:
                return int(h) * 3600 + int(m) * 60 + int(s)
        return 0

    def on_segment_selection_changed(self):
        """Handle selection change in the segments table."""
        selected_rows = self.segments_table.selectionModel().selectedRows()
        if selected_rows:
            row_idx = selected_rows[0].row()
            if 0 <= row_idx < len(self.segments):
                self.current_segment_idx = row_idx
                self.load_segment_to_editor(self.segments[row_idx])

                start_time = self.segments[row_idx].get('start', 0)
                self.media_player.setPosition(int(start_time * 1000))
                self._show_current_subtitle_at_playback_position()
            else:
                self.current_segment_idx = -1
                self.subtitle_text_item.setPlainText("") # Clear subtitle
                self.start_time_edit.setTime(QTime(0,0,0))
                self.end_time_edit.setTime(QTime(0,0,0))
                self.subtitle_text_edit.clear()
                self._update_readability_indicators()
        else:
            self.current_segment_idx = -1
            self.subtitle_text_item.setPlainText("") # Clear subtitle
            self.start_time_edit.setTime(QTime(0,0,0))
            self.end_time_edit.setTime(QTime(0,0,0))
            self.subtitle_text_edit.clear()
            self._update_readability_indicators()

    def load_segment_to_editor(self, segment):
        """Load selected segment details to editor fields."""
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)
        text = segment.get('text', "")

        # Set time fields
        # Temporarily disconnect signals to prevent premature updates
        self.start_time_edit.timeChanged.disconnect(self._update_readability_indicators)
        self.end_time_edit.timeChanged.disconnect(self._update_readability_indicators)
        self.subtitle_text_edit.textChanged.disconnect(self._update_readability_indicators)

        start_time_qtime = QTime(0, 0, 0).addMSecs(int(start_time * 1000))
        self.start_time_edit.setTime(start_time_qtime)

        end_time_qtime = QTime(0, 0, 0).addMSecs(int(end_time * 1000))
        self.end_time_edit.setTime(end_time_qtime)

        # Set text field
        self.subtitle_text_edit.setText(text)

        # Reconnect signals
        self.subtitle_text_edit.textChanged.connect(self._update_readability_indicators)
        self.subtitle_text_edit.textChanged.connect(self._show_current_subtitle_at_playback_position)
        self.start_time_edit.timeChanged.connect(self._update_readability_indicators)
        self.start_time_edit.timeChanged.connect(self._show_current_subtitle_at_playback_position)
        self.end_time_edit.timeChanged.connect(self._update_readability_indicators)
        self.end_time_edit.timeChanged.connect(self._show_current_subtitle_at_playback_position)

        # Manually trigger update for the loaded segment
        self._update_readability_indicators()
        self._show_current_subtitle_at_playback_position() # Also update preview

    def update_current_segment(self):
        """Update the currently selected segment with editor values using QUndoCommand."""
        if self.current_segment_idx == -1 or self.current_segment_idx >= len(self.segments):
            QMessageBox.warning(self, "Warning", "No segment selected.")
            return

        # Get new values from editor
        new_start_time = self.start_time_edit.time().msecsSinceStartOfDay() / 1000.0
        new_end_time = self.end_time_edit.time().msecsSinceStartOfDay() / 1000.0
        new_text = self.subtitle_text_edit.toPlainText()

        # Validate
        if new_end_time <= new_start_time:
            QMessageBox.warning(self, "Invalid Time", "End time must be after start time.")
            return

        old_segment_data = self.segments[self.current_segment_idx]
        # Preserve other potential data in the segment, like style
        new_segment_data = old_segment_data.copy()
        new_segment_data['start'] = new_start_time
        new_segment_data['end'] = new_end_time
        new_segment_data['text'] = new_text

        command = UpdateSegmentCommand(self, self.current_segment_idx, old_segment_data, new_segment_data)
        self.undo_stack.push(command)
        # The command's redo() method will handle the actual update and UI refresh.

    def add_new_segment(self):
        """Add a new empty segment using QUndoCommand."""
        # Get current video position
        current_pos = self.media_player.position() / 1000.0

        # Create new segment data
        new_segment_data = {
            'start': current_pos,
            'end': current_pos + 5,  # Default 5 seconds duration
            'text': "New subtitle",
            'style': {} # Initialize with empty style dict
        }

        # The index where the new segment will be added
        add_index = len(self.segments)

        command = AddSegmentCommand(self, new_segment_data, add_index)
        self.undo_stack.push(command)
        # The command's redo() method will handle adding to self.segments and UI updates.

    def delete_selected_segment(self):
        """Delete the selected segment using QUndoCommand."""
        if self.current_segment_idx == -1 or self.current_segment_idx >= len(self.segments):
            QMessageBox.warning(self, "Warning", "No segment selected.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete segment #{self.current_segment_idx + 1} ('{self.segments[self.current_segment_idx].get('text', '')[:20]}...')?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_segment_data = self.segments[self.current_segment_idx].copy()
            deleted_segment_index = self.current_segment_idx

            command = DeleteSegmentCommand(self, deleted_segment_data, deleted_segment_index)
            self.undo_stack.push(command)
            # The command's redo() method will handle removal from self.segments and UI updates.

    def sort_segments(self):
        """Sort segments by start time."""
        self.segments.sort(key=lambda x: x.get('start', 0))
        self.load_segments()

    def apply_style(self, target='current'):
        """Apply selected style to current or all segments."""
        if target == 'current' and (self.current_segment_idx == -1 or self.current_segment_idx >= len(self.segments)):
            QMessageBox.warning(self, "Warning", "No segment selected.")
            return

        style = {
            'font': self.font_combo.currentText(),
            'size': self.size_combo.currentText(),
            'color': self.color_combo.currentText(),
            'position': self.position_combo.currentText()
        }

        if target == 'current':
            # Apply to current segment only
            if 'style' not in self.segments[self.current_segment_idx]:
                self.segments[self.current_segment_idx]['style'] = {}
            self.segments[self.current_segment_idx]['style'].update(style)
        else:
            # Apply to all segments
            for segment in self.segments:
                if 'style' not in segment:
                    segment['style'] = {}
                segment['style'].update(style)

        QMessageBox.information(self, "Style Applied", f"Style applied to {target} segment(s).")
        self._show_current_subtitle_at_playback_position() # Refresh preview after style change

    def toggle_play(self):
        """Toggle between play and pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def set_position(self, position):
        """Set the media player position."""
        self.media_player.setPosition(position)

    def position_changed(self, position):
        """Handle media player position change."""
        # Update position slider
        self.position_slider.setValue(position)

        # Update position time label
        seconds = position / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        self.position_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

        # Auto-select the segment that matches current playback position
        self._auto_select_segment(seconds)

    def _auto_select_segment(self, current_seconds):
        """Update selected segment based on playback time."""
        if not self.segments:
            return

        new_index = -1
        for i, seg in enumerate(self.segments):
            start = float(seg.get('start', 0))
            end = float(seg.get('end', 0))
            if start <= current_seconds < end:
                new_index = i
                break

        if new_index != self.current_segment_idx:
            self.current_segment_idx = new_index
            if new_index == -1:
                # Clear preview if not within any segment
                self.subtitle_text_item.setPlainText("")
                return

            # Highlight row without triggering position jump
            self.segments_table.blockSignals(True)
            self.segments_table.selectRow(new_index)
            self.segments_table.blockSignals(False)

            # Load segment into editor for preview update
            self.load_segment_to_editor(self.segments[new_index])


    def duration_changed(self, duration):
        """Handle media player duration change."""
        # Update position slider range
        self.position_slider.setRange(0, duration)

        # Update duration time label
        seconds = duration / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        self.duration_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def playback_state_changed(self, state):
        """Handle media player playback state change."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("⏸ Pause")
        else:
            self.play_button.setText("▶ Play")

    def set_time_from_player(self, time_type):
        """Set the start or end time from current player position."""
        current_pos = self.media_player.position()
        current_time = QTime(0, 0, 0).addMSecs(current_pos)

        if time_type == 'start':
            self.start_time_edit.setTime(current_time)
        else:
            self.end_time_edit.setTime(current_time)

    def jump_to_previous_segment(self):
        """Jump to the previous segment in the list."""
        if not self.segments or self.current_segment_idx <= 0:
            return

        new_idx = self.current_segment_idx - 1
        self.segments_table.selectRow(new_idx)

    def jump_to_next_segment(self):
        """Jump to the next segment in the list."""
        if not self.segments or self.current_segment_idx >= len(self.segments) - 1:
            return

        new_idx = self.current_segment_idx + 1
        self.segments_table.selectRow(new_idx)

    def save_all_changes(self):
        """Save all changes to segments."""
        if self.current_segment_idx != -1:
            # Save the current segment being edited
            self.update_current_segment()

        QMessageBox.information(self, "Saved", "All changes have been saved.")

    def accept(self):
        """Handle dialog acceptance."""
        self.save_all_changes()
        # Stop media player to prevent sound continuing after dialog closes
        self.media_player.stop()
        # Emit signal with updated segments
        self.subtitle_updated.emit(self.segments)
        super().accept()

    def reject(self):
        """Handle dialog rejection."""
        # Stop media player to prevent sound continuing after dialog closes
        self.media_player.stop()
        super().reject()

    def _update_readability_indicators(self):
        """Calculate and update CPS and CPL indicators."""
        if self.current_segment_idx == -1 and not self.subtitle_text_edit.toPlainText():
            # No segment selected or text edit is empty after clearing, reset labels
            self.cps_label.setText("CPS: N/A")
            self.cpl_label.setText("Max CPL: N/A")
            if self.NORMAL_TEXT_COLOR == "":
                 self.NORMAL_TEXT_COLOR = self.cps_label.styleSheet()
            self.cps_label.setStyleSheet(self.NORMAL_TEXT_COLOR)
            self.cpl_label.setStyleSheet(self.NORMAL_TEXT_COLOR)
            return

        text = self.subtitle_text_edit.toPlainText()
        start_time_ms = self.start_time_edit.time().msecsSinceStartOfDay()
        end_time_ms = self.end_time_edit.time().msecsSinceStartOfDay()

        duration_seconds = (end_time_ms - start_time_ms) / 1000.0

        # CPS calculation
        if duration_seconds > 0:
            cps = len(text) / duration_seconds
            self.cps_label.setText(f"CPS: {cps:.2f}")
            if cps > self.MAX_CPS_THRESHOLD:
                self.cps_label.setStyleSheet(self.WARNING_TEXT_COLOR)
            else:
                self.cps_label.setStyleSheet(self.NORMAL_TEXT_COLOR)
        else:
            self.cps_label.setText("CPS: N/A (invalid duration)")
            self.cps_label.setStyleSheet(self.WARNING_TEXT_COLOR)

        # CPL calculation
        lines = text.splitlines()
        if not lines:
            max_cpl = 0
        else:
            max_cpl = max(len(line) for line in lines)

        self.cpl_label.setText(f"Max CPL: {max_cpl}")
        if max_cpl > self.MAX_CPL_THRESHOLD:
            self.cpl_label.setStyleSheet(self.WARNING_TEXT_COLOR)
        else:
            self.cpl_label.setStyleSheet(self.NORMAL_TEXT_COLOR)

    def _update_subtitle_preview(self):
        """Updates the text, style, and position of the subtitle preview using QGraphicsTextItem."""
        self.log_status(f"Attempting to update subtitle preview. Current segment index: {self.current_segment_idx}")

        if self.current_segment_idx == -1 or not self.segments:
            self.log_status("Preview hidden: No current segment or segments list empty.")
            self.subtitle_text_item.setPlainText("")
            return

        text = self.subtitle_text_edit.toPlainText()
        if not text.strip():
            self.log_status("Preview hidden: Text is empty.")
            self.subtitle_text_item.setPlainText("")
            return

        self.log_status(f"Preview text: '{text[:30]}...'")

        font_family = self.font_combo.currentText()
        text_color_name = self.color_combo.currentText().lower()
        position_pref = self.position_combo.currentText().lower()
        font_size_pref = self.size_combo.currentText().lower()

        # 1. Desired font size in screen pixels
        desired_pixel_size_map = {"small": 16, "medium": 20, "large": 24, "x-large": 30}
        desired_px = desired_pixel_size_map.get(font_size_pref, 20) # Default to medium (20px)

        color_map = {
            "white": QColor("white"), "yellow": QColor("yellow"),
            "green": QColor("lightgreen"), "cyan": QColor("cyan"),
            "red": QColor("red")
        }
        actual_text_color = color_map.get(text_color_name, QColor("white"))

        self.subtitle_text_item.setPlainText(text)
        self.subtitle_text_item.setDefaultTextColor(actual_text_color)

        # Set initial font (will be adjusted for scale shortly)
        # This helps in getting a preliminary bounding rect if needed before scaling adjustment
        # but the final visual size depends on the scaled font.
        initial_font = QFont(font_family, desired_px) # Use desired_px for now
        self.subtitle_text_item.setFont(initial_font)

        # Word wrap for QGraphicsTextItem - set text width based on video item
        video_bound_rect = self.video_item.boundingRect()
        if video_bound_rect.width() > 0 :
             self.subtitle_text_item.setTextWidth(video_bound_rect.width() * 0.9)
        else:
             self.subtitle_text_item.setTextWidth(self.graphics_view.width() * 0.9)

        # 2. Get current view scale factor
        # Ensure the view's transform is up-to-date if fitInView was just called in a different method.
        # However, typically fitInView would be called before this in _update_video_size.
        current_transform = self.graphics_view.transform()
        scale_factor = current_transform.m11() # Assuming uniform scaling (m11 == m22)

        # 3. Calculate scene font size
        # Avoid division by zero or extremely small scale_factor
        if abs(scale_factor) < 1e-3:
            scene_font_size = desired_px * 1000 # Effectively a very large font if scale is near zero
        else:
            scene_font_size = int(desired_px / scale_factor)

        scene_font_size = max(1, scene_font_size) # Ensure font size is at least 1

        # Apply the scene-adjusted font size
        scaled_font = QFont(font_family, scene_font_size)
        self.subtitle_text_item.setFont(scaled_font)
        self.log_status(f"Font: {font_family}, DesiredPx: {desired_px}, Scale: {scale_factor:.2f}, SceneFontSize: {scene_font_size}")

        # Positioning (uses bounding rect *after* font is set)
        text_bound_rect = self.subtitle_text_item.boundingRect()

        target_x = (video_bound_rect.width() - text_bound_rect.width()) / 2 + video_bound_rect.x()

        if position_pref == "top":
            target_y = video_bound_rect.top() + 10 # 10px from top of video item
        elif position_pref == "middle":
            target_y = video_bound_rect.center().y() - text_bound_rect.height() / 2
        else: # Bottom (default)
            target_y = video_bound_rect.bottom() - text_bound_rect.height() - 10 # 10px from bottom of video item

        self.subtitle_text_item.setPos(target_x, target_y)
        self.subtitle_text_item.show()

        self.log_status(f"Subtitle Item updated. Text: '{text[:20]}', Pos: ({target_x:.1f}, {target_y:.1f}), Visible: {self.subtitle_text_item.isVisible()}")

    def _show_current_subtitle_at_playback_position(self, player_position_ms=None):
        """Shows or hides the subtitle preview based on player position and current segment."""
        if self.current_segment_idx == -1 or not self.segments:
            self.subtitle_text_item.setPlainText("")
            return

        if player_position_ms is None:
            player_position_ms = self.media_player.position()

        current_segment = self.segments[self.current_segment_idx]

        raw_start_time = current_segment.get('start')
        raw_end_time = current_segment.get('end')

        start_time_s = 0.0
        if isinstance(raw_start_time, (int, float)): start_time_s = float(raw_start_time)
        elif raw_start_time is not None:
            try: start_time_s = float(raw_start_time)
            except (ValueError, TypeError): self.log_status(f"Warning: Could not convert raw_start_time ('{raw_start_time}') to float. Using 0.", "WARNING")

        end_time_s = 0.0
        if isinstance(raw_end_time, (int, float)): end_time_s = float(raw_end_time)
        elif raw_end_time is not None:
            try: end_time_s = float(raw_end_time)
            except (ValueError, TypeError): self.log_status(f"Warning: Could not convert raw_end_time ('{raw_end_time}') to float. Using 0.", "WARNING")

        start_time_ms = start_time_s * 1000.0
        end_time_ms = end_time_s * 1000.0

        if not isinstance(player_position_ms, (int, float)):
            player_position_ms = 0.0
        else:
            player_position_ms = float(player_position_ms)

        self.log_status(f"Debug Preview Times: start={start_time_ms}ms, player={player_position_ms}ms, end={end_time_ms}ms")

        if isinstance(start_time_ms, float) and isinstance(player_position_ms, float) and isinstance(end_time_ms, float):
            if start_time_ms <= player_position_ms < end_time_ms and self.subtitle_text_edit.toPlainText().strip():
                self._update_subtitle_preview()
            else:
                self.subtitle_text_item.setPlainText("")
        else:
            self.log_status(f"Error: Type mismatch for comparison. Check log.", "ERROR")
            self.subtitle_text_item.setPlainText("")

    def resizeEvent(self, event):
        """Handle dialog resize to ensure video and subtitles are displayed correctly."""
        super().resizeEvent(event)
        # Call _update_video_size here as well, as it contains fitInView and subtitle update logic
        self._update_video_size()

    # Placeholder for logging within the dialog
    def log_status(self, message, level="INFO"):
        # Simple print for now, can be integrated with main app's logger if needed
        print(f"[AdvEditor][{level}] {message}")

    # Helper methods for video scaling
    def _update_video_size(self):
        ns = self.video_item.nativeSize()
        if ns.isValid():
            self.video_item.setSize(ns)              # Ensure boundingRect has dimensions
            self.graphics_scene.setSceneRect(self.video_item.boundingRect()) # Set sceneRect to video item
            self.graphics_view.fitInView(self.video_item, Qt.KeepAspectRatio) # Scale to fit view

            # If subtitle is already visible, its position might need re-computation
            if self.subtitle_text_item.toPlainText():
                self._update_subtitle_preview()

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.log_status("Media loaded, updating video size.")
            self._update_video_size() # Call once media is fully loaded
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.log_status("Media finished.")
            # Optionally, you might want to reset player or handle looping here
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.log_status("Invalid media.", "ERROR")
            QMessageBox.critical(self, "Media Error", "Could not load the video. The file might be corrupted or in an unsupported format.")

# --- QUndoCommand Subclasses ---

class UpdateSegmentCommand(QUndoCommand):
    def __init__(self, editor, segment_idx, old_data, new_data, description="Update Segment"):
        super().__init__(description)
        self.editor = editor
        self.segment_idx = segment_idx
        self.old_data = old_data.copy() # Ensure we store copies
        self.new_data = new_data.copy()

    def redo(self):
        self.editor.segments[self.segment_idx] = self.new_data.copy()
        self.editor.load_segments() # Reloads table
        self.editor.segments_table.selectRow(self.segment_idx)
        # The selection change will trigger load_segment_to_editor and preview updates
        self.editor.log_status(f"Redo: {self.text()}")

    def undo(self):
        self.editor.segments[self.segment_idx] = self.old_data.copy()
        self.editor.load_segments()
        self.editor.segments_table.selectRow(self.segment_idx)
        self.editor.log_status(f"Undo: {self.text()}")

class AddSegmentCommand(QUndoCommand):
    def __init__(self, editor, segment_data, index, description="Add Segment"):
        super().__init__(description)
        self.editor = editor
        self.segment_data = segment_data.copy()
        self.index = index # Index where segment was/will be added

    def redo(self):
        self.editor.segments.insert(self.index, self.segment_data.copy())
        self.editor.load_segments()
        self.editor.segments_table.selectRow(self.index)
        self.editor.log_status(f"Redo: {self.text()}")

    def undo(self):
        self.editor.segments.pop(self.index)
        self.editor.load_segments()
        if self.editor.segments:
            prev_idx = max(0, self.index -1)
            if prev_idx < len(self.editor.segments):
                 self.editor.segments_table.selectRow(prev_idx)
            # If list becomes empty after pop, current_segment_idx might be -1
            # and editor fields should reflect that (handled by selection change or explicitly)
            elif not self.editor.segments: # Check again if list is empty
                 self.editor.current_segment_idx = -1
                 self.editor.subtitle_text_edit.clear()
                 self.editor.start_time_edit.setTime(QTime(0,0,0))
                 self.editor.end_time_edit.setTime(QTime(0,0,0))
        else:
            self.editor.current_segment_idx = -1
            self.editor.subtitle_text_edit.clear()
            self.editor.start_time_edit.setTime(QTime(0,0,0))
            self.editor.end_time_edit.setTime(QTime(0,0,0))
        self.editor.log_status(f"Undo: {self.text()}")

class DeleteSegmentCommand(QUndoCommand):
    def __init__(self, editor, segment_data, index, description="Delete Segment"):
        super().__init__(description)
        self.editor = editor
        self.segment_data = segment_data.copy()
        self.index = index # Index from where segment was deleted

    def redo(self):
        if 0 <= self.index < len(self.editor.segments):
            self.editor.segments.pop(self.index)
            self.editor.load_segments()
            if self.editor.segments:
                # Try to select the item now at the deleted index, or the one before, or the last one
                row_to_select = min(self.index, len(self.editor.segments) - 1)
                if row_to_select >=0:
                    self.editor.segments_table.selectRow(row_to_select)
                else: # List became empty
                    self.editor.current_segment_idx = -1
                    self.editor.subtitle_text_edit.clear()
                    self.editor.start_time_edit.setTime(QTime(0,0,0))
                    self.editor.end_time_edit.setTime(QTime(0,0,0))
            else: # List became empty
                self.editor.current_segment_idx = -1
                self.editor.subtitle_text_edit.clear()
                self.editor.start_time_edit.setTime(QTime(0,0,0))
                self.editor.end_time_edit.setTime(QTime(0,0,0))
        self.editor.log_status(f"Redo: {self.text()}")

    def undo(self):
        self.editor.segments.insert(self.index, self.segment_data.copy())
        self.editor.load_segments()
        self.editor.segments_table.selectRow(self.index)
        self.editor.log_status(f"Undo: {self.text()}")
