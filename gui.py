import sys
import os
import subprocess
import torch
import clip
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QComboBox,
    QInputDialog,
    QLabel,
    QPlainTextEdit,
    QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
import re
from collections import Counter

# Local modules
from database import Database
from file_manager import FileManager
from tagging import TagManager
from search import SearchEngine

# File type mappings
FILE_TYPE_MAPPINGS = {
    # Text Documents
    'text': {
        'extensions': ['.txt', '.doc', '.docx', '.odt', '.rtf', '.md', '.markdown'],
        'tag': 'text document'
    },
    # Programming
    'python': {
        'extensions': ['.py', '.pyw', '.ipynb'],
        'tag': 'python code'
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'tag': 'javascript code'
    },
    'java': {
        'extensions': ['.java', '.class', '.jar'],
        'tag': 'java code'
    },
    'cpp': {
        'extensions': ['.cpp', '.hpp', '.c', '.h', '.cc', '.cxx'],
        'tag': 'c++ code'
    },
    # Images
    'image': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'],
        'tag': 'image'
    },
    # Audio
    'audio': {
        'extensions': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'],
        'tag': 'audio'
    },
    # Video
    'video': {
        'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
        'tag': 'video'
    },
    # Archives
    'archive': {
        'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'tag': 'archive'
    },
    # PDFs
    'pdf': {
        'extensions': ['.pdf'],
        'tag': 'pdf document'
    },
    # Spreadsheets
    'spreadsheet': {
        'extensions': ['.xls', '.xlsx', '.ods', '.csv'],
        'tag': 'spreadsheet'
    },
    # Presentations
    'presentation': {
        'extensions': ['.ppt', '.pptx', '.odp'],
        'tag': 'presentation'
    }
}

# Common programming libraries and frameworks
CODE_PATTERNS = {
    'python': {
        'libraries': {
            'numpy': r'import\s+numpy|from\s+numpy',
            'pandas': r'import\s+pandas|from\s+pandas',
            'tensorflow': r'import\s+tensorflow|from\s+tensorflow',
            'pytorch': r'import\s+torch|from\s+torch',
            'scikit-learn': r'import\s+sklearn|from\s+sklearn',
            'matplotlib': r'import\s+matplotlib|from\s+matplotlib',
            'flask': r'import\s+flask|from\s+flask',
            'django': r'import\s+django|from\s+django',
            'requests': r'import\s+requests|from\s+requests',
            'beautifulsoup': r'import\s+bs4|from\s+bs4',
            'opencv': r'import\s+cv2|from\s+cv2',
            'pillow': r'import\s+PIL|from\s+PIL',
        }
    },
    'javascript': {
        'libraries': {
            'react': r'import\s+React|from\s+[\'"]react[\'"]',
            'vue': r'import\s+Vue|from\s+[\'"]vue[\'"]',
            'angular': r'import\s+.*from\s+[\'"]@angular/',
            'jquery': r'\$\(|jQuery',
            'express': r'import\s+express|from\s+[\'"]express[\'"]',
            'node': r'import\s+.*from\s+[\'"]node:',
            'typescript': r'\.tsx?$',
        }
    }
}

# Common themes and their associated keywords
THEME_KEYWORDS = {
    'business': ['report', 'meeting', 'project', 'budget', 'finance', 'marketing', 'sales', 'strategy'],
    'technical': ['technical', 'specification', 'architecture', 'design', 'implementation', 'system'],
    'academic': ['research', 'study', 'analysis', 'thesis', 'paper', 'academic', 'university'],
    'creative': ['story', 'poem', 'creative', 'fiction', 'narrative', 'plot', 'character'],
    'documentation': ['documentation', 'guide', 'manual', 'tutorial', 'how-to', 'instructions'],
    'data': ['data', 'analysis', 'statistics', 'dataset', 'metrics', 'analytics'],
    'web': ['web', 'website', 'html', 'css', 'javascript', 'frontend', 'backend'],
    'science': ['science', 'scientific', 'experiment', 'research', 'laboratory', 'physics', 'chemistry'],
    'mathematics': ['math', 'mathematics', 'equation', 'formula', 'calculation', 'algebra', 'geometry'],
}

def auto_tag_image(image_path: str):
    """
    Loads an image, performs a simple zero-shot label matching
    using CLIP, and returns the best match or top matches.
    """

    # 1) Load the model and device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    # 2) Image load and preprocess
    image = Image.open(image_path).convert("RGB")
    image_input = preprocess(image).unsqueeze(0).to(device)

    # 3) Custom label prompts.
    label_prompts = [
        "a photo of a cat",
        "a photo of a dog",
        "a photo of a car",
        "a photo of a person",
        "a photo of a building",
        "a photo of a tree",
        "a photo of a flower",
        "a photo of food",
        "a photo of a fruit",
        "a photo of a vegetable",
        "a photo of a laptop",
        "a photo of a smartphone",
        "a photo of a book",
        "a photo of a bike",
        "a photo of a bus",
        "a photo of a truck",
        "a photo of an airplane",
        "a photo of a train",
        "a photo of a boat",
        "a photo of water (ocean, lake, etc.)",
        "a photo of a mountain",
        "a photo of a desert",
        "a photo of a forest",
        "a photo of a beach",
        "a photo of a painting",
        "a photo of clothing",
        "a photo of shoes",
        "a photo of furniture",
        "a photo of a chair",
        "a photo of a table",
        "a photo of a clock",
        "a photo of headphones",
        "a photo of a horse",
        "a photo of a bird",
        "a photo of a fish",
        "a photo of an insect",
        "a photo of a reptile",
        "a photo of text or words",
        "a photo of a face (portrait)",
        "a photo of a cartoon",
        "a photo of a sign (street sign, billboard)",
        "a photo of a logo",
        "a photo of a plant",
        "a photo of a city or skyline",
        "a photo of a plate of food",
        "a photo of an animal",
        "a photo of the sky (clouds, sunset)",
        "a photo of art or sculpture"
    ]

    text_tokens = clip.tokenize(label_prompts).to(device)

    # 4) Encode the image and text
    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_tokens)

    # 5) Normalize and compute similarity
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    similarity = (image_features @ text_features.T)[ 0 ]  # shape: [num_labels]

    # 6) Find the best match
    best_score_idx = similarity.argmax().item()
    best_label = label_prompts[ best_score_idx ]
    return best_label


def open_file_cross_platform(file_path: str):
    """
    Opens the given file/path in the default application on Windows, macOS, or Linux.
    """
    if sys.platform.startswith("win"):
        os.startfile(file_path)
    elif sys.platform.startswith("darwin"):
        subprocess.run([ "open", file_path ])
    else:
        subprocess.run([ "xdg-open", file_path ])


def open_folder_cross_platform(folder_path: str):
    """
    Opens the given folder in the system's file explorer.
    """
    if sys.platform.startswith("win"):
        os.startfile(folder_path)
    elif sys.platform.startswith("darwin"):
        subprocess.run([ "open", folder_path ])
    else:
        subprocess.run([ "xdg-open", folder_path ])


class AutoTagWorker(QThread):
    tag_complete = pyqtSignal(int, str)  # file_id, tag

    def __init__(self, file_path, file_id, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_id = file_id

    def run(self):
        tag = auto_tag_image(self.file_path)
        self.tag_complete.emit(self.file_id, tag)


class FileTypeTagWorker(QThread):
    tag_complete = pyqtSignal(int, str)  # file_id, tag

    def __init__(self, file_path, file_id, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_id = file_id

    def run(self):
        tag = get_file_type_tag(self.file_path)
        if tag:
            self.tag_complete.emit(self.file_id, tag)


class ContentAnalysisWorker(QThread):
    analysis_complete = pyqtSignal(int, list)  # file_id, tags

    def __init__(self, file_path, file_id, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_id = file_id

    def run(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            _, ext = os.path.splitext(self.file_path)
            ext = ext.lower()
            
            tags = []
            
            # Analyze based on file type
            if ext in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf']:
                # Text analysis
                theme_tags = analyze_text_content(content)
                tags.extend(theme_tags)
            
            elif ext in ['.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                # Code analysis
                library_tags = analyze_code_content(content, ext)
                tags.extend(library_tags)
            
            if tags:
                self.analysis_complete.emit(self.file_id, tags)
        except Exception as e:
            print(f"Error analyzing content: {e}")


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.file_manager = FileManager(db)
        self.tag_manager = TagManager(db)
        self.search_engine = SearchEngine(db)

        self.setWindowTitle("Digital Library Management System")
        self.resize(1200, 650)

        self.threads = []  # Keep references to threads

        # --- Main Container & Layout ---
        container = QWidget()
        main_layout = QVBoxLayout(container)

        # ------------------------------------------------
        # 1) SEARCH BAR (TOP)
        # ------------------------------------------------
        search_layout = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by file name, path, metadata, tag name, or tag value...")
        search_layout.addWidget(self.search_bar)

        self.search_button = QPushButton("Search")
        # Optional: add an icon to the search button
        self.search_button.setIcon(QIcon("icons/search.png"))  # Adjust path if needed
        self.search_button.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_button)

        main_layout.addLayout(search_layout)

        # ------------------------------------------------
        # 2) FILE TABLE
        # ------------------------------------------------
        self.file_table = QTableWidget()
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Double-click to open the file (cross-platform)
        self.file_table.cellDoubleClicked.connect(self.open_file_in_system)

        # Optional dark style for the file table
        self.file_table.setStyleSheet("""
            QTableWidget {
                background-color: #2F2F2F;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #444;
                color: #FFFFFF;
            }
            QTableWidget::item {
                color: #DDDDDD;
            }
            QTableWidget::item:selected {
                background-color: #555;
            }
        """)

        # Add context menu to file table
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)

        main_layout.addWidget(self.file_table)

        # ------------------------------------------------
        # 3) ACTION BUTTONS
        # ------------------------------------------------
        btn_layout = QHBoxLayout()

        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.setIcon(QIcon("icons/add_file.png"))  # adjust as needed
        self.add_file_btn.clicked.connect(self.add_file)
        btn_layout.addWidget(self.add_file_btn)

        self.remove_file_btn = QPushButton("Remove File")
        self.remove_file_btn.setIcon(QIcon("icons/delete.png"))
        self.remove_file_btn.clicked.connect(self.remove_selected_file)
        btn_layout.addWidget(self.remove_file_btn)

        self.details_btn = QPushButton("Open Details")
        self.details_btn.setIcon(QIcon("icons/details.png"))
        self.details_btn.clicked.connect(self.open_file_details_dialog)
        btn_layout.addWidget(self.details_btn)

        main_layout.addLayout(btn_layout)

        self.setCentralWidget(container)
        self.setup_menu_bar()

        # Populate file table initially
        self.refresh_file_list()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #333;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #444;
            }
            QMenu {
                background-color: #333;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #555;
            }
        """)

        # File Menu
        file_menu = menubar.addMenu("File")

        add_file_action = QAction(QIcon("icons/add_file.png"), "Add File", self)
        add_file_action.triggered.connect(self.add_file)
        file_menu.addAction(add_file_action)

        remove_file_action = QAction(QIcon("icons/delete.png"), "Remove File", self)
        remove_file_action.triggered.connect(self.remove_selected_file)
        file_menu.addAction(remove_file_action)

        # Add Verify Files action
        verify_files_action = QAction("Verify Files", self)
        verify_files_action.triggered.connect(self.verify_files)
        file_menu.addAction(verify_files_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tag Menu
        tag_menu = menubar.addMenu("Tag")
        create_tag_action = QAction(QIcon("icons/tag_add.png"), "Create Tag", self)
        create_tag_action.triggered.connect(self.create_tag_dialog)
        tag_menu.addAction(create_tag_action)

    # -----------------------------------------------------
    # A) Searching
    # -----------------------------------------------------
    def on_search(self):
        query = self.search_bar.text().strip()
        if query:
            results = self.search_engine.search_all(query)
            self.refresh_file_list(results)
        else:
            # Show all if query is empty
            self.refresh_file_list()

    # -----------------------------------------------------
    # B) File Table Population
    # -----------------------------------------------------
    def refresh_file_list(self, files=None):
        """
        Shows columns: ID, Name, Path.
        """
        if files is None:
            files = self.file_manager.list_files()

        self.file_table.setColumnCount(3)
        headers = [ "ID", "Name", "Path" ]
        self.file_table.setHorizontalHeaderLabels(headers)
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.file_table.setRowCount(len(files))

        for row_idx, (file_id, file_name, file_path, metadata) in enumerate(files):
            # 0: ID
            item_id = QTableWidgetItem(str(file_id))
            item_id.setForeground(QColor("#DDDDDD"))
            self.file_table.setItem(row_idx, 0, item_id)

            # 1: Name
            item_name = QTableWidgetItem(file_name if file_name else "")
            item_name.setForeground(QColor("#DDDDDD"))
            self.file_table.setItem(row_idx, 1, item_name)

            # 2: Path
            item_path = QTableWidgetItem(file_path)
            item_path.setForeground(QColor("#DDDDDD"))
            self.file_table.setItem(row_idx, 2, item_path)

    # -----------------------------------------------------
    # C) File Actions
    # -----------------------------------------------------
    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            desc, ok = QInputDialog.getText(self, "Description", "Enter description (optional):")
            if ok:
                file_id = self.file_manager.add_file(file_path, desc)
                
                # Auto-tag based on file type
                file_type_thread = FileTypeTagWorker(file_path, file_id)
                file_type_thread.tag_complete.connect(self.on_file_type_tag_complete)
                file_type_thread.start()
                self.threads.append(file_type_thread)
                
                # If it's an image, do CLIP tagging
                if self._is_image(file_path):
                    auto_tag_thread = AutoTagWorker(file_path, file_id)
                    auto_tag_thread.tag_complete.connect(self.on_auto_tag_complete)
                    auto_tag_thread.start()
                    self.threads.append(auto_tag_thread)
                
                # If it's a text or code file, analyze content
                _, ext = os.path.splitext(file_path)
                if ext.lower() in ['.txt', '.md', '.markdown', '.doc', '.docx', '.odt', '.rtf', 
                                 '.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx']:
                    content_thread = ContentAnalysisWorker(file_path, file_id)
                    content_thread.analysis_complete.connect(self.on_content_analysis_complete)
                    content_thread.start()
                    self.threads.append(content_thread)
                
                QMessageBox.information(self, "File Added", f"File ID={file_id} added.")
                self.refresh_file_list()

    def _is_image(self, file_path: str) -> bool:
        """
        Returns True if 'file_path' has a typical image extension.
        """
        # Check extension
        ext = os.path.splitext(file_path)[ 1 ].lower()
        return ext in [ ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp" ]

    def _get_or_create_tag(self, tag_name: str, tag_type: str) -> int:
        """
        Return the ID of the existing tag with name=tag_name,
        or create it if not found.
        """
        # Check if there's already a tag with that name
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE name=?", (tag_name,))
        row = cursor.fetchone()
        if row:
            return row[ 0 ]
        else:
            # Create it via TagManager
            return self.tag_manager.create_tag(tag_name, tag_type)

    def remove_selected_file(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a file to remove.")
            return
        file_id_str = self.file_table.item(row, 0).text()
        file_id = int(file_id_str)

        confirm = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Are you sure you want to remove File ID={file_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.file_manager.remove_file(file_id)
            QMessageBox.information(self, "File Removed", f"File ID={file_id} removed.")
            self.refresh_file_list()

    def open_file_in_system(self, row, col):
        """
        Double-click action: open the file with default system app (cross-platform).
        """
        file_path = self.file_table.item(row, 2).text()

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"'{file_path}' does not exist on disk.")
            return

        # The cross-platform open:
        open_file_cross_platform(file_path)

    # -----------------------------------------------------
    # D) Open File Details Dialog
    # -----------------------------------------------------
    def open_file_details_dialog(self):
        row = self.file_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a file to view/edit details.")
            return

        file_id_str = self.file_table.item(row, 0).text()
        file_id = int(file_id_str)

        dialog = FileDetailsDialog(self.db, file_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh after changes
            self.refresh_file_list()

    # -----------------------------------------------------
    # E) Create Tag (Menu)
    # -----------------------------------------------------
    def create_tag_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Tag")

        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems([ "boolean", "numeric", "string" ])

        layout.addRow("Tag Name:", name_input)
        layout.addRow("Tag Type:", type_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            tag_name = name_input.text().strip()
            tag_type = type_combo.currentText().strip()
            if tag_name:
                tag_id = self.tag_manager.create_tag(tag_name, tag_type)
                QMessageBox.information(self, "Tag Created", f"'{tag_name}' (ID={tag_id}, {tag_type}) created.")
            else:
                QMessageBox.warning(self, "Invalid Name", "Tag name cannot be empty.")

    def verify_files(self):
        """
        Verify all files in the database and update paths if needed
        """
        self.file_manager.verify_all_files()
        self.refresh_file_list()
        QMessageBox.information(self, "File Verification", "File verification completed. The file list has been updated.")

    def on_auto_tag_complete(self, file_id, auto_tag):
        auto_tag_id = self._get_or_create_tag("auto", "string")
        self.tag_manager.assign_tag_to_file(file_id, auto_tag_id, auto_tag)
        QMessageBox.information(self, "Auto-Tagging Complete", f"Auto-tag for file ID={file_id}: {auto_tag}")
        self.refresh_file_list()

    def on_file_type_tag_complete(self, file_id, file_type_tag):
        """
        Handle completion of file type tagging
        """
        if file_type_tag:
            file_type_tag_id = self._get_or_create_tag("file_type", "string")
            self.tag_manager.assign_tag_to_file(file_id, file_type_tag_id, file_type_tag)
            self.refresh_file_list()

    def on_content_analysis_complete(self, file_id, tags):
        """
        Handle completion of content analysis
        """
        if tags:
            content_tag_id = self._get_or_create_tag("content_analysis", "string")
            for tag in tags:
                self.tag_manager.assign_tag_to_file(file_id, content_tag_id, tag)
            self.refresh_file_list()

    def show_context_menu(self, position):
        """
        Show context menu for file table
        """
        menu = QMenu()
        open_action = menu.addAction("Open File")
        open_folder_action = menu.addAction("Open Containing Folder")
        menu.addSeparator()
        remove_action = menu.addAction("Remove File")
        
        # Get the row at the clicked position
        row = self.file_table.rowAt(position.y())
        if row >= 0:
            action = menu.exec(self.file_table.mapToGlobal(position))
            if action == open_action:
                self.open_file_in_system(row, 0)
            elif action == open_folder_action:
                self.open_containing_folder(row)
            elif action == remove_action:
                self.remove_selected_file()

    def open_containing_folder(self, row):
        """
        Open the folder containing the selected file
        """
        file_path = self.file_table.item(row, 2).text()
        folder_path = os.path.dirname(file_path)
        
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, "Folder Not Found", f"Folder '{folder_path}' does not exist.")
            return
            
        open_folder_cross_platform(folder_path)


# ---------------------------------------------------------
# FileDetailsDialog: View/Update Name, Path, Description, Tags
# ---------------------------------------------------------
class FileDetailsDialog(QDialog):
    def __init__(self, db: Database, file_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.file_id = file_id

        self.file_manager = FileManager(db)
        self.tag_manager = TagManager(db)

        self.setWindowTitle(f"File Details (ID={file_id})")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # 1) Fetch file info
        conn = self.db.get_connection()
        file_info = conn.execute(
            "SELECT id, name, file_path, metadata FROM files WHERE id=?",
            (self.file_id,)
        ).fetchone()
        if not file_info:
            QMessageBox.critical(self, "Error", f"No file found with ID={file_id}")
            self.reject()
            return

        _, self.file_name, self.file_path, self.file_description = file_info

        # 2) Basic form: Name, Path, Description
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        self.name_edit = QLineEdit(self.file_name if self.file_name else "")
        form_layout.addRow("Name:", self.name_edit)

        # Add Open Folder button next to the path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.file_path if self.file_path else "")
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self.open_containing_folder)
        path_layout.addWidget(open_folder_btn)
        
        form_layout.addRow("Path:", path_layout)

        self.description_edit = QPlainTextEdit(self.file_description if self.file_description else "")
        form_layout.addRow("Description:", self.description_edit)

        layout.addWidget(form_widget)

        # 3) Tag Table
        self.tag_table = QTableWidget()
        self.tag_table.setColumnCount(3)  # [tag_id, tag_name, value]
        self.tag_table.setHorizontalHeaderLabels([ "Tag ID", "Tag Name", "Value" ])
        self.tag_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tag_table)
        self.tag_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.SelectedClicked
        )

        # We'll add a guard variable so we don't update the DB while we ourselves fill the table
        self.updating_table = False

        # Connect cellChanged
        self.tag_table.cellChanged.connect(self.on_tag_value_changed)

        self.refresh_tag_table()

        # 4) Tag Buttons
        tag_btn_layout = QHBoxLayout()
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.setIcon(QIcon("icons/tag_add.png"))
        self.add_tag_btn.clicked.connect(self.add_tag_dialog)
        tag_btn_layout.addWidget(self.add_tag_btn)

        self.remove_tag_btn = QPushButton("Remove Tag")
        self.remove_tag_btn.setIcon(QIcon("icons/tag_delete.png"))
        self.remove_tag_btn.clicked.connect(self.remove_selected_tag)
        tag_btn_layout.addWidget(self.remove_tag_btn)

        layout.addLayout(tag_btn_layout)

        # 5) Save/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Optionally keep your dark style for the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2F2F2F;
                color: #FFFFFF;
            }
            QLineEdit, QPlainTextEdit, QComboBox {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: 1px solid #555;
            }
            QLabel {
                color: #DDDDDD;
            }
            QPushButton {
                background-color: #444;
                color: #FFFFFF;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QTableWidget {
                background-color: #2F2F2F;
                gridline-color: #444;
                color: #DDDDDD;
            }
            QHeaderView::section {
                background-color: #444;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #555;
            }
        """)

    def refresh_tag_table(self):
        self.updating_table = True
        tags = self.tag_manager.get_tags_for_file(self.file_id)
        self.tag_table.setRowCount(len(tags))
        for row_idx, (t_id, t_name, t_type, t_val) in enumerate(tags):
            self.tag_table.setItem(row_idx, 0, QTableWidgetItem(str(t_id)))
            self.tag_table.setItem(row_idx, 1, QTableWidgetItem(t_name))
            self.tag_table.setItem(row_idx, 2, QTableWidgetItem(t_val if t_val else ""))
        self.updating_table = False

    def add_tag_dialog(self):
        """
        Show a dialog that lets user pick from existing tags (combo box)
        and optionally specify a value.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Existing Tag")
        d_layout = QFormLayout(dialog)

        tags_list = self.tag_manager.get_all_tags()  # returns [(id, name, type), ...]
        if not tags_list:
            QMessageBox.warning(self, "No Tags", "No tags exist yet. Create a new tag first.")
            dialog.reject()
            return

        self.tag_combo = QComboBox()
        for (tg_id, tg_name, tg_type) in tags_list:
            self.tag_combo.addItem(f"{tg_id}: {tg_name} [{tg_type}]", userData=(tg_id, tg_name, tg_type))
        d_layout.addRow("Tag:", self.tag_combo)

        self.value_edit = QLineEdit()
        d_layout.addRow("Value (optional):", self.value_edit)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        d_layout.addWidget(box)
        box.accepted.connect(dialog.accept)
        box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            (selected_tag_id, selected_tag_name, selected_tag_type) = self.tag_combo.currentData()
            value = self.value_edit.text().strip() or None
            try:
                self.tag_manager.assign_tag_to_file(self.file_id, selected_tag_id, value)
                QMessageBox.information(self, "Tag Assigned",
                                        f"Tag '{selected_tag_name}' (ID={selected_tag_id}) assigned.")
                self.refresh_tag_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def remove_selected_tag(self):
        row = self.tag_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a tag to remove.")
            return

        tag_id_str = self.tag_table.item(row, 0).text()
        tag_id = int(tag_id_str)

        confirm = QMessageBox.question(
            self,
            "Remove Tag",
            f"Are you sure you want to remove Tag ID={tag_id} from this file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.tag_manager.remove_tag_from_file(self.file_id, tag_id)
            QMessageBox.information(self, "Tag Removed", f"Tag ID={tag_id} removed.")
            self.refresh_tag_table()

    def save_changes(self):
        """
        Save updated Name/Description to DB.
        """
        new_name = self.name_edit.text().strip()
        new_description = self.description_edit.toPlainText().strip()

        conn = self.db.get_connection()
        with conn:
            conn.execute("""
                UPDATE files
                SET name = ?, metadata = ?
                WHERE id = ?
            """, (new_name, new_description, self.file_id))

        QMessageBox.information(self, "Saved", "File info updated.")
        self.accept()

    def on_tag_value_changed(self, row, column):
        """
        Called when the user finishes editing a cell.
        We'll update the DB if it's the Value column.
        """
        # Prevent updates while we are populating the table ourselves
        if self.updating_table:
            return

        # If the user changed the 'Value' column (index 2):
        if column == 2:
            tag_id_str = self.tag_table.item(row, 0).text()
            tag_id = int(tag_id_str)

            new_value = self.tag_table.item(row, column).text().strip() or None

            try:
                self.tag_manager.assign_tag_to_file(self.file_id, tag_id, new_value)
                # Optionally show a quick message or refresh the row
                # self.refresh_tag_table()  # or just keep it updated in place
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def open_containing_folder(self):
        """
        Open the folder containing the current file
        """
        folder_path = os.path.dirname(self.file_path)
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, "Folder Not Found", f"Folder '{folder_path}' does not exist.")
            return
            
        open_folder_cross_platform(folder_path)


def get_file_type_tag(file_path: str) -> str:
    """
    Determine the file type based on extension and return appropriate tag.
    Returns None if file type is not recognized.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    for category, info in FILE_TYPE_MAPPINGS.items():
        if ext in info['extensions']:
            return info['tag']
    return None


def analyze_text_content(text: str) -> list:
    """
    Analyze text content and return relevant theme tags.
    """
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    word_freq = Counter(words)
    
    themes = []
    for theme, keywords in THEME_KEYWORDS.items():
        # Count how many theme keywords appear in the text
        theme_score = sum(word_freq[word] for word in keywords if word in word_freq)
        if theme_score > 0:
            themes.append(theme)
    
    return themes


def analyze_code_content(content: str, file_extension: str) -> list:
    """
    Analyze code content and return relevant library/framework tags.
    """
    detected_libraries = []
    
    # Determine language based on extension
    if file_extension in ['.py', '.pyw', '.ipynb']:
        language = 'python'
    elif file_extension in ['.js', '.jsx', '.ts', '.tsx']:
        language = 'javascript'
    else:
        return []
    
    # Check for libraries in the code
    if language in CODE_PATTERNS:
        for lib, pattern in CODE_PATTERNS[language]['libraries'].items():
            if re.search(pattern, content, re.IGNORECASE):
                detected_libraries.append(lib)
    
    return detected_libraries


def main_gui():
    """
    Entry point for launching the GUI with a custom dark theme.
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Create a dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    app.setPalette(dark_palette)

    db = Database("library.db")
    db.connect()
    db.init_schema()

    window = MainWindow(db)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main_gui()
