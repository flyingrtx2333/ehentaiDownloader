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
                               progress_callback=None, single_page_only: bool = False, 
                               auto_retry: bool = False) -> bool:
        """
        Download manga starting from a specific URL
        
        Args:
            first_url: The first page URL to start downloading from
            custom_folder_name: Custom folder name to use instead of manga title
            progress_callback: Callback function for progress updates (progress, status, success_count, failed_count, total_count)
            single_page_only: If True, only download the single page specified by first_url
            auto_retry: If True, automatically retry failed downloads
            
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
            # Get total pages from first URL response
            if progress_callback:
                progress_callback(0, "Getting total page count...")
            
            try:
                first_url = f"https://e-hentai.org/s/{current_id}/{book_id}-{current_page}"
                response = self.session.get(
                    url=first_url,
                    proxies=self.proxies,
                    headers=self._get_headers(),
                    timeout=8
                )
                
                if "Your IP address has been temporarily banned" in response.text:
                    logger.warning("IP has been temporarily banned, need to change proxy")
                    return False
                
                total_pages = self._extract_total_pages(response.text)
                if total_pages == 0:
                    logger.warning("Could not extract total pages, will count during download")
                    total_pages = 1  # Will be updated during download
                else:
                    logger.info(f"Total pages detected: {total_pages}")
                    
            except Exception as e:
                logger.error(f"Failed to get total pages from first URL: {e}")
                total_pages = 1  # Will be updated during download
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
                
                # If we couldn't get total pages initially, try to extract it now
                if total_pages == 1 and current_page == current_page_num:
                    extracted_total = self._extract_total_pages(response.text)
                    if extracted_total > 0:
                        total_pages = extracted_total
                        logger.info(f"Updated total pages to: {total_pages}")
                
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
                if self.failed_urls:
                    logger.warning("Failed URLs:")
                    for failed_url in self.failed_urls:
                        logger.warning(failed_url)
                    
                    # Auto retry logic
                    if auto_retry and self.failed_urls:
                        logger.info(f"Auto retry enabled, retrying {len(self.failed_urls)} failed URLs...")
                        # Clear failed URLs for the retry attempt
                        retry_failed_urls = self.failed_urls.copy()
                        self.failed_urls = []
                        
                        # Retry each failed URL
                        for failed_url in retry_failed_urls:
                            try:
                                logger.info(f"Retrying: {failed_url}")
                                # Extract page info from failed URL
                                book_id, page_num, current_id = self.parse_url_info(failed_url)
                                
                                # Download single page
                                single_page_success = self.download_manga_from_url(
                                    failed_url,
                                    custom_folder_name=custom_folder_name,
                                    progress_callback=progress_callback,
                                    single_page_only=True,
                                    auto_retry=False  # Don't retry again to avoid infinite loop
                                )
                                
                                if not single_page_success:
                                    self.failed_urls.append(failed_url)
                                    
                            except Exception as e:
                                logger.error(f"Retry failed for {failed_url}: {e}")
                                self.failed_urls.append(failed_url)
                        
                        # Log final results
                        if self.failed_urls:
                            logger.warning(f"After auto retry, {len(self.failed_urls)} URLs still failed")
                        else:
                            logger.info("Auto retry successful - all URLs downloaded")
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
    
    def _extract_total_pages(self, html_content: str) -> int:
        """Extract total page count from HTML content"""
        try:
            # Look for pattern like: <span>1</span> / <span>207</span>
            pattern = r'<span>\d+</span>\s*/\s*<span>(\d+)</span>'
            matches = re.findall(pattern, html_content)
            if matches:
                logger.debug(f"Found total pages using pattern1: {matches[0]}")
                return int(matches[0])
            
            # Alternative pattern: look for " / 207" in the page indicator
            pattern2 = r'/\s*(\d+)'
            matches2 = re.findall(pattern2, html_content)
            if matches2:
                # Find the largest number which is likely the total page count
                numbers = [int(match) for match in matches2 if match.isdigit()]
                if numbers:
                    max_num = max(numbers)
                    logger.debug(f"Found total pages using pattern2: {max_num}")
                    return max_num
            
            # More specific pattern for the page indicator div
            pattern3 = r'<div><span>\d+</span>\s*/\s*<span>(\d+)</span></div>'
            matches3 = re.findall(pattern3, html_content)
            if matches3:
                logger.debug(f"Found total pages using pattern3: {matches3[0]}")
                return int(matches3[0])
            
            logger.debug("No total pages pattern found in HTML")
            return 0
        except Exception as e:
            logger.error(f"Failed to extract total pages: {e}")
            return 0
    
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
    
    def _natural_sort_key(self, text: str) -> List[Tuple[int, str]]:
        """Natural sort key for file names"""
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return alphanum_key(text)