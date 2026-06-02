import sys
import os
import json
import hashlib
import re
import logging
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QPlainTextEdit, QProgressBar, QLabel, QMessageBox, QSplitter,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QProcess, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# ==========================================
# Logging Configuration
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==========================================
# UI Theme (Professional Dark Mode)
# ==========================================
DARK_THEME_QSS = """
/* Global */
QWidget {
    background-color: #12121A;
    color: #E5E7EB;
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #09090B;
}

/* Cards / Frames */
QFrame#card {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 10px;
}

/* Typography */
QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #F9FAFB;
    letter-spacing: -0.5px;
}
QLabel#subtitle {
    font-size: 14px;
    color: #A1A1AA;
    margin-bottom: 8px;
}
QLabel#section-header {
    font-size: 12px;
    font-weight: 600;
    color: #D4D4D8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
}

/* Buttons */
QPushButton {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    min-width: 120px;
}
QPushButton:hover {
    background-color: #3F3F46;
    border: 1px solid #52525B;
}
QPushButton:pressed {
    background-color: #18181B;
}
QPushButton:disabled {
    background-color: #18181B;
    color: #52525B;
    border: 1px solid #27272A;
}

QPushButton#primary {
    background-color: #2563EB;
    border: 1px solid #3B82F6;
    color: white;
}
QPushButton#primary:hover {
    background-color: #1D4ED8;
    border: 1px solid #2563EB;
}
QPushButton#primary:disabled {
    background-color: #1E3A8A;
    border: 1px solid #1E3A8A;
    color: #93C5FD;
}

QPushButton#danger {
    background-color: #7F1D1D;
    border: 1px solid #991B1B;
    color: #FCA5A5;
}
QPushButton#danger:hover {
    background-color: #991B1B;
}

/* Tables */
QTableWidget {
    background-color: #09090B;
    alternate-background-color: #12121A;
    color: #E5E7EB;
    gridline-color: #27272A;
    border: 1px solid #27272A;
    border-radius: 8px;
    selection-background-color: #2563EB;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #18181B;
}
QTableWidget::item:selected {
    background-color: #2563EB;
    color: white;
}
QHeaderView::section {
    background-color: #18181B;
    color: #A1A1AA;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #27272A;
    border-right: 1px solid #27272A;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QHeaderView::section:last {
    border-right: none;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #09090B;
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #3F3F46;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #52525B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #09090B;
    height: 12px;
    margin: 0px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #3F3F46;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #52525B;
}

/* Text Edits (Logs) */
QPlainTextEdit {
    background-color: #000000;
    color: #10B981; /* Terminal green */
    border: 1px solid #27272A;
    border-radius: 8px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 12px;
    selection-background-color: #2563EB;
}
QPlainTextEdit#warningLog {
    color: #F59E0B; /* Amber for warnings */
    background-color: #0C0A09;
    border: 1px solid #422006;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #27272A;
    border-radius: 8px;
    background-color: #18181B;
    text-align: center;
    color: #F3F4F6;
    font-weight: bold;
    height: 24px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #60A5FA);
    border-radius: 7px;
}

/* Splitter */
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 16px;
    image: none;
}
QSplitter::handle:horizontal:hover {
    background-color: #27272A;
    border-radius: 4px;
}
"""

# ==========================================
# Data Models
# ==========================================
@dataclass
class VideoMetadata:
    file_path: str
    filename: str
    duration: float = 0.0
    fps: float = 0.0
    r_frame_rate: str = ""
    avg_frame_rate: str = ""
    codec: str = ""
    width: int = 0
    height: int = 0
    pixel_format: str = ""
    time_base: str = ""
    audio_codec: str = ""
    audio_channels: int = 0
    audio_sample_rate: int = 0
    bitrate: int = 0
    num_frames: int = 0
    creation_time: Optional[datetime] = None
    file_hash: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_vfr: bool = False

# ==========================================
# Helper Functions
# ==========================================
def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    # Check if running from source and file is in 'binaries' folder
    dev_path = os.path.join(base_path, "binaries", relative_path)
    if os.path.exists(dev_path):
        return dev_path
        
    return os.path.join(base_path, relative_path)

def natural_sort_key(s: str) -> list:
    """Sort strings containing numbers naturally (e.g., vid2.mp4 before vid10.mp4)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def parse_timestamp(text: str) -> Optional[datetime]:
    """Attempt to parse various timestamp formats found in CCTV filenames/metadata."""
    formats = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d_%H%M%S",
        "%Y-%m-%d_%H-%M-%S", "%Y-%m-%d %H-%M-%S", "%Y-%m-%d %H.%M.%S"
    ]
    text = re.sub(r'\.\d+', '', text)  # Remove milliseconds
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file efficiently using chunks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Hashing failed for {file_path}: {e}")
        return "ERROR"

# ==========================================
# FFprobe Analysis
# ==========================================
class FFprobeAnalyzer:
    def __init__(self, ffprobe_path: str):
        self.ffprobe_path = ffprobe_path

    def analyze(self, file_path: str) -> VideoMetadata:
        # Explicitly requested flags for forensic analysis
        cmd = [
            self.ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", "-count_frames", file_path
        ]
        
        try:
            kwargs = {}
            if sys.platform == 'win32':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, **kwargs)
            data = json.loads(result.stdout)
        except Exception as e:
            raise RuntimeError(f"FFprobe failed: {e}")

        meta = VideoMetadata(file_path=file_path, filename=os.path.basename(file_path))
        fmt = data.get("format", {})
        meta.duration = float(fmt.get("duration", 0))
        meta.bitrate = int(fmt.get("bit_rate", 0))
        
        # Parse Creation Time
        tags = fmt.get("tags", {})
        ct_str = tags.get("creation_time")
        if ct_str:
            meta.creation_time = parse_timestamp(ct_str)

        # Parse Streams
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

        if video_stream:
            meta.codec = video_stream.get("codec_name", "")
            meta.width = int(video_stream.get("width", 0))
            meta.height = int(video_stream.get("height", 0))
            meta.pixel_format = video_stream.get("pix_fmt", "")
            meta.time_base = video_stream.get("time_base", "")
            meta.r_frame_rate = video_stream.get("r_frame_rate", "")
            meta.avg_frame_rate = video_stream.get("avg_frame_rate", "")
            
            try:
                num, den = meta.r_frame_rate.split('/')
                meta.fps = float(num) / float(den)
            except Exception:
                meta.fps = 0.0
                
            # Prefer nb_read_frames from -count_frames, fallback to nb_frames
            meta.num_frames = int(video_stream.get("nb_read_frames", 0) or video_stream.get("nb_frames", 0))
            meta.is_vfr = self._detect_vfr(meta.avg_frame_rate, meta.r_frame_rate)

        if audio_stream:
            meta.audio_codec = audio_stream.get("codec_name", "")
            meta.audio_channels = int(audio_stream.get("channels", 0))
            meta.audio_sample_rate = int(audio_stream.get("sample_rate", 0))

        # Timestamp Extraction from filename fallback
        if not meta.creation_time:
            match = re.search(r'(\d{4}[-_]?\d{2}[-_]?\d{2}[T\s_-]\d{2}[:-]?\d{2}[:-]?\d{2})', meta.filename)
            if match:
                meta.creation_time = parse_timestamp(match.group(1).replace('_', ' ').replace('-', ' '))

        if meta.creation_time:
            meta.start_time = meta.creation_time
            meta.end_time = meta.start_time + timedelta(seconds=meta.duration)

        return meta

    def _detect_vfr(self, avg_rate: str, r_rate: str) -> bool:
        if not avg_rate or not r_rate or '/' not in avg_rate or '/' not in r_rate:
            return False
        try:
            avg = float(avg_rate.split('/')[0]) / float(avg_rate.split('/')[1])
            r = float(r_rate.split('/')[0]) / float(r_rate.split('/')[1])
            return abs(avg - r) / r > 0.01  # >1% difference implies VFR
        except Exception:
            return False

# ==========================================
# Background Workers
# ==========================================
class AnalysisWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, files: List[str], ffprobe_path: str):
        super().__init__()
        self.files = files
        self.ffprobe_path = ffprobe_path
        self._is_running = True

    def run(self):
        analyzer = FFprobeAnalyzer(self.ffprobe_path)
        metadata_list = []
        warnings = []
        total = len(self.files)

        for i, file in enumerate(self.files):
            if not self._is_running: break
            try:
                meta = analyzer.analyze(file)
                self.progress.emit(i + 1, total) # Emit progress before heavy hashing
                meta.file_hash = calculate_sha256(file)
                metadata_list.append(meta)
            except Exception as e:
                warnings.append(f"Failed to analyze {os.path.basename(file)}: {str(e)}")
                
        self.finished.emit(metadata_list, warnings)

    def stop(self):
        self._is_running = False

# ==========================================
# Validation Logic
# ==========================================
def validate_streams(metadata_list: List[VideoMetadata]) -> Tuple[bool, List[str]]:
    if not metadata_list: return True, []
    ref = metadata_list[0]
    warnings = []
    
    for i, meta in enumerate(metadata_list[1:]):
        diffs = []
        if meta.codec != ref.codec: diffs.append(f"Video Codec: {meta.codec} vs {ref.codec}")
        if (meta.width, meta.height) != (ref.width, ref.height): diffs.append(f"Resolution: {meta.width}x{meta.height} vs {ref.width}x{ref.height}")
        if abs(meta.fps - ref.fps) > 0.1: diffs.append(f"FPS: {meta.fps:.2f} vs {ref.fps:.2f}")
        if meta.time_base != ref.time_base: diffs.append(f"Time Base: {meta.time_base} vs {ref.time_base}")
        if meta.pixel_format != ref.pixel_format: diffs.append(f"Pixel Format: {meta.pixel_format} vs {ref.pixel_format}")
        if meta.audio_codec != ref.audio_codec: diffs.append(f"Audio Codec: {meta.audio_codec} vs {ref.audio_codec}")
        if meta.audio_channels != ref.audio_channels: diffs.append(f"Audio Channels: {meta.audio_channels} vs {ref.audio_channels}")
        if meta.audio_sample_rate != ref.audio_sample_rate: diffs.append(f"Audio Sample Rate: {meta.audio_sample_rate} vs {ref.audio_sample_rate}")
        
        if diffs:
            warnings.append(f"File {i+2} ({meta.filename}) differs from File 1 ({ref.filename}):\n" + "\n".join(diffs))
            
    return len(warnings) == 0, warnings

def check_vfr(metadata_list: List[VideoMetadata]) -> Tuple[bool, List[str]]:
    vfr_files = [m for m in metadata_list if m.is_vfr]
    warnings = []
    if vfr_files:
        warnings.append(f"Variable Frame Rate (VFR) footage detected in {len(vfr_files)} file(s) (e.g., {vfr_files[0].filename}).\nExact timestamp synchronization cannot be guaranteed when using stream-copy mode.")
    return len(vfr_files) == 0, warnings

def check_timeline(metadata_list: List[VideoMetadata]) -> Tuple[bool, List[str]]:
    warnings = []
    for i in range(1, len(metadata_list)):
        prev, curr = metadata_list[i-1], metadata_list[i]
        if prev.end_time and curr.start_time:
            diff = (curr.start_time - prev.end_time).total_seconds()
            if diff > 1.0:
                warnings.append(f"Timestamp discontinuity detected between {prev.filename} and {curr.filename}.\nGap: {timedelta(seconds=diff)}")
            elif diff < -1.0:
                warnings.append(f"Timestamp overlap detected between {prev.filename} and {curr.filename}.\nOverlap: {timedelta(seconds=abs(diff))}")
    return len(warnings) == 0, warnings

# ==========================================
# Merge Engine
# ==========================================
class MergeEngine(QObject):
    progress_update = pyqtSignal(float, str)
    log_message = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, ffmpeg_path: str):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.process = None
        self.total_duration = 0.0

    def start_merge(self, metadata_list: List[VideoMetadata], output_file: str):
        concat_list_path = os.path.join(os.path.dirname(output_file), "concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for meta in metadata_list:
                safe_path = meta.file_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
                
        self.total_duration = sum(m.duration for m in metadata_list)
        args = ["-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", "-y", output_file]
        
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_ready_read)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)
        self.process.start(self.ffmpeg_path, args)

    def cancel(self):
        if self.process: self.process.terminate()

    def _on_ready_read(self):
        data = self.process.readAll().data().decode('utf-8', errors='ignore')
        self.log_message.emit(data)
        
        matches = re.findall(r'time=(\d+):(\d{2}):(\d{2}(?:\.\d+)?)', data)
        if matches:
            h, m, s = matches[-1]
            current_time_sec = int(h) * 3600 + int(m) * 60 + float(s)
            percent = (current_time_sec / self.total_duration) * 100 if self.total_duration > 0 else 0
            self.progress_update.emit(min(percent, 100.0), "")

    def _on_error(self, error):
        self.finished_signal.emit(False, f"Process Error: {error}")

    def _on_finished(self, exit_code, exit_status):
        if exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            self.finished_signal.emit(True, "Success")
        else:
            self.finished_signal.emit(False, f"FFmpeg exited with code {exit_code}.")

# ==========================================
# Verification Engine
# ==========================================
class VerificationEngine:
    def __init__(self, ffprobe_path: str):
        self.analyzer = FFprobeAnalyzer(ffprobe_path)
        
    def verify(self, output_file: str, expected_duration: float, expected_frames: int, fps: float) -> Dict:
        meta = self.analyzer.analyze(output_file)
        duration_diff = abs(meta.duration - expected_duration)
        frame_diff = abs(meta.num_frames - expected_frames)
        max_duration_error = 1.0 / fps if fps > 0 else 0.04
        
        return {
            "passed": (frame_diff <= 1) and (duration_diff <= max_duration_error),
            "expected_duration": expected_duration, "actual_duration": meta.duration, "duration_diff": duration_diff,
            "expected_frames": expected_frames, "actual_frames": meta.num_frames, "frame_diff": frame_diff,
            "meta": meta
        }

# ==========================================
# Main GUI Application
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCTVConcatenator")
        self.resize(1200, 800)
        
        self.ffmpeg_path = get_resource_path("ffmpeg.exe")
        self.ffprobe_path = get_resource_path("ffprobe.exe")
        
        if not os.path.exists(self.ffmpeg_path) or not os.path.exists(self.ffprobe_path):
            QMessageBox.warning(self, "Executables Missing", "Could not find ffmpeg.exe and ffprobe.exe.\nPlease select the folder containing them.")
            folder = QFileDialog.getExistingDirectory(self, "Select FFmpeg Folder")
            if folder:
                self.ffmpeg_path = os.path.join(folder, "ffmpeg.exe")
                self.ffprobe_path = os.path.join(folder, "ffprobe.exe")
                if not os.path.exists(self.ffmpeg_path):
                    QMessageBox.critical(self, "Error", "FFmpeg not found in selected folder.")
                    sys.exit(1)
            else:
                sys.exit(1)
                
        self.metadata_list = []
        self.expected_duration = 0.0
        self.expected_frames = 0
        self.avg_fps = 0.0
        self.output_path = ""
        
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(DARK_THEME_QSS)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("CCTVConcatenator")
        title.setObjectName("title")
        subtitle = QLabel("Preserve exact frame sequence, playback duration, and timestamp progression.")
        subtitle.setObjectName("subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        # Action Bar
        action_card = QFrame()
        action_card.setObjectName("card")
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)
        
        self.btn_folder = QPushButton("📁 Select Input Folder")
        self.btn_output = QPushButton("💾 Select Output File")
        self.btn_merge = QPushButton("▶ Start Merge")
        self.btn_merge.setObjectName("primary")
        self.btn_cancel = QPushButton("✖ Cancel")
        self.btn_cancel.setObjectName("danger")
        
        self.btn_merge.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        
        action_layout.addWidget(self.btn_folder)
        action_layout.addWidget(self.btn_output)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_merge)
        action_layout.addWidget(self.btn_cancel)
        
        main_layout.addWidget(action_card)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Side
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        
        # Files Card
        files_card = QFrame()
        files_card.setObjectName("card")
        files_layout = QVBoxLayout(files_card)
        files_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_files = QLabel("Input Files")
        lbl_files.setObjectName("section-header")
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Duration", "Start Time", "End Time", "Status"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.currentItemChanged.connect(self._on_file_selected)
        
        files_layout.addWidget(lbl_files)
        files_layout.addWidget(self.file_table)
        left_layout.addWidget(files_card)
        
        # Metadata Card
        meta_card = QFrame()
        meta_card.setObjectName("card")
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_meta = QLabel("Selected File Metadata")
        lbl_meta.setObjectName("section-header")
        
        self.meta_table = QTableWidget()
        self.meta_table.setColumnCount(2)
        self.meta_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.meta_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.meta_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.meta_table.verticalHeader().setVisible(False)
        
        meta_layout.addWidget(lbl_meta)
        meta_layout.addWidget(self.meta_table)
        left_layout.addWidget(meta_card)
        
        splitter.addWidget(left_widget)
        
        # Right Side
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # Validation Card
        val_card = QFrame()
        val_card.setObjectName("card")
        val_layout = QVBoxLayout(val_card)
        val_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_val = QLabel("Validation & Warnings")
        lbl_val.setObjectName("section-header")
        
        self.validation_text = QPlainTextEdit()
        self.validation_text.setObjectName("warningLog")
        self.validation_text.setReadOnly(True)
        
        val_layout.addWidget(lbl_val)
        val_layout.addWidget(self.validation_text)
        right_layout.addWidget(val_card)
        
        # Log Card
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_log = QLabel("Processing Log")
        lbl_log.setObjectName("section-header")
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(2000)
        
        log_layout.addWidget(lbl_log)
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_card)
        
        splitter.addWidget(right_widget)
        
        splitter.setSizes([700, 500])
        main_layout.addWidget(splitter, 1)
        
        # Footer / Status
        footer_card = QFrame()
        footer_card.setObjectName("card")
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #A1A1AA; font-weight: 500;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        footer_layout.addWidget(self.status_label)
        footer_layout.addWidget(self.progress_bar, 1)
        
        main_layout.addWidget(footer_card)
        
        # Signals
        self.btn_folder.clicked.connect(self._on_select_folder)
        self.btn_output.clicked.connect(self._on_select_output)
        self.btn_merge.clicked.connect(self._on_start_merge)
        self.btn_cancel.clicked.connect(self._on_cancel_merge)

    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select CCTV Footage Folder")
        if not folder: return
        
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".mp4")]
        files.sort(key=natural_sort_key)
        
        if not files:
            QMessageBox.warning(self, "No Files", "No MP4 files found.")
            return
            
        self.status_label.setText("Analyzing files...")
        self.btn_merge.setEnabled(False)
        self.btn_folder.setEnabled(False)
        
        self.analysis_worker = AnalysisWorker(files, self.ffprobe_path)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.start()

    def _on_analysis_progress(self, current, total):
        self.status_label.setText(f"Analyzing file {current}/{total}...")

    def _on_analysis_finished(self, metadata_list, warnings):
        self.metadata_list = metadata_list
        self._populate_file_table()
        
        self.validation_text.clear()
        if warnings:
            self.validation_text.appendPlainText("Analysis Warnings:\n" + "\n".join(warnings) + "\n")
            
        valid_streams, stream_w = validate_streams(self.metadata_list)
        valid_vfr, vfr_w = check_vfr(self.metadata_list)
        valid_timeline, time_w = check_timeline(self.metadata_list)
        
        all_warnings = stream_w + vfr_w + time_w
        if all_warnings:
            self.validation_text.appendPlainText("VALIDATION WARNINGS:\n" + "\n\n".join(all_warnings))
            self.validation_text.appendPlainText("\nMerge can still continue in stream-copy mode, but forensic integrity might be compromised.")
        else:
            self.validation_text.appendPlainText("All validation checks PASSED. Safe to merge in stream-copy mode.")
            
        if not valid_streams:
            self.btn_merge.setEnabled(False)
            QMessageBox.critical(self, "Stream Mismatch", "Files have different stream properties.\nCannot merge using stream-copy mode.")
        else:
            self.btn_merge.setEnabled(True)
            self.btn_folder.setEnabled(True)
            self.status_label.setText("Ready to merge.")
            
        self.expected_duration = sum(m.duration for m in self.metadata_list)
        self.expected_frames = sum(m.num_frames for m in self.metadata_list)
        self.avg_fps = sum(m.fps for m in self.metadata_list) / len(self.metadata_list) if self.metadata_list else 0

    def _populate_file_table(self):
        self.file_table.setRowCount(0)
        for meta in self.metadata_list:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            self.file_table.setItem(row, 0, QTableWidgetItem(meta.filename))
            self.file_table.setItem(row, 1, QTableWidgetItem(str(timedelta(seconds=int(meta.duration)))))
            self.file_table.setItem(row, 2, QTableWidgetItem(meta.start_time.strftime("%H:%M:%S") if meta.start_time else "N/A"))
            self.file_table.setItem(row, 3, QTableWidgetItem(meta.end_time.strftime("%H:%M:%S") if meta.end_time else "N/A"))
            self.file_table.setItem(row, 4, QTableWidgetItem("VFR" if meta.is_vfr else "OK"))

    def _on_file_selected(self, current, previous):
        if not current: return
        meta = self.metadata_list[current.row()]
        self.meta_table.setRowCount(0)
        
        props = [
            ("Filename", meta.filename), ("Duration", f"{meta.duration:.2f}s"),
            ("FPS", f"{meta.fps:.2f}"), ("Resolution", f"{meta.width}x{meta.height}"),
            ("Video Codec", meta.codec), ("Pixel Format", meta.pixel_format),
            ("Time Base", meta.time_base), ("Frames", str(meta.num_frames)),
            ("Audio Codec", meta.audio_codec), ("Audio Channels", str(meta.audio_channels)),
            ("Sample Rate", str(meta.audio_sample_rate)), ("Bitrate", f"{meta.bitrate} bps"),
            ("Creation Time", meta.creation_time.isoformat() if meta.creation_time else "N/A"),
            ("VFR", "Yes" if meta.is_vfr else "No"), ("SHA256", meta.file_hash)
        ]
        
        for prop, val in props:
            row = self.meta_table.rowCount()
            self.meta_table.insertRow(row)
            self.meta_table.setItem(row, 0, QTableWidgetItem(prop))
            self.meta_table.setItem(row, 1, QTableWidgetItem(str(val)))

    def _on_select_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select Output File", "merged_cctv.mp4", "MP4 Files (*.mp4)")
        if path:
            self.output_path = path
            self.status_label.setText(f"Output: {path}")

    def _on_start_merge(self):
        if not self.output_path:
            QMessageBox.warning(self, "No Output", "Please select an output file first.")
            return
            
        if os.path.exists(self.output_path):
            reply = QMessageBox.question(self, "File Exists", "Output file already exists. Overwrite?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No: return
                
        self.btn_merge.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        self.merge_engine = MergeEngine(self.ffmpeg_path)
        self.merge_engine.progress_update.connect(self._on_merge_progress)
        self.merge_engine.log_message.connect(self._on_merge_log)
        self.merge_engine.finished_signal.connect(self._on_merge_finished)
        self.merge_engine.start_merge(self.metadata_list, self.output_path)

    def _on_merge_progress(self, percent, _):
        self.progress_bar.setValue(int(percent))

    def _on_merge_log(self, msg):
        self.log_text.appendPlainText(msg.strip())

    def _on_merge_finished(self, success, message):
        self.btn_cancel.setEnabled(False)
        self.btn_merge.setEnabled(True)
        
        if success:
            self.status_label.setText("Merge completed. Running verification...")
            self._run_verification()
        else:
            self.status_label.setText(f"Merge failed: {message}")
            QMessageBox.critical(self, "Merge Failed", message)
            
    def _on_cancel_merge(self):
        if hasattr(self, 'merge_engine'):
            self.merge_engine.cancel()
            self.status_label.setText("Cancelling...")

    def _run_verification(self):
        verifier = VerificationEngine(self.ffprobe_path)
        result = verifier.verify(self.output_path, self.expected_duration, self.expected_frames, self.avg_fps)
        self._generate_report(result)
        
        if result["passed"]:
            self.status_label.setText("Merge PASSED verification. Forensic integrity maintained.")
            QMessageBox.information(self, "Success", "Merge completed and PASSED forensic verification!\nReport saved to verification_report.txt")
        else:
            self.status_label.setText("Merge FAILED verification. Check report.")
            QMessageBox.warning(self, "Verification Failed", "The merged file failed forensic verification checks.\nPlease review verification_report.txt")

    def _generate_report(self, verify_result):
        report_path = os.path.join(os.path.dirname(self.output_path), "verification_report.txt")
        meta = verify_result["meta"]
        
        lines = [
            "="*50, "CCTV MERGE VERIFICATION REPORT", "="*50,
            f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Input Files Count: {len(self.metadata_list)}", "",
            "Input File List & SHA256 Hashes:"
        ]
        for m in self.metadata_list:
            lines.append(f"  {m.filename}  |  {m.file_hash}")
            
        lines.extend([
            "", "Expected Statistics vs Actual:",
            f"  Expected Duration: {self.expected_duration:.4f} s",
            f"  Actual Duration:   {meta.duration:.4f} s",
            f"  Duration Diff:     {verify_result['duration_diff']:.4f} s",
            "",
            f"  Expected Frames:   {self.expected_frames}",
            f"  Actual Frames:     {meta.num_frames}",
            f"  Frame Difference:  {verify_result['frame_diff']}",
            "",
            f"  Input FPS (Avg):   {self.avg_fps:.2f}",
            f"  Output FPS:        {meta.fps:.2f}",
            f"  Codec:             {meta.codec}",
            f"  Time Base:         {meta.time_base}",
            "",
            f"Validation Result: {'PASS' if verify_result['passed'] else 'FAIL'}",
            "", "Warnings Encountered During Analysis:",
            self.validation_text.toPlainText() or "None", "="*50
        ])
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"Report saved to {report_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())