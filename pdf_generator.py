#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Generator - Standalone module for generating PDFs from image folders
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
from loguru import logger
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class PDFGenerator:
    """Standalone PDF generator for image folders"""
    
    def __init__(self):
        """Initialize PDF generator"""
        pass
    
    def generate_pdf_from_folder(self, folder_path: str, output_path: str = None, 
                                file_extensions: List[str] = None, 
                                sort_by_name: bool = True, progress_callback=None) -> bool:
        """
        Generate PDF from images in a folder
        
        Args:
            folder_path: Path to folder containing images
            output_path: Output PDF path (optional, defaults to folder_name.pdf)
            file_extensions: List of file extensions to include
            sort_by_name: Whether to sort files by name
            
        Returns:
            True if successful, False otherwise
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"Folder {folder_path} does not exist")
            return False
        
        # Get all image files
        image_files = []
        for ext in file_extensions:
            # Get both lowercase and uppercase extensions
            image_files.extend(folder.glob(f"*.{ext}"))
            image_files.extend(folder.glob(f"*.{ext.upper()}"))
        
        # Remove duplicates (same file with different case extensions)
        unique_files = []
        seen_names = set()
        for file_path in image_files:
            if file_path.name not in seen_names:
                unique_files.append(file_path)
                seen_names.add(file_path.name)
        
        image_files = unique_files
        
        if not image_files:
            logger.error(f"No image files found in {folder_path}")
            return False
        
        # Sort files
        if sort_by_name:
            image_files.sort(key=lambda x: self._natural_sort_key(x.name))
        else:
            image_files.sort()
        
        # Set output path
        if output_path is None:
            output_path = folder / f"{folder.name}.pdf"
        else:
            # Ensure output_path is a Path object
            output_path = Path(output_path)
        
        logger.info(f"Generating PDF from {len(image_files)} images")
        logger.info(f"Output: {output_path}")
        
        if progress_callback:
            progress_callback(50, f"Processing {len(image_files)} images...")
        
        try:
            success = self._create_pdf_with_pillow(image_files, output_path, progress_callback)
            if success:
                logger.info(f"✅ PDF generated successfully: {output_path}")
                if progress_callback:
                    progress_callback(100, "PDF generation completed!")
            else:
                logger.error(f"❌ Failed to generate PDF: {output_path}")
                if progress_callback:
                    progress_callback(0, "PDF generation failed!")
            return success
        except Exception as e:
            logger.error(f"❌ Failed to generate PDF: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False
    
    def generate_pdf_with_reportlab(self, folder_path: str, output_path: str = None,
                                   file_extensions: List[str] = None,
                                   page_size: str = "A4",
                                   max_width: int = 500,
                                   max_height: int = 700) -> bool:
        """
        Generate PDF using reportlab with more control over layout
        
        Args:
            folder_path: Path to folder containing images
            output_path: Output PDF path
            file_extensions: List of file extensions to include
            page_size: Page size ("A4", "letter", etc.)
            max_width: Maximum image width
            max_height: Maximum image height
            
        Returns:
            True if successful, False otherwise
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"Folder {folder_path} does not exist")
            return False
        
        # Get all image files
        image_files = []
        for ext in file_extensions:
            # Get both lowercase and uppercase extensions
            image_files.extend(folder.glob(f"*.{ext}"))
            image_files.extend(folder.glob(f"*.{ext.upper()}"))
        
        # Remove duplicates (same file with different case extensions)
        unique_files = []
        seen_names = set()
        for file_path in image_files:
            if file_path.name not in seen_names:
                unique_files.append(file_path)
                seen_names.add(file_path.name)
        
        image_files = unique_files
        
        if not image_files:
            logger.error(f"No image files found in {folder_path}")
            return False
        
        # Sort files by name
        image_files.sort(key=lambda x: self._natural_sort_key(x.name))
        
        # Set output path
        if output_path is None:
            output_path = folder / f"{folder.name}_reportlab.pdf"
        
        # Set page size
        if page_size.upper() == "A4":
            pagesize = A4
        else:
            pagesize = letter
        
        logger.info(f"Generating PDF with reportlab from {len(image_files)} images")
        logger.info(f"Output: {output_path}")
        
        try:
            # Check if output file exists and remove it to ensure clean generation
            if output_path.exists():
                logger.info(f"Removing existing PDF file: {output_path}")
                output_path.unlink()
            
            c = canvas.Canvas(str(output_path), pagesize=pagesize)
            
            for i, image_path in enumerate(image_files):
                logger.debug(f"Processing image {i+1}/{len(image_files)}: {image_path.name}")
                
                img = Image.open(image_path)
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                
                # Calculate image size to fit on page
                if img_width > max_width or img_height > max_height:
                    if aspect_ratio > 1:
                        display_width = max_width
                        display_height = max_width / aspect_ratio
                    else:
                        display_height = max_height
                        display_width = max_height * aspect_ratio
                else:
                    display_width = img_width
                    display_height = img_height
                
                # Center image on page
                page_width, page_height = pagesize
                x = (page_width - display_width) / 2
                y = (page_height - display_height) / 2
                
                c.drawImage(str(image_path), x, y, width=display_width, height=display_height)
                c.showPage()
            
            c.save()
            logger.info(f"✅ PDF generated successfully with reportlab: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate PDF with reportlab: {e}")
            return False
    
    def _create_pdf_with_pillow(self, image_files: List[Path], output_path: Path, progress_callback=None) -> bool:
        """Create PDF using Pillow"""
        try:
            # Check if output file exists and remove it to avoid appending
            if output_path.exists():
                logger.info(f"Removing existing PDF file: {output_path}")
                output_path.unlink()
            
            # Open first image
            output_image = Image.open(image_files[0])
            sources = []
            
            # Process remaining images
            for i, image_file in enumerate(image_files[1:], 1):
                if progress_callback:
                    progress = 50 + (i / len(image_files)) * 50  # 50-100%
                    progress_callback(progress, f"Processing image {i}/{len(image_files)}...")
                
                img = Image.open(image_file)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                sources.append(img)
            
            # Save PDF
            if progress_callback:
                progress_callback(90, "Saving PDF...")
            
            output_image.save(str(output_path), "PDF", save_all=True, append_images=sources)
            logger.info(f"✅ PDF generated successfully with Pillow: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create PDF with Pillow: {e}")
            return False
    
    def _natural_sort_key(self, text: str) -> List[Tuple[int, str]]:
        """Natural sort key for file names"""
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return alphanum_key(text)
    
    def get_image_info(self, folder_path: str, file_extensions: List[str] = None) -> dict:
        """
        Get information about images in a folder
        
        Args:
            folder_path: Path to folder
            file_extensions: List of file extensions to check
            
        Returns:
            Dictionary with image information
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": "Folder does not exist"}
        
        image_files = []
        total_size = 0
        
        for ext in file_extensions:
            for file_path in folder.glob(f"*.{ext}"):
                image_files.append(file_path)
                total_size += file_path.stat().st_size
            for file_path in folder.glob(f"*.{ext.upper()}"):
                image_files.append(file_path)
                total_size += file_path.stat().st_size
        
        # Remove duplicates
        image_files = list(set(image_files))
        image_files.sort(key=lambda x: self._natural_sort_key(x.name))
        
        return {
            "folder_path": str(folder),
            "total_images": len(image_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_extensions": list(set([f.suffix.lower() for f in image_files])),
            "image_files": [f.name for f in image_files]
        }
    
    def batch_generate_pdfs(self, directory: str, file_extensions: List[str] = None,
                           output_suffix: str = "_pdf") -> List[str]:
        """
        Generate PDFs for all folders in a directory
        
        Args:
            directory: Directory to scan
            file_extensions: List of file extensions to include
            output_suffix: Suffix to add to output PDF names
            
        Returns:
            List of generated PDF paths
        """
        if file_extensions is None:
            file_extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        directory_path = Path(directory)
        generated_pdfs = []
        
        for item in directory_path.iterdir():
            if item.is_dir():
                # Check if folder contains images
                info = self.get_image_info(str(item), file_extensions)
                if "error" not in info and info["total_images"] > 0:
                    logger.info(f"Generating PDF for {item.name}")
                    output_path = item / f"{item.name}{output_suffix}.pdf"
                    
                    if self.generate_pdf_from_folder(str(item), str(output_path), file_extensions):
                        generated_pdfs.append(str(output_path))
                    else:
                        logger.error(f"Failed to generate PDF for {item.name}")
        
        return generated_pdfs


def main():
    """Main function for testing"""
    generator = PDFGenerator()
    
    # Example usage
    # generator.generate_pdf_from_folder("数物作业")
    # generator.generate_pdf_with_reportlab("数物作业")
    
    # Get folder info
    info = generator.get_image_info("数物作业")
    print(f"Folder info: {info}")
    
    # Test duplicate removal
    print("\nTesting duplicate removal...")
    test_extensions = ['jpg', 'JPG', 'png', 'PNG']
    print(f"Extensions to test: {test_extensions}")
    
    # This would be tested with actual folder
    # generator.generate_pdf_from_folder("test_folder", file_extensions=test_extensions)


if __name__ == "__main__":
    main() 