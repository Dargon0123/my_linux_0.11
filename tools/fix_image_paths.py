#!/usr/bin/env python3
"""
图片路径自动修复工具
功能：
1. 检测Markdown文件中的本地图片路径
2. 将图片复制到assets/images/目录
3. 自动更新Markdown文件中的图片路径
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple


class ImagePathFixer:
    """图片路径修复器"""
    
    SUPPORTED_MARKDOWN_EXTENSIONS = {'.md', '.markdown', '.mkd'}
    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.assets_images_dir = self.project_root / 'assets' / 'images'
        self.stats = {'found': 0, 'copied': 0, 'updated': 0, 'skipped': 0}
    
    def find_markdown_files(self, exclude_dirs: List[str] = None) -> List[Path]:
        """查找项目中的所有Markdown文件"""
        if exclude_dirs is None:
            exclude_dirs = ['.git', 'node_modules', '__pycache__', 'venv', '.venv']
        
        markdown_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if Path(file).suffix.lower() in self.SUPPORTED_MARKDOWN_EXTENSIONS:
                    markdown_files.append(Path(root) / file)
        return markdown_files
    
    def extract_image_paths(self, markdown_file: Path) -> List[Tuple[str, str]]:
        """从Markdown文件中提取所有图片路径"""
        content = markdown_file.read_text(encoding='utf-8')
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        return matches
    
    def is_local_path(self, path: str) -> bool:
        """判断是否为本地路径（不是URL）"""
        if path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
            return False
        if path.startswith('data:'):
            return False
        return True
    
    def is_image_file(self, filename: str) -> bool:
        """判断是否为图片文件"""
        return Path(filename).suffix.lower() in self.SUPPORTED_IMAGE_EXTENSIONS
    
    def find_local_image(self, image_path: str, markdown_dir: Path) -> Path:
        """尝试在多个位置查找本地图片"""
        search_paths = [
            markdown_dir / image_path,
            self.project_root / image_path,
            Path(image_path),
        ]
        
        for search_path in search_paths:
            if search_path.exists() and search_path.is_file():
                return search_path
        
        return None
    
    def ensure_assets_directory(self):
        """确保assets/images目录存在"""
        self.assets_images_dir.mkdir(parents=True, exist_ok=True)
    
    def copy_image_to_assets(self, source_path: Path) -> Path:
        """将图片复制到assets/images目录"""
        filename = source_path.name
        dest_path = self.assets_images_dir / filename
        
        if dest_path.exists():
            print(f"  跳过: {filename} 已存在")
            self.stats['skipped'] += 1
            return dest_path
        
        shutil.copy2(source_path, dest_path)
        print(f"  复制: {source_path.name} -> assets/images/")
        self.stats['copied'] += 1
        return dest_path
    
    def update_markdown_file(self, markdown_file: Path, image_updates: List[Tuple[str, str, str]]):
        """更新Markdown文件中的图片路径"""
        content = markdown_file.read_text(encoding='utf-8')
        
        for alt_text, old_path, new_path in image_updates:
            old_pattern = f'![{alt_text}]({re.escape(old_path)})'
            new_replacement = f'![{alt_text}]({new_path})'
            content = content.replace(old_pattern, new_replacement)
        
        if content != markdown_file.read_text(encoding='utf-8'):
            markdown_file.write_text(content, encoding='utf-8')
            self.stats['updated'] += 1
            print(f"  更新: {markdown_file.name}")
    
    def process_markdown_file(self, markdown_file: Path) -> Tuple[int, int]:
        """处理单个Markdown文件的图片"""
        images = self.extract_image_paths(markdown_file)
        image_updates = []
        found_count = 0
        
        print(f"\n处理: {markdown_file.relative_to(self.project_root)}")
        
        for alt_text, image_path in images:
            if not self.is_local_path(image_path):
                continue
            
            found_count += 1
            
            if not self.is_image_file(image_path):
                print(f"  跳过: 非图片文件 ({image_path})")
                continue
            
            source_path = self.find_local_image(image_path, markdown_file.parent)
            
            if source_path:
                dest_path = self.copy_image_to_assets(source_path)
                relative_path = dest_path.relative_to(self.project_root)
                new_path = str(relative_path).replace('\\', '/')
                image_updates.append((alt_text, image_path, new_path))
            else:
                print(f"  警告: 未找到图片文件 ({image_path})")
        
        self.stats['found'] += found_count
        
        if image_updates:
            self.update_markdown_file(markdown_file, image_updates)
        
        return found_count, len(image_updates)
    
    def process_all(self, exclude_files: List[str] = None):
        """处理所有Markdown文件的图片"""
        if exclude_files is None:
            exclude_files = []
        
        print("=" * 60)
        print("图片路径自动修复工具")
        print("=" * 60)
        print(f"项目根目录: {self.project_root}")
        print(f"图片目标目录: {self.assets_images_dir}")
        print("=" * 60)
        
        self.ensure_assets_directory()
        
        markdown_files = self.find_markdown_files()
        
        for markdown_file in markdown_files:
            if markdown_file.name in exclude_files:
                continue
            
            self.process_markdown_file(markdown_file)
        
        print("\n" + "=" * 60)
        print("处理完成！统计信息：")
        print(f"  发现本地图片: {self.stats['found']} 个")
        print(f"  复制图片: {self.stats['copied']} 个")
        print(f"  跳过(已存在): {self.stats['skipped']} 个")
        print(f"  更新文件: {self.stats['updated']} 个Markdown文件")
        print("=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='图片路径自动修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    parser.add_argument('--file', type=str, help='指定处理的Markdown文件')
    
    args = parser.parse_args()
    
    project_root = os.getcwd()
    fixer = ImagePathFixer(project_root)
    
    if args.dry_run:
        print("预览模式：")
        markdown_files = fixer.find_markdown_files()
        for md_file in markdown_files:
            images = fixer.extract_image_paths(md_file)
            if images:
                print(f"\n{md_file.relative_to(project_root)}:")
                for alt_text, path in images:
                    if fixer.is_local_path(path):
                        print(f"  - {path}")
        return
    
    if args.file:
        md_file = Path(args.file)
        if not md_file.is_absolute():
            md_file = Path(project_root) / md_file
        
        if md_file.exists():
            fixer.process_markdown_file(md_file)
        else:
            print(f"错误: 文件不存在 - {md_file}")
        return
    
    fixer.process_all()


if __name__ == '__main__':
    main()
