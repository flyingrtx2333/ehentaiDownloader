#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manga Downloader UI - A modern GUI for manga downloading and PDF generation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from pathlib import Path
from typing import Optional

from manga_downloader import MangaDownloader
from pdf_generator import PDFGenerator


class MangaDownloaderUI:
    """Modern UI for manga downloader"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("E-hentai Manga Downloader - 漫画下载器")
        self.root.geometry("800x900")  # 增加默认窗口大小
        self.root.resizable(True, True)
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 900)
        
        # 居中显示窗口
        self.center_window()
        
        # 配置文件路径
        self.config_file = "ui_config.json"
        
        # 语言设置
        self.current_language = "zh"  # 默认中文
        self.translations = self._get_translations()
        
        # Initialize downloader and PDF generator
        self.downloader = MangaDownloader()
        self.pdf_generator = PDFGenerator()
        
        # Variables
        self.download_url = tk.StringVar()
        self.save_path = tk.StringVar()
        self.folder_name = tk.StringVar()
        self.proxy_host = tk.StringVar(value="127.0.0.1")
        self.proxy_port = tk.StringVar(value="7890")
        self.generate_pdf = tk.BooleanVar(value=True)
        self.pdf_name = tk.StringVar()  # PDF文件名
        self.pdf_author = tk.StringVar()  # PDF作者信息
        self.is_downloading = False
        self.failed_urls = []  # 存储失败的URL
        
        # 加载保存的配置
        self.load_config()
        
        # 设置现代化样式
        self.setup_modern_style()
        self.setup_ui()
        
        # 绑定窗口关闭事件，保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """加载保存的配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 恢复各个输入框的值
                if 'download_url' in config:
                    self.download_url.set(config['download_url'])
                if 'save_path' in config:
                    self.save_path.set(config['save_path'])
                if 'folder_name' in config:
                    folder_name = config['folder_name']
                    if folder_name and folder_name != self.t("folder_name_hint"):
                        self.folder_name.set(folder_name)
                if 'proxy_host' in config:
                    self.proxy_host.set(config['proxy_host'])
                if 'proxy_port' in config:
                    self.proxy_port.set(config['proxy_port'])
                if 'generate_pdf' in config:
                    self.generate_pdf.set(config['generate_pdf'])
                if 'pdf_name' in config:
                    pdf_name = config['pdf_name']
                    if pdf_name and pdf_name != self.t("pdf_name_hint"):
                        self.pdf_name.set(pdf_name)
                if 'pdf_author' in config:
                    pdf_author = config['pdf_author']
                    if pdf_author and pdf_author != self.t("pdf_author_hint"):
                        self.pdf_author.set(pdf_author)
                if 'pdf_folder' in config:
                    # PDF文件夹路径会在UI创建后设置
                    self._saved_pdf_folder = config['pdf_folder']
                if 'language' in config:
                    self.current_language = config['language']
                    
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存当前配置"""
        try:
            config = {
                'download_url': self.download_url.get(),
                'save_path': self.save_path.get(),
                'folder_name': self.folder_name.get(),
                'proxy_host': self.proxy_host.get(),
                'proxy_port': self.proxy_port.get(),
                'generate_pdf': self.generate_pdf.get(),
                'pdf_name': self.pdf_name.get(),
                'pdf_author': self.pdf_author.get(),
                'pdf_folder': getattr(self, 'pdf_folder_var', tk.StringVar()).get(),
                'language': self.current_language
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        self.save_config()
        self.root.destroy()
    
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _get_translations(self):
        """获取翻译文本"""
        return {
            "zh": {
                "title": "E-hentai漫画下载器",
                "download_config": "下载配置",
                "download_url": "下载地址:(请给出首个页面地址，例如https://e-hentai.org/s/f079533ce8/3210316-1)",
                "save_path": "保存路径:",
                "folder_name": "文件夹名称:",
                "folder_name_hint": "(留空使用漫画标题)",
                "proxy_settings": "代理设置",
                "proxy_host": "代理主机:",
                "proxy_port": "代理端口:",
                "generate_pdf_after": "下载后生成PDF",
                "start_download": "开始下载",
                "retry_failed": "重试失败项",
                "pdf_generation": "PDF生成",
                "image_folder": "图片文件夹:",

                "pdf_name": "PDF文件名:",
                "pdf_name_hint": "(留空使用文件夹名称)",
                "pdf_author": "作者信息:",
                "pdf_author_hint": "(留空则不添加作者信息)",
                "generate_pdf": "生成PDF",
                "progress": "进度",
                "ready": "就绪",
                "success_count": "成功: {}",
                "failed_count": "失败: {}",
                "total_count": "总计: {}",
                "log": "日志",
                "clear_log": "清除日志",
                "failed_urls": "失败URL列表",
                "retry_all": "重试全部",
                "copy_urls": "复制URLs",
                "browse": "浏览",
                "select_save_dir": "选择保存目录",
                "select_image_folder": "选择图片文件夹",
                "language": "语言",
                "chinese": "中文",
                "english": "English",
                "settings": "设置",
                "download_in_progress": "下载正在进行中!",
                "please_enter_url": "请输入下载地址!",
                "please_select_folder": "请选择图片文件夹!",
                "folder_not_exist": "选择的文件夹不存在!",

                "starting_download": "开始下载...",
                "download_completed": "下载完成!",
                "download_failed": "下载失败!",
                "generating_pdf": "正在生成PDF...",
                "pdf_generated": "PDF生成成功!",
                "pdf_failed": "PDF生成失败!",
                "error_occurred": "发生错误!",
                "counting_pages": "正在计算总页数...",
                "downloading_page": "正在下载第{}页...",
                "download_completed_pdf": "下载完成，正在生成PDF...",
                "found_images": "找到{}张图片 ({} MB)",
                "generating_pdf_for": "正在为{}生成PDF",
                "pdf_generated_success": "PDF生成成功: {}.pdf",
                "error_during_download": "下载过程中发生错误: {}",
                "error_during_pdf": "PDF生成过程中发生错误: {}",
                "retry_completed": "重试完成!",
                "no_failed_urls": "没有失败的URL需要重试"
            },
            "en": {
                "title": "E-hentai Manga Downloader",
                "download_config": "Download Configuration",
                "download_url": "Download URL:(Please give the first page address, such as https://e-hentai.org/s/f079533ce8/3210316-1)",
                "save_path": "Save Path:",
                "folder_name": "Folder Name:",
                "folder_name_hint": "(Leave empty to use manga title)",
                "proxy_settings": "Proxy Settings",
                "proxy_host": "Proxy Host:",
                "proxy_port": "Proxy Port:",
                "generate_pdf_after": "Generate PDF after download",
                "start_download": "Start Download",
                "retry_failed": "Retry Failed",
                "pdf_generation": "PDF Generation",
                "image_folder": "Image Folder:",

                "pdf_name": "PDF Name:",
                "pdf_name_hint": "(Leave empty to use folder name)",
                "pdf_author": "Author Info:",
                "pdf_author_hint": "(Leave empty to skip author info)",
                "generate_pdf": "Generate PDF",
                "progress": "Progress",
                "ready": "Ready",
                "success_count": "Success: {}",
                "failed_count": "Failed: {}",
                "total_count": "Total: {}",
                "log": "Log",
                "clear_log": "Clear Log",
                "failed_urls": "Failed URLs",
                "retry_all": "Retry All",
                "copy_urls": "Copy URLs",
                "browse": "Browse",
                "select_save_dir": "Select Save Directory",
                "select_image_folder": "Select Image Folder",
                "language": "Language",
                "chinese": "中文",
                "english": "English",
                "settings": "Settings",
                "download_in_progress": "Download already in progress!",
                "please_enter_url": "Please enter a download URL!",
                "please_select_folder": "Please select an image folder!",
                "folder_not_exist": "Selected folder does not exist!",

                "starting_download": "Starting download...",
                "download_completed": "Download completed!",
                "download_failed": "Download failed!",
                "generating_pdf": "Generating PDF...",
                "pdf_generated": "PDF generated successfully!",
                "pdf_failed": "PDF generation failed!",
                "error_occurred": "Error occurred!",
                "counting_pages": "Counting total pages...",
                "downloading_page": "Downloading page {}...",
                "download_completed_pdf": "Download completed, generating PDF...",
                "found_images": "Found {} images ({} MB)",
                "generating_pdf_for": "Generating PDF for {}",
                "pdf_generated_success": "PDF generated successfully: {}.pdf",
                "error_during_download": "Error during download: {}",
                "error_during_pdf": "Error during PDF generation: {}",
                "retry_completed": "Retry completed!",
                "no_failed_urls": "No failed URLs to retry"
            }
        }
    
    def t(self, key: str, *args):
        """获取翻译文本"""
        text = self.translations[self.current_language].get(key, key)
        if args:
            return text.format(*args)
        return text
    
    def setup_modern_style(self):
        """设置现代化样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 现代化配色方案
        colors = {
            'primary': '#667eea',      # 主色调 - 蓝紫色
            'primary_dark': '#5a6fd8',  # 深色主色调
            'secondary': '#764ba2',     # 次要色调
            'success': '#48bb78',       # 成功色
            'warning': '#ed8936',       # 警告色
            'error': '#f56565',         # 错误色
            'info': '#4299e1',          # 信息色
            'background': '#f7fafc',    # 背景色
            'surface': '#ffffff',       # 表面色
            'text_primary': '#2d3748',  # 主要文本色
            'text_secondary': '#718096', # 次要文本色
            'border': '#e2e8f0',        # 边框色
            'shadow': 'rgba(0, 0, 0, 0.1)'  # 阴影色
        }
        
        # 配置现代化颜色和样式
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 20, 'bold'), 
                       foreground=colors['primary'])
        
        style.configure('Section.TLabelframe', 
                       font=('Segoe UI', 11, 'bold'), 
                       foreground=colors['text_primary'],
                       background=colors['surface'],
                       borderwidth=2,
                       relief='solid')
        
        style.configure('Section.TLabelframe.Label', 
                       font=('Segoe UI', 11, 'bold'),
                       foreground=colors['primary'],
                       background=colors['surface'])
        
        # 现代化按钮样式 - 圆角渐变效果
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 9, 'bold'),
                       background=colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(12, 6))
        
        style.map('Modern.TButton',
                 background=[('active', colors['primary_dark']), 
                           ('pressed', colors['secondary'])],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # 小按钮样式 - 用于浏览按钮
        style.configure('Small.TButton', 
                       font=('Segoe UI', 8, 'bold'),
                       background=colors['info'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(8, 4))
        
        style.map('Small.TButton',
                 background=[('active', '#3182ce'), ('pressed', '#2c5282')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # 成功按钮样式 - 用于开始下载
        style.configure('Success.TButton', 
                       font=('Segoe UI', 9, 'bold'),
                       background=colors['success'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(12, 6))
        
        style.map('Success.TButton',
                 background=[('active', '#38a169'), ('pressed', '#2f855a')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # 警告按钮样式 - 用于重试失败项
        style.configure('Warning.TButton', 
                       font=('Segoe UI', 9, 'bold'),
                       background=colors['warning'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(12, 6))
        
        style.map('Warning.TButton',
                 background=[('active', '#dd6b20'), ('pressed', '#c05621')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # 次要按钮样式 - 用于生成PDF
        style.configure('Secondary.TButton', 
                       font=('Segoe UI', 9, 'bold'),
                       background=colors['secondary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(12, 6))
        
        style.map('Secondary.TButton',
                 background=[('active', '#6b46c1'), ('pressed', '#553c9a')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # 现代化输入框样式 - 更好的圆角效果
        style.configure('Modern.TEntry',
                       fieldbackground=colors['surface'],
                       borderwidth=1,
                       relief='solid',
                       focuscolor=colors['primary'],
                       bordercolor=colors['border'])
        
        # 现代化Combobox样式
        style.configure('Modern.TCombobox',
                       fieldbackground=colors['surface'],
                       background=colors['surface'],
                       borderwidth=1,
                       relief='solid',
                       focuscolor=colors['primary'],
                       bordercolor=colors['border'],
                       arrowcolor=colors['text_secondary'])
        
        style.map('Modern.TCombobox',
                 fieldbackground=[('readonly', colors['surface'])],
                 selectbackground=[('readonly', colors['primary'])],
                 selectforeground=[('readonly', 'white')])
        
        # 标签样式 - 移除背景色
        style.configure('Success.TLabel', 
                       font=('Segoe UI', 9), 
                       foreground=colors['success'])
        
        style.configure('Error.TLabel', 
                       font=('Segoe UI', 9), 
                       foreground=colors['error'])
        
        style.configure('Info.TLabel', 
                       font=('Segoe UI', 9), 
                       foreground=colors['info'])
        
        style.configure('Warning.TLabel', 
                       font=('Segoe UI', 9), 
                       foreground=colors['warning'])
        
        # 现代化进度条样式 - 更细的进度条
        try:
            style.configure('Progress.TProgressbar', 
                          thickness=8, 
                          background=colors['primary'],
                          borderwidth=0,
                          lightcolor=colors['primary'],
                          darkcolor=colors['primary_dark'])
        except:
            pass
        
        # 设置窗口背景色和现代化效果
        self.root.configure(bg=colors['background'])
        
        # 设置窗口圆角和半透明效果
        try:
            # 设置窗口透明度
            self.root.attributes('-alpha', 0.95)
            
            # 尝试设置窗口圆角（仅在支持的平台上）
            import platform
            if platform.system() == "Windows":
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # 设置窗口圆角
                    hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                    if hwnd:
                        # 设置窗口样式为圆角
                        GWL_EXSTYLE = -20
                        WS_EX_LAYERED = 0x80000
                        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
                                                           ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)
                except:
                    pass
        except:
            pass
        
        # 设置全局字体
        default_font = ('Segoe UI', 9)
        style.configure('TLabel', font=default_font)
        style.configure('TButton', font=default_font)
        style.configure('TEntry', font=default_font)
        style.configure('TCombobox', font=default_font)
        style.configure('TCheckbutton', font=default_font)
        style.configure('TRadiobutton', font=default_font)
        
        # 现代化复选框样式 - 使用更完整的配置
        style.configure('Modern.TCheckbutton',
                       background=colors['background'],
                       foreground=colors['text_primary'],
                       indicatorcolor=colors['success'],
                       indicatorrelief='flat',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       indicatorbackground=colors['background'],
                       indicatorborderwidth=1,
                       indicatordiameter=12)
        
        # 设置复选框的选中状态样式
        style.map('Modern.TCheckbutton',
                 background=[('active', colors['background']), ('selected', colors['background'])],
                 foreground=[('active', colors['text_primary']), ('selected', colors['text_primary'])],
                 indicatorcolor=[('selected', colors['success']), ('active', colors['success']),
                               ('pressed', colors['success']), ('alternate', colors['success'])],
                 indicatorbackground=[('selected', colors['background']), ('active', colors['background'])])
        
        # 现代化分隔线样式
        style.configure('Separator.TFrame',
                       background=colors['border'],
                       relief='flat',
                       borderwidth=0)
        
        # 现代化Notebook样式 - 更好的标签样式
        style.configure('TNotebook',
                       background=colors['surface'],
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background=colors['background'],
                       foreground=colors['text_secondary'],
                       borderwidth=1,
                       relief='solid',
                       padding=(15, 8),
                       width=15)  # 增加固定标签宽度，确保两个tab大小一致
        
        style.map('TNotebook.Tab',
                 background=[('selected', colors['primary']), ('active', colors['primary_dark'])],
                 foreground=[('selected', 'white'), ('active', 'white')])
        
        # 现代化Frame样式
        style.configure('Modern.TFrame',
                       background=colors['surface'],
                       relief='flat',
                       borderwidth=0)
        
    def setup_ui(self):
        """Setup the user interface"""
        # 现代化配色方案
        colors = {
            'background': '#f7fafc',
            'surface': '#ffffff',
            'border': '#e2e8f0',
            'shadow': 'rgba(0, 0, 0, 0.1)'
        }
        
        # Main frame with reduced padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 设置主框架背景色
        try:
            main_frame.configure(style='Main.TFrame')
            style = ttk.Style()
            style.configure('Main.TFrame', background=colors['background'])
        except:
            pass
        
        # Header with title and language selector
        self.create_header(main_frame)
        
        # Download Section
        self.create_download_section(main_frame)
        
        # PDF Generation Section
        self.create_pdf_section(main_frame)
        
        # Progress Section
        self.create_progress_section(main_frame)
        
        # Log Section
        self.create_log_section(main_frame)
        
        # 设置保存的PDF文件夹路径（如果存在）
        if hasattr(self, '_saved_pdf_folder'):
            self.pdf_folder_var.set(self._saved_pdf_folder)
        
    def create_header(self, parent):
        """创建标题和语言选择器"""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)
        
        # 创建内部容器用于更好的布局
        inner_header = ttk.Frame(header_frame, style='Modern.TFrame')
        inner_header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        inner_header.columnconfigure(0, weight=1)
        
        # Title with modern styling - removed background color
        title_label = ttk.Label(inner_header, text=self.t("title"), style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Language selector with modern styling
        lang_frame = ttk.Frame(inner_header, style='Modern.TFrame')
        lang_frame.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        ttk.Label(lang_frame, text=self.t("language") + ": ", 
                 font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        lang_var = tk.StringVar(value=self.current_language)
        lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, 
                                 values=["zh", "en"], state="readonly", width=8,
                                 font=('Segoe UI', 9), style='Modern.TCombobox')
        lang_combo.pack(side=tk.LEFT, padx=(5, 0))
        lang_combo.bind('<<ComboboxSelected>>', lambda e: self.change_language(lang_var.get()))
        
        # 添加分隔线
        separator = ttk.Frame(header_frame, height=1, style='Separator.TFrame')
        separator.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(8, 0))
        
    def create_download_section(self, parent):
        """Create download configuration section"""
        # Download frame with modern styling
        download_frame = ttk.LabelFrame(parent, text=self.t("download_config"), 
                                       padding="0", style='Section.TLabelframe')
        download_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        download_frame.columnconfigure(1, weight=1)
        
        # 添加内部间距和现代化布局
        inner_frame = ttk.Frame(download_frame, padding="8")
        inner_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        inner_frame.columnconfigure(1, weight=1)
        
        # URL
        ttk.Label(inner_frame, text=self.t("download_url"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 3))
        url_entry = ttk.Entry(inner_frame, textvariable=self.download_url, 
                             width=70, font=('Segoe UI', 10), style='Modern.TEntry')
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        # 绑定自动保存
        self.download_url.trace('w', lambda *args: self.save_config())
        
        # Save Path
        ttk.Label(inner_frame, text=self.t("save_path"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 3))
        path_frame = ttk.Frame(inner_frame)
        path_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        path_frame.columnconfigure(0, weight=1)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.save_path, 
                              width=60, font=('Segoe UI', 10), style='Modern.TEntry')
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        # 绑定自动保存
        self.save_path.trace('w', lambda *args: self.save_config())
        
        browse_btn = ttk.Button(path_frame, text=self.t("browse"), 
                               command=self.browse_save_path, style='Small.TButton')
        browse_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Folder Name - moved below save_path
        ttk.Label(inner_frame, text=self.t("folder_name"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(0, 3))
        folder_entry = ttk.Entry(inner_frame, textvariable=self.folder_name, 
                                width=70, font=('Segoe UI', 10), style='Modern.TEntry')
        folder_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        # 绑定自动保存
        self.folder_name.trace('w', lambda *args: self.save_config())
        # Set placeholder text only if no saved value
        if not self.folder_name.get():
            folder_entry.insert(0, self.t("folder_name_hint"))
            folder_entry.configure(foreground='#718096')
        
        def on_folder_focus_in(event):
            if folder_entry.get() == self.t("folder_name_hint"):
                folder_entry.delete(0, tk.END)
                folder_entry.configure(foreground='#2d3748')
                self.folder_name.set("")  # Clear the variable too
        
        def on_folder_focus_out(event):
            if not folder_entry.get():
                folder_entry.insert(0, self.t("folder_name_hint"))
                folder_entry.configure(foreground='#718096')
                # 不保存placeholder文本
            else:
                # 保存实际输入的内容
                self.save_config()
        
        folder_entry.bind('<FocusIn>', on_folder_focus_in)
        folder_entry.bind('<FocusOut>', on_folder_focus_out)
        
        # Proxy Settings with modern separator
        separator_frame = ttk.Frame(inner_frame)
        separator_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)
        separator_frame.configure(height=1, style='Separator.TFrame')
        
        ttk.Label(inner_frame, text=self.t("proxy_settings"), 
                 font=('Segoe UI', 11, 'bold')).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        
        proxy_frame = ttk.Frame(inner_frame)
        proxy_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        ttk.Label(proxy_frame, text=self.t("proxy_host"), 
                 font=('Segoe UI', 9)).pack(side=tk.LEFT)
        proxy_host_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_host, 
                                   width=15, font=('Segoe UI', 9), style='Modern.TEntry')
        proxy_host_entry.pack(side=tk.LEFT, padx=(5, 15))
        # 绑定自动保存
        self.proxy_host.trace('w', lambda *args: self.save_config())
        
        ttk.Label(proxy_frame, text=self.t("proxy_port"), 
                 font=('Segoe UI', 9)).pack(side=tk.LEFT)
        proxy_port_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_port, 
                                   width=8, font=('Segoe UI', 9), style='Modern.TEntry')
        proxy_port_entry.pack(side=tk.LEFT, padx=(5, 0))
        # 绑定自动保存
        self.proxy_port.trace('w', lambda *args: self.save_config())
        
        # Options with modern checkbox styling
        options_frame = ttk.Frame(inner_frame)
        options_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))
        
        # 使用tk.Checkbutton以获得更好的样式控制
        pdf_check = tk.Checkbutton(options_frame, text=self.t("generate_pdf_after"), 
                                  variable=self.generate_pdf, 
                                  font=('Segoe UI', 9),
                                  fg='#2d3748',  # 文本色
                                  selectcolor='#48bb78',  # 选中时的颜色（绿色）
                                  activeforeground='#2d3748',
                                  relief='flat',
                                  bd=0,
                                  command=self.save_config)  # 绑定自动保存
        pdf_check.pack(side=tk.LEFT)
        
        # Download and Retry buttons with modern spacing
        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))
        
        self.download_btn = ttk.Button(button_frame, text=self.t("start_download"), 
                                      command=self.start_download, style='Success.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.retry_btn = ttk.Button(button_frame, text=self.t("retry_failed"), 
                                   command=self.retry_failed_downloads, style='Warning.TButton')
        self.retry_btn.pack(side=tk.LEFT)
        
    def create_pdf_section(self, parent):
        """Create PDF generation section"""
        # PDF frame with modern styling
        pdf_frame = ttk.LabelFrame(parent, text=self.t("pdf_generation"), 
                                  padding="0", style='Section.TLabelframe')
        pdf_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        pdf_frame.columnconfigure(1, weight=1)
        
        # 添加内部间距和现代化布局
        inner_frame = ttk.Frame(pdf_frame, padding="8")
        inner_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        inner_frame.columnconfigure(1, weight=1)
        
        # Folder selection
        ttk.Label(inner_frame, text=self.t("image_folder"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 3))
        pdf_path_frame = ttk.Frame(inner_frame)
        pdf_path_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        pdf_path_frame.columnconfigure(0, weight=1)
        
        self.pdf_folder_var = tk.StringVar()
        pdf_folder_entry = ttk.Entry(pdf_path_frame, textvariable=self.pdf_folder_var, 
                                   width=60, font=('Segoe UI', 10), style='Modern.TEntry')
        pdf_folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        # 绑定自动保存
        self.pdf_folder_var.trace('w', lambda *args: self.save_config())
        
        pdf_browse_btn = ttk.Button(pdf_path_frame, text=self.t("browse"), 
                                   command=self.browse_pdf_folder, style='Small.TButton')
        pdf_browse_btn.grid(row=0, column=1, padx=(10, 0))
        
        # File extensions - fixed format
        self.extensions_var = tk.StringVar(value="jpg,jpg,webp")
        # Note: Extensions are fixed to jpg,jpg,webp for PDF generation
        
        # PDF name
        ttk.Label(inner_frame, text=self.t("pdf_name"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 3))
        pdf_name_entry = ttk.Entry(inner_frame, textvariable=self.pdf_name, 
                                 width=70, font=('Segoe UI', 10), style='Modern.TEntry')
        pdf_name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        # 绑定自动保存
        self.pdf_name.trace('w', lambda *args: self.save_config())
        # Set placeholder text only if no saved value
        if not self.pdf_name.get():
            pdf_name_entry.insert(0, self.t("pdf_name_hint"))
            pdf_name_entry.configure(foreground='#718096')
        
        def on_pdf_name_focus_in(event):
            if pdf_name_entry.get() == self.t("pdf_name_hint"):
                pdf_name_entry.delete(0, tk.END)
                pdf_name_entry.configure(foreground='#2d3748')
                self.pdf_name.set("")  # Clear the variable too
        
        def on_pdf_name_focus_out(event):
            if not pdf_name_entry.get():
                pdf_name_entry.insert(0, self.t("pdf_name_hint"))
                pdf_name_entry.configure(foreground='#718096')
                self.pdf_name.set("")  # Ensure variable is also empty
            else:
                # 保存实际输入的内容
                self.save_config()
        
        pdf_name_entry.bind('<FocusIn>', on_pdf_name_focus_in)
        pdf_name_entry.bind('<FocusOut>', on_pdf_name_focus_out)
        
        # PDF Author
        ttk.Label(inner_frame, text=self.t("pdf_author"), 
                 font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(0, 3))
        pdf_author_entry = ttk.Entry(inner_frame, textvariable=self.pdf_author, 
                                   width=70, font=('Segoe UI', 10), style='Modern.TEntry')
        pdf_author_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(15, 0), pady=(0, 8))
        # 绑定自动保存
        self.pdf_author.trace('w', lambda *args: self.save_config())
        # Set placeholder text only if no saved value
        if not self.pdf_author.get():
            pdf_author_entry.insert(0, self.t("pdf_author_hint"))
            pdf_author_entry.configure(foreground='#718096')
        
        def on_pdf_author_focus_in(event):
            if pdf_author_entry.get() == self.t("pdf_author_hint"):
                pdf_author_entry.delete(0, tk.END)
                pdf_author_entry.configure(foreground='#2d3748')
                self.pdf_author.set("")  # Clear the variable too
        
        def on_pdf_author_focus_out(event):
            if not pdf_author_entry.get():
                pdf_author_entry.insert(0, self.t("pdf_author_hint"))
                pdf_author_entry.configure(foreground='#718096')
                self.pdf_author.set("")  # Ensure variable is also empty
            else:
                # 保存实际输入的内容
                self.save_config()
        
        pdf_author_entry.bind('<FocusIn>', on_pdf_author_focus_in)
        pdf_author_entry.bind('<FocusOut>', on_pdf_author_focus_out)
        
        # Generate PDF button with modern spacing
        self.generate_pdf_btn = ttk.Button(inner_frame, text=self.t("generate_pdf"), 
                                          command=self.generate_pdf_from_folder, style='Secondary.TButton')
        self.generate_pdf_btn.grid(row=3, column=0, columnspan=2, pady=(15, 0))
        
    def create_progress_section(self, parent):
        """Create progress section"""
        # Progress frame with modern styling
        progress_frame = ttk.LabelFrame(parent, text=self.t("progress"), 
                                       padding="0", style='Section.TLabelframe')
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 添加内部间距和现代化布局
        inner_frame = ttk.Frame(progress_frame, padding="8")
        inner_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        inner_frame.columnconfigure(0, weight=1)
        
        # Progress bar with modern styling
        self.progress_var = tk.DoubleVar()
        try:
            self.progress_bar = ttk.Progressbar(inner_frame, variable=self.progress_var, 
                                               maximum=100, style='Progress.TProgressbar')
        except:
            # 如果自定义样式失败，使用默认样式
            self.progress_bar = ttk.Progressbar(inner_frame, variable=self.progress_var, 
                                               maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Status and statistics with modern layout
        status_frame = ttk.Frame(inner_frame)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status label with modern styling
        self.status_var = tk.StringVar(value=self.t("ready"))
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=('Segoe UI', 10, 'bold'))
        status_label.pack(side=tk.LEFT)
        
        # Statistics labels with modern styling
        self.success_count_var = tk.StringVar(value=self.t("success_count", 0))
        self.failed_count_var = tk.StringVar(value=self.t("failed_count", 0))
        self.total_count_var = tk.StringVar(value=self.t("total_count", 0))
        
        # 创建统计信息容器
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(side=tk.RIGHT)
        
        total_label = ttk.Label(stats_frame, textvariable=self.total_count_var, 
                               style='Info.TLabel', font=('Segoe UI', 9))
        total_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        failed_label = ttk.Label(stats_frame, textvariable=self.failed_count_var, 
                                style='Error.TLabel', font=('Segoe UI', 9))
        failed_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        success_label = ttk.Label(stats_frame, textvariable=self.success_count_var, 
                                 style='Success.TLabel', font=('Segoe UI', 9))
        success_label.pack(side=tk.RIGHT)
        
    def create_log_section(self, parent):
        """Create log section"""
        # Log frame with modern styling
        log_frame = ttk.LabelFrame(parent, text=self.t("log"), 
                                   padding="12", style='Section.TLabelframe')
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(4, weight=1)
        
        # 添加内部间距和现代化布局
        inner_frame = ttk.Frame(log_frame, padding="8")
        inner_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        inner_frame.columnconfigure(0, weight=1)
        inner_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs with modern styling
        notebook = ttk.Notebook(inner_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log tab
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text=self.t("log"))
        
        # Log text area with modern styling
        self.log_text = scrolledtext.ScrolledText(log_tab, height=10, width=90, 
                                                 font=('Consolas', 9), 
                                                 bg='#f8fafc', fg='#2d3748',
                                                 insertbackground='#667eea',
                                                 selectbackground='#667eea',
                                                 selectforeground='white',
                                                 relief='solid', borderwidth=1)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Failed URLs tab
        failed_tab = ttk.Frame(notebook)
        notebook.add(failed_tab, text=self.t("failed_urls"))
        
        # Failed URLs text area with modern styling
        self.failed_urls_text = scrolledtext.ScrolledText(failed_tab, height=10, width=90, 
                                                         font=('Consolas', 9), 
                                                         bg='#fff5f5', fg='#c53030',
                                                         insertbackground='#f56565',
                                                         selectbackground='#f56565',
                                                         selectforeground='white',
                                                         relief='solid', borderwidth=1)
        self.failed_urls_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Button frame with modern spacing
        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=1, column=0, pady=(8, 0))
        
        # Clear log button
        clear_btn = ttk.Button(button_frame, text=self.t("clear_log"), 
                              command=self.clear_log, style='Small.TButton')
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Retry all button
        retry_all_btn = ttk.Button(button_frame, text=self.t("retry_all"), 
                                  command=self.retry_failed_downloads, style='Warning.TButton')
        retry_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Copy URLs button
        copy_urls_btn = ttk.Button(button_frame, text=self.t("copy_urls"), 
                                  command=self.copy_failed_urls, style='Small.TButton')
        copy_urls_btn.pack(side=tk.LEFT)
        
    def change_language(self, language: str):
        """切换语言"""
        self.current_language = language
        self.update_ui_texts()
        # 保存语言设置
        self.save_config()
        
    def update_ui_texts(self):
        """更新UI文本"""
        # 更新窗口标题
        self.root.title(f"Manga Downloader - {self.t('title')}")
        
        # 更新各个部分的文本
        # 这里可以添加更多UI元素的文本更新
        self.status_var.set(self.t("ready"))
        
    def browse_save_path(self):
        """Browse for save path"""
        path = filedialog.askdirectory(title=self.t("select_save_dir"))
        if path:
            self.save_path.set(path)
            # 保存路径设置
            self.save_config()
            
    def browse_pdf_folder(self):
        """Browse for PDF folder"""
        path = filedialog.askdirectory(title=self.t("select_image_folder"))
        if path:
            self.pdf_folder_var.set(path)
            # 保存PDF文件夹路径
            self.save_config()
            
    def log_message(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear log text"""
        self.log_text.delete(1.0, tk.END)
        
    def update_failed_urls_display(self):
        """Update failed URLs display"""
        self.failed_urls_text.delete(1.0, tk.END)
        for url in self.failed_urls:
            self.failed_urls_text.insert(tk.END, f"{url}\n")
            
    def copy_failed_urls(self):
        """Copy failed URLs to clipboard"""
        if self.failed_urls:
            urls_text = "\n".join(self.failed_urls)
            self.root.clipboard_clear()
            self.root.clipboard_append(urls_text)
            self.log_message("Failed URLs copied to clipboard")
        else:
            self.log_message("No failed URLs to copy")
            
    def retry_failed_downloads(self):
        """Retry failed downloads"""
        if not self.failed_urls:
            messagebox.showinfo("Info", self.t("no_failed_urls"))
            return
            
        if self.is_downloading:
            messagebox.showwarning("Warning", self.t("download_in_progress"))
            return
            
        # Start retry in separate thread
        self.is_downloading = True
        self.retry_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._retry_thread)
        thread.daemon = True
        thread.start()
        
    def update_progress(self, value: float, status: str, success_count: int = None, 
                       failed_count: int = None, total_count: int = None):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_var.set(status)
        
        # Update statistics if provided
        if success_count is not None:
            self.success_count_var.set(self.t("success_count", success_count))
        if failed_count is not None:
            self.failed_count_var.set(self.t("failed_count", failed_count))
        if total_count is not None:
            self.total_count_var.set(self.t("total_count", total_count))
            
        self.root.update_idletasks()
        
    def start_download(self):
        """Start download process"""
        if self.is_downloading:
            messagebox.showwarning("Warning", self.t("download_in_progress"))
            return
            
        url = self.download_url.get().strip()
        if not url:
            messagebox.showerror("Error", self.t("please_enter_url"))
            return
            
        # Start download in separate thread
        self.is_downloading = True
        self.download_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._download_thread)
        thread.daemon = True
        thread.start()
        
    def _download_thread(self):
        """Download thread"""
        try:
            url = self.download_url.get().strip()
            save_path = self.save_path.get().strip()
            folder_name = self.folder_name.get().strip()
            proxy_host = self.proxy_host.get().strip()
            proxy_port = self.proxy_port.get().strip()
            
            # Update downloader with new proxy settings
            self.downloader.proxies = {
                'http': f'{proxy_host}:{proxy_port}',
                'https': f'{proxy_host}:{proxy_port}'
            }
            
            # Set save path
            if save_path:
                os.chdir(save_path)
                
            self.log_message(f"Starting download from: {url}")
            self.log_message(f"Using proxy: {proxy_host}:{proxy_port}")
            self.update_progress(0, self.t("starting_download"))
            
            # Reset statistics
            self.failed_urls = []
            self.update_failed_urls_display()
            
            # Start download with progress callback
            success = self.downloader.download_manga_from_url(
                url, 
                custom_folder_name=folder_name if folder_name else None,
                progress_callback=self._progress_callback
            )
            
            if success:
                self.update_progress(100, self.t("download_completed"))
                self.log_message(self.t("download_completed"))
                
                if self.generate_pdf.get():
                    self.log_message(self.t("generating_pdf"))
                    # Generate PDF after download using pdf_generator for better handling
                    if folder_name:
                        # Get author info for PDF generation
                        pdf_author = self.pdf_author.get().strip()
                        if pdf_author == self.t("pdf_author_hint"):
                            pdf_author = ""
                        
                        # Use pdf_generator instead of downloader.generate_pdf for better duplicate handling
                        pdf_success = self.pdf_generator.generate_pdf_from_folder(
                            folder_name, 
                            file_extensions=["jpg", "jpeg", "png", "webp"],
                            author=pdf_author if pdf_author else None
                        )
                    else:
                        # Try to find the actual folder name from the download
                        # This is a simplified approach - in practice you might want to return the folder name
                        pdf_success = False
                    
                    if pdf_success:
                        self.log_message(self.t("pdf_generated"))
                    else:
                        self.log_message(self.t("pdf_failed"))
                    
            else:
                self.update_progress(0, self.t("download_failed"))
                self.log_message(self.t("download_failed"))
                
        except Exception as e:
            self.log_message(self.t("error_during_download", str(e)))
            self.update_progress(0, self.t("error_occurred"))
            
        finally:
            self.is_downloading = False
            self.download_btn.config(state="normal")
            self.retry_btn.config(state="normal")
            
    def _retry_thread(self):
        """Retry failed downloads thread"""
        try:
            if not self.failed_urls:
                self.log_message(self.t("no_failed_urls"))
                return
                
            self.log_message(f"Retrying {len(self.failed_urls)} failed URLs...")
            self.update_progress(0, "Retrying failed downloads...")
            
            # Create a new downloader for retry
            retry_downloader = MangaDownloader(
                proxy_host=self.proxy_host.get().strip(),
                proxy_port=int(self.proxy_port.get().strip())
            )
            
            retry_success_count = 0
            retry_failed_count = 0
            
            for i, url in enumerate(self.failed_urls):
                try:
                    self.update_progress((i / len(self.failed_urls)) * 100, f"Retrying {i+1}/{len(self.failed_urls)}")
                    
                    # Extract folder name from URL or use default
                    folder_name = self.folder_name.get().strip()
                    
                    success = retry_downloader.download_manga_from_url(
                        url,
                        custom_folder_name=folder_name if folder_name else None,
                        single_page_only=True
                    )
                    
                    if success:
                        retry_success_count += 1
                        self.failed_urls.remove(url)
                    else:
                        retry_failed_count += 1
                        
                except Exception as e:
                    retry_failed_count += 1
                    self.log_message(f"Retry failed for {url}: {e}")
                    
            # Update display
            self.update_failed_urls_display()
            self.update_progress(100, self.t("retry_completed"), 
                               retry_success_count, retry_failed_count, len(self.failed_urls))
            self.log_message(f"Retry completed: {retry_success_count} successful, {retry_failed_count} failed")
            
        except Exception as e:
            self.log_message(f"Error during retry: {e}")
            self.update_progress(0, self.t("error_occurred"))
            
        finally:
            self.is_downloading = False
            self.retry_btn.config(state="normal")
            
    def _progress_callback(self, progress: float, status: str, success_count: int = None, 
                          failed_count: int = None, total_count: int = None):
        """Progress callback with statistics"""
        self.update_progress(progress, status, success_count, failed_count, total_count)
        
        # Update failed URLs if provided
        if hasattr(self.downloader, 'failed_urls'):
            self.failed_urls = self.downloader.failed_urls
            self.update_failed_urls_display()
            
    def generate_pdf_from_folder(self):
        """Generate PDF from selected folder"""
        folder_path = self.pdf_folder_var.get().strip()
        if not folder_path:
            messagebox.showerror("Error", self.t("please_select_folder"))
            return
            
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", self.t("folder_not_exist"))
            return
            
        # Use fixed file extensions
        extensions = ["jpg", "jpg", "webp"]
            
        # Start PDF generation in separate thread
        thread = threading.Thread(target=self._generate_pdf_thread, 
                                args=(folder_path, extensions))
        thread.daemon = True
        thread.start()
        
    def _generate_pdf_thread(self, folder_path: str, extensions: list):
        """PDF generation thread"""
        try:
            folder_name = os.path.basename(folder_path)
            pdf_name = self.pdf_name.get().strip()
            pdf_author = self.pdf_author.get().strip()
            
            # Check if pdf_name is the hint text and treat it as empty
            if pdf_name == self.t("pdf_name_hint"):
                pdf_name = ""
            
            # Check if pdf_author is the hint text and treat it as empty
            if pdf_author == self.t("pdf_author_hint"):
                pdf_author = ""
            
            self.log_message(self.t("generating_pdf_for", folder_name))
            self.update_progress(0, self.t("generating_pdf"))
            
            # Get folder info first
            info = self.pdf_generator.get_image_info(folder_path, extensions)
            if "error" in info:
                self.log_message(f"❌ Error: {info['error']}")
                self.update_progress(0, self.t("error_occurred"))
                return
            
            self.log_message(f"📁 Found {info['total_images']} images ({info['total_size_mb']} MB)")
            
            # Set output path with custom name if provided
            output_path = None
            if pdf_name:
                output_path = os.path.join(folder_path, f"{pdf_name}.pdf")
                self.log_message(f"📄 Will save as: {pdf_name}.pdf")
            else:
                self.log_message(f"📄 Will save as: {folder_name}.pdf")
            
            # Log author info if provided
            if pdf_author:
                self.log_message(f"👤 Author: {pdf_author}")
            
            # Update progress
            self.update_progress(25, "Processing images...")
            
            # Generate PDF
            success = self.pdf_generator.generate_pdf_from_folder(
                folder_path, 
                output_path=output_path,
                file_extensions=extensions,
                progress_callback=self.update_progress,
                author=pdf_author if pdf_author else None
            )
            
            if success:
                self.update_progress(100, self.t("pdf_generated"))
                final_name = pdf_name if pdf_name else folder_name
                self.log_message(f"✅ {self.t('pdf_generated_success', final_name)}")
            else:
                self.update_progress(0, self.t("pdf_failed"))
                self.log_message(f"❌ {self.t('pdf_failed')}")
                
        except Exception as e:
            self.log_message(f"❌ {self.t('error_during_pdf', str(e))}")
            self.update_progress(0, self.t("error_occurred"))
            
    def run(self):
        """Run the UI"""
        self.root.mainloop()


def main():
    """Main function"""
    app = MangaDownloaderUI()
    app.run()


if __name__ == "__main__":
    main()
