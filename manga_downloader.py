#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manga Downloader - A tool for downloading manga images and converting them to PDF
Author: Your Name
Version: 1.0.0
"""

import os
import re
import traceback
from typing import List, Optional, Dict, Tuple
from pathlib import Path

from PIL import Image
import requests
from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class MangaDownloader:
    """Main class for downloading manga images and converting to PDF"""
    
    def __init__(self, proxy_host: str = "127.0.0.1", proxy_port: int = 7890):
        """
        Initialize the manga downloader
        
        Args:
            proxy_host: Proxy host address
            proxy_port: Proxy port number
        """
        self.proxies = {
            'http': f'{proxy_host}:{proxy_port}',
            'https': f'{proxy_host}:{proxy_port}'
        }
        self.session = requests.Session()
        self.error_image_data = self._load_error_image()
        self.title_replace_map = self._get_title_replace_map()
        
        # Configure logger
        logger.add("manga_downloader.log", rotation="10 MB", level="INFO")
        
    def _load_error_image(self) -> bytes:
        """Load error image data for comparison"""
        try:
            with open('error.jpg', 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("error.jpg not found, using empty bytes")
            return b''
    
    def _get_title_replace_map(self) -> Dict[str, str]:
        """Get title replacement mapping"""
        return {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
    
    def parse_url_info(self, url: str) -> Tuple[str, int, str]:
        """
        Parse URL to extract book information
        
        Args:
            url: The manga page URL
            
        Returns:
            Tuple of (book_id, current_page, current_id)
        """
        parts = url.split('/')
        book_id = parts[-1].split('-')[0]
        current_page = int(parts[-1].split('-')[1])
        current_id = parts[-2]
        return book_id, current_page, current_id
    
    def download_manga_from_url(self, first_url: str, custom_folder_name: str = None, 
                               progress_callback=None, single_page_only: bool = False) -> bool:
        """
        Download manga starting from a specific URL
        
        Args:
            first_url: The first page URL to start downloading from
            custom_folder_name: Custom folder name to use instead of manga title
            progress_callback: Callback function for progress updates (progress, status, success_count, failed_count, total_count)
            single_page_only: If True, only download the single page specified by first_url
            
        Returns:
            True if successful, False otherwise
        """
        book_id, current_page, current_id = self.parse_url_info(first_url)
        self.failed_urls = []  # Store failed URLs for retry
        success_count = 0
        failed_count = 0
        total_pages = 0
        current_page_num = current_page
        
        logger.info(f"Starting download for book {book_id} from page {current_page}")
        
        # If single page only, skip counting total pages
        if not single_page_only:
            # First pass to count total pages
            if progress_callback:
                progress_callback(0, "Counting total pages...")
            
            temp_current_id = current_id
            temp_current_page = current_page
            while True:
                url = f"https://e-hentai.org/s/{temp_current_id}/{book_id}-{temp_current_page}"
                try:
                    response = self.session.get(
                        url=url,
                        proxies=self.proxies,
                        headers=self._get_headers(),
                        timeout=8
                    )
                    total_pages += 1
                    next_page_id = self._find_next_page_id(response.text, temp_current_page + 1)
                    if next_page_id:
                        temp_current_id = next_page_id
                        temp_current_page += 1
                    else:
                        break
                except:
                    break
        else:
            # For single page download, set total_pages to 1
            total_pages = 1
        
        # Reset for actual download
        current_id = self.parse_url_info(first_url)[2]
        current_page = self.parse_url_info(first_url)[1]
        
        while True:
            url = f"https://e-hentai.org/s/{current_id}/{book_id}-{current_page}"
            logger.info(f"Downloading page {current_page} from {url}")
            
            if progress_callback:
                progress = ((current_page - current_page_num) / total_pages) * 100
                progress_callback(progress, f"Downloading page {current_page}...", 
                               success_count, failed_count, total_pages)
            
            try:
                response = self.session.get(
                    url=url,
                    proxies=self.proxies,
                    headers=self._get_headers(),
                    timeout=8
                )
                
                if "Your IP address has been temporarily banned" in response.text:
                    logger.warning("IP has been temporarily banned, need to change proxy")
                    return False
                
                title = self._extract_title(response.text)
                if title in self.title_replace_map:
                    title = self.title_replace_map[title]
                
                # Use custom folder name if provided
                if custom_folder_name:
                    title = custom_folder_name
                    
            except requests.exceptions.ReadTimeout:
                logger.warning(f"Timeout for page {current_page}, retrying...")
                continue
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for page {current_page}, retrying...")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for page {current_page}: {e}")
                self.failed_urls.append(url)
                failed_count += 1
                continue
            
            try:
                self._download_and_save_image(response.text, title, current_page)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to save image for page {current_page}: {e}")
                self.failed_urls.append(url)
                failed_count += 1
            
            # Find next page
            next_page_id = self._find_next_page_id(response.text, current_page + 1)
            if next_page_id:
                current_id = next_page_id
                current_page += 1
            else:
                logger.info("Reached end of manga, generating PDF...")
                if progress_callback:
                    progress_callback(100, "Download completed, generating PDF...", 
                                   success_count, failed_count, total_pages)
                self.generate_pdf(title)
                if self.failed_urls:
                    logger.warning("Failed URLs:")
                    for failed_url in self.failed_urls:
                        logger.warning(failed_url)
                break
        
        return True
    
    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content"""
        try:
            title = html_content.split('<title>')[1].split('</title>')[0]
            return title
        except IndexError:
            logger.error("Could not extract title from HTML")
            return "Unknown_Title"
    
    def _find_next_page_id(self, html_content: str, next_page_num: int) -> Optional[str]:
        """Find the next page ID from HTML content"""
        pattern = f"load_image\\({next_page_num}, '(.*?)'\\)"
        matches = re.findall(pattern, html_content)
        return matches[0] if matches else None
    
    def _download_and_save_image(self, html_content: str, dir_name: str, page_num: int) -> bool:
        """
        Download and save image from HTML content
        
        Args:
            html_content: HTML content containing image URL
            dir_name: Directory name to save image
            page_num: Page number
            
        Returns:
            True if successful, False otherwise
        """
        image_path = Path(dir_name) / f"{page_num}.jpg"
        
        if image_path.exists():
            logger.info(f"Image {page_num} already exists, skipping")
            return True
        
        image_url = self._extract_image_url(html_content)
        if not image_url:
            raise Exception("Could not find image URL")
        
        try:
            response = requests.get(
                url=image_url,
                proxies=self.proxies,
                headers={
                    'Referer': 'https://e-hentai.org',
                    **self._get_headers()
                },
                timeout=18
            )
            
            image_data = response.content
            if image_data == self.error_image_data:
                raise Exception("Downloaded image is error image, not saving")
            
            # Create directory if it doesn't exist
            Path(dir_name).mkdir(exist_ok=True)
            
            # Save image
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            logger.debug(f"Successfully saved {dir_name} page {page_num}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download image for page {page_num}: {e}")
            raise
    
    def _extract_image_url(self, html_content: str) -> Optional[str]:
        """Extract image URL from HTML content"""
        matches = re.findall('src="(.*?)"', html_content)
        for i, match in enumerate(matches):
            if match.endswith("jads.js") and i + 1 < len(matches):
                return matches[i + 1]
        return None
    
    def generate_pdf(self, book_name: str, file_extensions: List[str] = None) -> bool:
        """
        Generate PDF from images in a directory
        
        Args:
            book_name: Directory name containing images
            file_extensions: List of file extensions to include (default: ['jpg', 'webp'])
            
        Returns:
            True if successful, False otherwise
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'webp']
        
        logger.info(f"Starting PDF generation for {book_name}")
        
        book_path = Path(book_name)
        if not book_path.exists():
            logger.error(f"Directory {book_name} does not exist")
            return False
        
        # Get all image files
        image_files = []
        for ext in file_extensions:
            image_files.extend(book_path.glob(f"*.{ext}"))
            image_files.extend(book_path.glob(f"*.{ext.upper()}"))
        
        if not image_files:
            logger.error(f"No image files found in {book_name}")
            return False
        
        # Sort files by name
        image_files.sort(key=lambda x: x.name)
        
        try:
            # Open first image
            output_image = Image.open(image_files[0])
            sources = []
            
            # Process remaining images
            for image_file in image_files[1:]:
                img = Image.open(image_file)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                sources.append(img)
            
            # Save PDF
            pdf_path = book_path / f"{book_name}.pdf"
            output_image.save(str(pdf_path), "PDF", save_all=True, append_images=sources)
            
            logger.info(f"Successfully generated PDF: {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate PDF for {book_name}: {e}")
            return False
    
    def create_pdf_with_reportlab(self, image_paths: List[str], author: str, pdf_path: str) -> bool:
        """
        Create PDF using reportlab (alternative method)
        
        Args:
            image_paths: List of image file paths
            author: Author name for PDF metadata
            pdf_path: Output PDF path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setTitle(author)
            c.setAuthor(author)
            
            for image_path in image_paths:
                img = Image.open(image_path)
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                max_width = 500
                max_height = 700
                
                # Adjust image size based on aspect ratio
                if img_width > max_width or img_height > max_height:
                    if aspect_ratio > 1:
                        img_width = max_width
                        img_height = max_width / aspect_ratio
                    else:
                        img_height = max_height
                        img_width = max_height * aspect_ratio
                    
                    img.thumbnail((img_width, img_height), Image.LANCZOS)
                
                c.drawImage(image_path, 50, 50, width=img_width, height=img_height)
                c.showPage()
            
            c.save()
            logger.info(f"Successfully created PDF with reportlab: {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PDF with reportlab: {e}")
            return False
    
    def check_folder_for_pdf(self, folder_path: str) -> bool:
        """Check if folder contains PDF files"""
        folder = Path(folder_path)
        if not folder.exists():
            return False
        pdf_files = list(folder.glob("*.pdf"))
        return len(pdf_files) > 0
    
    def batch_generate_pdfs(self, directory: str = ".", file_extensions: List[str] = None) -> None:
        """
        Generate PDFs for all folders that don't have them
        
        Args:
            directory: Directory to scan
            file_extensions: List of file extensions to include
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'png', 'webp']
        
        directory_path = Path(directory)
        for item in directory_path.iterdir():
            if item.is_dir():
                if not self.check_folder_for_pdf(str(item)):
                    logger.info(f"Generating PDF for {item.name}")
                    try:
                        self.generate_pdf(item.name, file_extensions)
                    except Exception as e:
                        logger.error(f"Failed to generate PDF for {item.name}: {e}")
                        traceback.print_exc()


def main():
    """Main function"""
    downloader = MangaDownloader()
    
    # Example usage
    downloader.download_manga_from_url("https://e-hentai.org/s/f079533ce8/3210316-1")
    
    # Generate PDF for existing folder
    # downloader.generate_pdf("folder_name", ["jpg", "JPG"])
    
    # Batch generate PDFs
    # downloader.batch_generate_pdfs(".", ["jpg", "png"])


if __name__ == '__main__':
    main() 